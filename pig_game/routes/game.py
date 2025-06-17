# routes/game.py
from flask import Blueprint, render_template, request, jsonify, session, current_app, redirect, url_for
from models import db, User, GameSession, Bet
from models.game_session import GameState
from datetime import datetime, timedelta
from utils import timer
import json

game_bp = Blueprint('game', __name__)

def login_required(f):
    """로그인 검증 데코레이터"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.', 'redirect': '/login'})
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_current_user():
    """현재 로그인한 사용자 조회"""
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

def format_cards_for_display(cards):
    """카드 리스트를 화면 표시용으로 변환"""
    if not cards:
        return []
    
    result = []
    for card in cards:
        if isinstance(card, dict):
            result.append(card)
        else:
            # 카드 정보를 JSON에서 파싱
            try:
                card_data = json.loads(card) if isinstance(card, str) else card
                result.append(card_data)
            except:
                # 기본 카드 정보 생성
                result.append({
                    'name': str(card),
                    'image_url': 'https://deckofcardsapi.com/static/img/back.png'
                })
    
    return result

@game_bp.route('/')
@login_required
def index():
    """메인 게임 페이지"""
    try:
        current_user = get_current_user()
        if not current_user:
            return redirect(url_for('auth.login'))
        
        # 사용자를 게임 중 상태로 설정
        current_user.is_in_game = True
        db.session.commit()
        
        return render_template('index.html', user=current_user)
        
    except Exception as e:
        print(f"메인 페이지 오류: {e}")
        return f"오류 발생: {e}", 500

@game_bp.route('/api/game/state')
@login_required
def get_game_state():
    """게임 상태 조회 (게임 로직 업데이트 포함)"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': '사용자 정보를 찾을 수 없습니다.'})
        
        # 게임 매니저를 통한 상태 업데이트 (안전 모드)
        try:
            from core.game_manager import GameManager
            game_manager = GameManager()
            game_manager.set_app(current_app)
            
            # 현재 세션이 없으면 생성
            current_session = GameSession.query.filter_by(is_active=True).first()
            if not current_session:
                # 새 세션 생성
                round_number = 1
                last_session = GameSession.query.order_by(GameSession.round_number.desc()).first()
                if last_session:
                    round_number = last_session.round_number + 1
                
                current_session = GameSession(
                    round_number=round_number,
                    state=GameState.WAITING,
                    phase_start_time=datetime.utcnow(),
                    is_active=True
                )
                db.session.add(current_session)
                db.session.commit()
                print(f"🆕 새 게임 세션 생성: Round #{round_number}")
            
        except Exception as e:
            print(f"게임 매니저 업데이트 오류: {e}")
            # 게임 매니저가 실패해도 계속 진행
        
        # 현재 활성 세션 조회
        current_session = GameSession.query.filter_by(is_active=True).first()
        
        if not current_session:
            return jsonify({
                'success': False,
                'error': '활성 게임 세션이 없습니다.'
            })
        
        # 타이머 정보 계산
        timer_info = timer.calculate_remaining_time(
            current_session.phase_start_time,
            current_session.state
        )
        
        # 게임 상태 정보 구성
        game_state = {
            'session_id': current_session.id,
            'round_number': current_session.round_number,
            'state': current_session.state.value,
            'player_score': current_session.player_score,
            'banker_score': current_session.banker_score,
            'winner': current_session.winner,
            'player_cards_display': format_cards_for_display(current_session.player_cards or []),
            'banker_cards_display': format_cards_for_display(current_session.banker_cards or []),
            'total_bets': {
                'banker': current_session.total_banker_bets or 0,
                'player': current_session.total_player_bets or 0,
                'tie': current_session.total_tie_bets or 0,
                'banker_pair': current_session.total_banker_pair_bets or 0,
                'player_pair': current_session.total_player_pair_bets or 0
            }
        }
        
        # 활성 사용자 목록
        active_users_query = User.query.filter_by(is_in_game=True).limit(4).all()
        active_users = []
        
        for user in active_users_query:
            active_users.append({
                'username': user.username,
                'chips': user.chips,
                'is_current_user': user.id == session['user_id']
            })
        
        return jsonify({
            'success': True,
            'game_state': game_state,
            'timer_info': timer_info,
            'user_chips': current_user.chips,
            'active_users': active_users
        })
        
    except Exception as e:
        print(f"게임 상태 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': f'게임 상태 조회 실패: {str(e)}'
        })

