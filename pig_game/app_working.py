# app_working.py - 간단하고 확실히 작동하는 버전
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import random
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'baccarat-game-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baccarat_game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 간단한 모델들
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    chips = db.Column(db.Integer, default=10000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, default=1)
    state = db.Column(db.String(20), default='waiting')  # waiting, betting, dealing, result
    player_score = db.Column(db.Integer)
    banker_score = db.Column(db.Integer)
    winner = db.Column(db.String(20))  # player, banker, tie
    player_cards = db.Column(db.Text)  # JSON string
    banker_cards = db.Column(db.Text)  # JSON string
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    phase_start = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    bet_target = db.Column(db.String(20), nullable=False)  # banker, player, tie, banker_pair, player_pair
    bet_amount = db.Column(db.Integer, nullable=False)
    payout = db.Column(db.Integer, default=0)
    is_settled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 전역 게임 상태
class GameState:
    def __init__(self):
        self.current_session = None
        self.timer_thread = None
        self.running = False
    
    def start_game_loop(self):
        if not self.running:
            self.running = True
            self.timer_thread = threading.Thread(target=self._game_loop, daemon=True)
            self.timer_thread.start()
            print("🎮 게임 루프 시작")
    
    def _game_loop(self):
        while self.running:
            try:
                with app.app_context():
                    self._update_game()
                time.sleep(2)
            except Exception as e:
                print(f"게임 루프 오류: {e}")
                time.sleep(5)
    
    def _update_game(self):
        # 현재 세션 확인
        if not self.current_session or not self.current_session.is_active:
            self._create_new_session()
            return
        
        # DB에서 새로고침
        db.session.refresh(self.current_session)
        
        # 상태별 처리
        now = datetime.utcnow()
        elapsed = (now - self.current_session.phase_start).total_seconds()
        
        if self.current_session.state == 'waiting' and elapsed > 5:
            self._start_betting()
        elif self.current_session.state == 'betting' and elapsed > 15:
            self._deal_cards()
        elif self.current_session.state == 'dealing' and elapsed > 5:
            self._show_result()
        elif self.current_session.state == 'result' and elapsed > 8:
            self._finish_round()
    
    def _create_new_session(self):
        # 기존 세션 비활성화
        GameSession.query.filter_by(is_active=True).update({'is_active': False})
        
        # 새 세션 생성
        last = GameSession.query.order_by(GameSession.round_number.desc()).first()
        round_num = (last.round_number + 1) if last else 1
        
        self.current_session = GameSession(
            round_number=round_num,
            state='waiting',
            phase_start=datetime.utcnow()
        )
        db.session.add(self.current_session)
        db.session.commit()
        print(f"🆕 새 라운드 #{round_num} 시작")
    
    def _start_betting(self):
        self.current_session.state = 'betting'
        self.current_session.phase_start = datetime.utcnow()
        db.session.commit()
        print(f"💰 라운드 #{self.current_session.round_number} 베팅 시작")
    
    def _deal_cards(self):
        # 카드 생성 (간단 버전)
        def random_card():
            suits = ['S', 'H', 'D', 'C']
            values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'J', 'Q', 'K']
            suit = random.choice(suits)
            value = random.choice(values)
            return {
                'code': value + suit,
                'value': value,
                'suit': suit,
                'image': f'https://deckofcardsapi.com/static/img/{value}{suit}.png'
            }
        
        player_cards = [random_card(), random_card()]
        banker_cards = [random_card(), random_card()]
        
        # 점수 계산
        def calc_score(cards):
            total = 0
            for card in cards:
                val = card['value']
                if val in ['J', 'Q', 'K', '0']:
                    total += 0
                elif val == 'A':
                    total += 1
                else:
                    total += int(val)
            return total % 10
        
        player_score = calc_score(player_cards)
        banker_score = calc_score(banker_cards)
        
        # 승자 결정
        if player_score > banker_score:
            winner = 'player'
        elif banker_score > player_score:
            winner = 'banker'
        else:
            winner = 'tie'
        
        # DB 저장
        self.current_session.player_cards = json.dumps(player_cards)
        self.current_session.banker_cards = json.dumps(banker_cards)
        self.current_session.player_score = player_score
        self.current_session.banker_score = banker_score
        self.current_session.winner = winner
        self.current_session.state = 'dealing'
        self.current_session.phase_start = datetime.utcnow()
        db.session.commit()
        
        print(f"🃏 카드 분배: Player {player_score} vs Banker {banker_score} → {winner}")
    
    def _show_result(self):
        self.current_session.state = 'result'
        self.current_session.phase_start = datetime.utcnow()
        db.session.commit()
        
        # 베팅 정산
        self._settle_bets()
        print(f"🎯 라운드 #{self.current_session.round_number} 결과 발표: {self.current_session.winner}")
    
    def _settle_bets(self):
        bets = Bet.query.filter_by(session_id=self.current_session.id, is_settled=False).all()
        
        for bet in bets:
            user = User.query.get(bet.user_id)
            payout = 0
            
            # 배당 계산
            if bet.bet_target == self.current_session.winner:
                if bet.bet_target == 'player':
                    payout = bet.bet_amount * 2  # 1:1
                elif bet.bet_target == 'banker':
                    payout = int(bet.bet_amount * 1.95)  # 19:20
                elif bet.bet_target == 'tie':
                    payout = bet.bet_amount * 9  # 8:1
            
            # 유저에게 지급
            if payout > 0:
                user.chips += payout
                bet.payout = payout
                print(f"💰 {user.username}: {bet.bet_target} {bet.bet_amount} → {payout} 칩")
            
            bet.is_settled = True
        
        db.session.commit()
    
    def _finish_round(self):
        self.current_session.is_active = False
        db.session.commit()
        self.current_session = None
        print(f"✅ 라운드 완료, 다음 라운드 준비중...")