@game_bp.route('/api/bet', methods=['POST'])
@login_required
def place_bet():
    """베팅 접수"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': '사용자 정보를 찾을 수 없습니다.'})
        
        data = request.json
        bet_target = data.get('bet_target')
        bet_amount = data.get('bet_amount')
        
        # 입력 검증
        if not bet_target or not bet_amount:
            return jsonify({'success': False, 'error': '베팅 정보가 올바르지 않습니다.'})
        
        bet_amount = int(bet_amount)
        
        # 베팅 금액 검증
        if bet_amount < 100:
            return jsonify({'success': False, 'error': '최소 베팅 금액은 100칩입니다.'})
        
        if bet_amount > 50000:
            return jsonify({'success': False, 'error': '최대 베팅 금액은 50,000칩입니다.'})
        
        if bet_amount > current_user.chips:
            return jsonify({'success': False, 'error': '보유 칩이 부족합니다.'})
        
        # 현재 게임 세션 확인
        current_session = GameSession.query.filter_by(is_active=True).first()
        if not current_session:
            return jsonify({'success': False, 'error': '진행 중인 게임이 없습니다.'})
        
        # 베팅 가능한 상태인지 확인
        if current_session.state != GameState.BETTING:
            return jsonify({'success': False, 'error': '현재 베팅할 수 없는 상태입니다.'})
        
        # 중복 베팅 확인
        existing_bet = Bet.query.filter_by(
            session_id=current_session.id,
            user_id=current_user.id,
            bet_target=bet_target
        ).first()
        
        if existing_bet:
            return jsonify({'success': False, 'error': '이미 해당 항목에 베팅하셨습니다.'})
        
        # 베팅 생성
        new_bet = Bet(
            session_id=current_session.id,
            user_id=current_user.id,
            bet_target=bet_target,
            bet_amount=bet_amount,
            created_at=datetime.utcnow()
        )
        
        # 사용자 칩 차감
        current_user.chips -= bet_amount
        
        # DB에 저장
        db.session.add(new_bet)
        db.session.commit()
        
        print(f"베팅 접수: {current_user.username} -> {bet_target}: {bet_amount}")
        
        return jsonify({
            'success': True,
            'message': '베팅이 접수되었습니다.',
            'remaining_chips': current_user.chips,
            'bet_info': {
                'target': bet_target,
                'amount': bet_amount
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"베팅 접수 오류: {e}")
        return jsonify({
            'success': False,
            'error': f'베팅 처리 중 오류가 발생했습니다: {str(e)}'
        })

@game_bp.route('/api/user/bets')
@login_required
def get_user_bets():
    """사용자의 현재 세션 베팅 조회"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': '사용자 정보를 찾을 수 없습니다.'})
        
        current_session = GameSession.query.filter_by(is_active=True).first()
        if not current_session:
            return jsonify({'success': True, 'bets': []})
        
        user_bets = Bet.query.filter_by(
            session_id=current_session.id,
            user_id=current_user.id
        ).all()
        
        bets_data = []
        total_amount = 0
        
        for bet in user_bets:
            bets_data.append({
                'target': bet.bet_target,
                'amount': bet.bet_amount,
                'created_at': bet.created_at.isoformat()
            })
            total_amount += bet.bet_amount
        
        return jsonify({
            'success': True,
            'bets': bets_data,
            'total_amount': total_amount
        })
        
    except Exception as e:
        print(f"사용자 베팅 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': f'베팅 조회 실패: {str(e)}'
        })