# 전역 게임 상태 인스턴스
game_state = GameState()

# 로그인 검증
def login_required(f):
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# 라우트들
@app.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='잘못된 사용자명 또는 비밀번호입니다.')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='이미 존재하는 사용자명입니다.')
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            chips=10000
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/api/game/state')
@login_required
def get_game_state():
    try:
        user = User.query.get(session['user_id'])
        current_session = GameSession.query.filter_by(is_active=True).first()
        
        if not current_session:
            return jsonify({
                'success': True,
                'game_state': {
                    'state': 'waiting',
                    'round_number': 1,
                    'player_score': None,
                    'banker_score': None,
                    'winner': None,
                    'player_cards_display': [],
                    'banker_cards_display': [],
                    'total_bets': {'banker': 0, 'player': 0, 'tie': 0}
                },
                'timer_info': {'countdown': {'formatted_time': '00:00', 'percentage': 0}},
                'user_chips': user.chips,
                'active_users': [{'username': user.username, 'chips': user.chips, 'is_current_user': True}]
            })
        
        # 타이머 계산
        now = datetime.utcnow()
        elapsed = (now - current_session.phase_start).total_seconds()
        
        time_limits = {'waiting': 5, 'betting': 15, 'dealing': 5, 'result': 8}
        max_time = time_limits.get(current_session.state, 10)
        remaining = max(0, max_time - elapsed)
        percentage = max(0, min(100, (remaining / max_time) * 100))
        
        timer_info = {
            'countdown': {
                'formatted_time': f"{int(remaining//60):02d}:{int(remaining%60):02d}",
                'percentage': percentage,
                'is_warning': remaining < 5
            }
        }
        
        # 카드 정보
        player_cards = json.loads(current_session.player_cards) if current_session.player_cards else []
        banker_cards = json.loads(current_session.banker_cards) if current_session.banker_cards else []
        
        # 베팅 총액 계산
        bets = Bet.query.filter_by(session_id=current_session.id).all()
        total_bets = {'banker': 0, 'player': 0, 'tie': 0, 'banker_pair': 0, 'player_pair': 0}
        for bet in bets:
            total_bets[bet.bet_target] = total_bets.get(bet.bet_target, 0) + bet.bet_amount
        
        return jsonify({
            'success': True,
            'game_state': {
                'session_id': current_session.id,
                'round_number': current_session.round_number,
                'state': current_session.state,
                'player_score': current_session.player_score,
                'banker_score': current_session.banker_score,
                'winner': current_session.winner,
                'player_cards_display': player_cards,
                'banker_cards_display': banker_cards,
                'total_bets': total_bets
            },
            'timer_info': timer_info,
            'user_chips': user.chips,
            'active_users': [{'username': user.username, 'chips': user.chips, 'is_current_user': True}]
        })
        
    except Exception as e:
        print(f"API 오류: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bet', methods=['POST'])
@login_required
def place_bet():
    try:
        user = User.query.get(session['user_id'])
        data = request.json
        
        bet_target = data.get('bet_target')
        bet_amount = int(data.get('bet_amount', 0))
        
        # 검증
        if bet_amount < 100 or bet_amount > user.chips:
            return jsonify({'success': False, 'error': '베팅 금액이 올바르지 않습니다.'})
        
        current_session = GameSession.query.filter_by(is_active=True).first()
        if not current_session or current_session.state != 'betting':
            return jsonify({'success': False, 'error': '현재 베팅할 수 없습니다.'})
        
        # 중복 베팅 확인
        existing = Bet.query.filter_by(
            user_id=user.id, 
            session_id=current_session.id, 
            bet_target=bet_target
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': '이미 베팅하셨습니다.'})
        
        # 베팅 생성
        bet = Bet(
            user_id=user.id,
            session_id=current_session.id,
            bet_target=bet_target,
            bet_amount=bet_amount
        )
        
        user.chips -= bet_amount
        db.session.add(bet)
        db.session.commit()
        
        print(f"베팅: {user.username} -> {bet_target}: {bet_amount}")
        
        return jsonify({
            'success': True,
            'remaining_chips': user.chips,
            'message': '베팅 완료!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"베팅 오류: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 테스트 유저 생성
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password_hash=generate_password_hash('admin'), chips=100000)
            test1 = User(username='test1', password_hash=generate_password_hash('1234'), chips=10000)
            test2 = User(username='test2', password_hash=generate_password_hash('1234'), chips=10000)
            
            db.session.add(admin)
            db.session.add(test1)
            db.session.add(test2)
            db.session.commit()
            print("✅ 테스트 계정 생성 완료")
    
    print("🎮 바카라 게임 서버 시작!")
    print("🔗 http://localhost:5001 에서 접속하세요")
    
    # 게임 루프 시작
    game_state.start_game_loop()
    
    app.run(debug=True, host='0.0.0.0', port=5001)