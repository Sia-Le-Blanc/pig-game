# core/game_manager.py
from models import db, GameSession, User
from models.game_session import GameState
from .game_logic import BaccaratGame
from .betting_system import BettingSystem
from config import Config
from datetime import datetime
import threading
import time

class GameManager:
    """바카라 게임 매니저 - 싱글톤 패턴"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.current_session = None
            self.baccarat_game = BaccaratGame()
            self.betting_system = BettingSystem()
            self.timer_thread = None
            self.running = False
            self.app = None  # Flask 앱 저장용
            self.initialized = True
            print("🎯 GameManager 초기화됨")
    
    def set_app(self, app):
        """Flask 애플리케이션 설정"""
        self.app = app
        print("🔗 Flask 앱 연결됨")
    
    def start_game_loop(self):
        """게임 루프 시작"""
        if self.running:
            print("⚠️ 게임 루프가 이미 실행 중입니다.")
            return
            
        self.running = True
        self.timer_thread = threading.Thread(target=self._game_loop, daemon=True)
        self.timer_thread.start()
        print("🎮 게임 루프 시작됨")
    
    def stop_game_loop(self):
        """게임 루프 중단"""
        self.running = False
        if self.timer_thread:
            self.timer_thread.join(timeout=2)
        print("⏹️ 게임 루프 중단됨")
    
    def _game_loop(self):
        """메인 게임 루프 (수정됨)"""
        consecutive_errors = 0
        max_errors = 5
        
        while self.running:
            try:
                if self.app:
                    with self.app.app_context():
                        self._process_game_state()
                        consecutive_errors = 0  # 성공하면 에러 카운트 리셋
                else:
                    print("⚠️ Flask 앱이 설정되지 않았습니다.")
                    time.sleep(5)
                    continue
                
                time.sleep(2)  # 2초마다 체크 (부하 감소)
                
            except Exception as e:
                consecutive_errors += 1
                print(f"게임 루프 오류 ({consecutive_errors}/{max_errors}): {e}")
                
                if consecutive_errors >= max_errors:
                    print(f"❌ 연속 {max_errors}회 오류 발생. 게임 루프를 일시 중단합니다.")
                    time.sleep(30)  # 30초 대기 후 재시작
                    consecutive_errors = 0
                else:
                    time.sleep(5)  # 5초 대기
    
    def _process_game_state(self):
        """게임 상태 처리 (애플리케이션 컨텍스트 내에서 실행)"""
        try:
            # 현재 세션 조회
            if not self.current_session:
                self.current_session = GameSession.query.filter_by(is_active=True).first()
                
            if not self.current_session:
                self._start_new_session()
                return
            
            # DB에서 최신 상태 새로고침
            db.session.refresh(self.current_session)
            
            # 상태별 처리
            if self.current_session.state == GameState.WAITING:
                self._handle_waiting_state()
            elif self.current_session.state == GameState.FIRST_DEAL:
                self._handle_first_deal_state()
            elif self.current_session.state == GameState.BETTING:
                self._handle_betting_state()
            elif self.current_session.state == GameState.SECOND_DEAL:
                self._handle_second_deal_state()
            elif self.current_session.state == GameState.RESULT:
                self._handle_result_state()
            elif self.current_session.state == GameState.FINISHED:
                self._handle_finished_state()
                
        except Exception as e:
            print(f"게임 상태 처리 오류: {e}")
            # 에러 발생 시 DB 롤백
            db.session.rollback()
    
    def _start_new_session(self):
        """새 게임 세션 시작"""
        try:
            # 기존 활성 세션들 비활성화
            GameSession.query.filter_by(is_active=True).update({'is_active': False})
            
            # 새 세션 생성
            new_session = GameSession(
                round_number=self._get_next_round_number(),
                state=GameState.WAITING,
                phase_start_time=datetime.utcnow(),
                is_active=True
            )
            
            db.session.add(new_session)
            db.session.commit()
            
            self.current_session = new_session
            print(f"🆕 새 게임 세션 시작: Round #{new_session.round_number}")
            
        except Exception as e:
            print(f"새 세션 생성 오류: {e}")
            db.session.rollback()
    
    def _get_next_round_number(self):
        """다음 라운드 번호 조회"""
        try:
            last_session = GameSession.query.order_by(GameSession.round_number.desc()).first()
            return (last_session.round_number + 1) if last_session else 1
        except:
            return 1
    
    def _handle_waiting_state(self):
        """대기 상태 처리"""
        try:
            waiting_time = Config.GAME_CONFIG['WAITING_TIME']
            elapsed = (datetime.utcnow() - self.current_session.phase_start_time).total_seconds()
            
            if elapsed >= waiting_time:
                self._change_state(GameState.FIRST_DEAL)
                print(f"Round #{self.current_session.round_number}: 대기 → 첫 번째 카드")
                
        except Exception as e:
            print(f"대기 상태 처리 오류: {e}")
    
    def _handle_first_deal_state(self):
        """첫 번째 카드 분배 상태 처리"""
        try:
            # 첫 번째 카드 분배
            if not self.current_session.player_cards or not self.current_session.banker_cards:
                cards = self.baccarat_game.deal_initial_cards()
                
                self.current_session.player_cards = cards['player']
                self.current_session.banker_cards = cards['banker']
                
                db.session.commit()
                print(f"🃏 첫 번째 카드 분배 완료")
            
            # 베팅 상태로 전환
            deal_time = Config.GAME_CONFIG['FIRST_DEAL_TIME']
            elapsed = (datetime.utcnow() - self.current_session.phase_start_time).total_seconds()
            
            if elapsed >= deal_time:
                self._change_state(GameState.BETTING)
                print(f"Round #{self.current_session.round_number}: 첫 번째 카드 → 베팅")
                
        except Exception as e:
            print(f"첫 번째 카드 처리 오류: {e}")
    
    def _handle_betting_state(self):
        """베팅 상태 처리"""
        try:
            betting_time = Config.GAME_CONFIG['BETTING_TIME']
            elapsed = (datetime.utcnow() - self.current_session.phase_start_time).total_seconds()
            
            if elapsed >= betting_time:
                self._change_state(GameState.SECOND_DEAL)
                print(f"Round #{self.current_session.round_number}: 베팅 → 두 번째 카드")
                
        except Exception as e:
            print(f"베팅 상태 처리 오류: {e}")
    
    def _handle_second_deal_state(self):
        """두 번째 카드 분배 상태 처리"""
        try:
            # 두 번째 카드 필요한지 확인 및 분배
            current_cards = {
                'player': self.current_session.player_cards,
                'banker': self.current_session.banker_cards
            }
            
            additional_cards = self.baccarat_game.deal_additional_cards(current_cards)
            
            if additional_cards:
                if additional_cards.get('player'):
                    self.current_session.player_cards.extend(additional_cards['player'])
                if additional_cards.get('banker'):
                    self.current_session.banker_cards.extend(additional_cards['banker'])
                
                db.session.commit()
                print(f"🃏 추가 카드 분배 완료")
            
            # 결과 계산으로 전환
            deal_time = Config.GAME_CONFIG['SECOND_DEAL_TIME']
            elapsed = (datetime.utcnow() - self.current_session.phase_start_time).total_seconds()
            
            if elapsed >= deal_time:
                self._calculate_and_show_result()
                
        except Exception as e:
            print(f"두 번째 카드 처리 오류: {e}")
    
    def _handle_result_state(self):
        """결과 상태 처리"""
        try:
            result_time = Config.GAME_CONFIG['RESULT_TIME']
            elapsed = (datetime.utcnow() - self.current_session.phase_start_time).total_seconds()
            
            if elapsed >= result_time:
                self._change_state(GameState.FINISHED)
                print(f"Round #{self.current_session.round_number}: 결과 → 종료")
                
        except Exception as e:
            print(f"결과 상태 처리 오류: {e}")
    
    def _handle_finished_state(self):
        """종료 상태 처리"""
        try:
            # 베팅 정산
            self._settle_bets()
            
            # 세션 비활성화
            self.current_session.is_active = False
            self.current_session.ended_at = datetime.utcnow()
            db.session.commit()
            
            print(f"✅ Round #{self.current_session.round_number} 완료")
            
            # 다음 세션 준비
            self.current_session = None
            
        except Exception as e:
            print(f"게임 종료 처리 오류: {e}")
    
    def _calculate_and_show_result(self):
        """결과 계산 및 표시"""
        try:
            # 점수 계산
            player_score = self.baccarat_game.calculate_score(self.current_session.player_cards)
            banker_score = self.baccarat_game.calculate_score(self.current_session.banker_cards)
            
            # 승자 결정
            winner = self.baccarat_game.determine_winner(player_score, banker_score)
            
            # 결과 저장
            self.current_session.player_score = player_score
            self.current_session.banker_score = banker_score
            self.current_session.winner = winner
            
            self._change_state(GameState.RESULT)
            
            print(f"🎯 게임 결과: Player {player_score} vs Banker {banker_score} → {winner.upper()} 승!")
            
        except Exception as e:
            print(f"결과 계산 오류: {e}")
    
    def _settle_bets(self):
        """베팅 정산"""
        try:
            settled_bets = self.betting_system.settle_all_bets(
                self.current_session.id,
                self.current_session.winner
            )
            
            if settled_bets:
                print(f"💰 {len(settled_bets)}건의 베팅 정산 완료")
            
        except Exception as e:
            print(f"베팅 정산 오류: {e}")
    
    def _change_state(self, new_state):
        """게임 상태 변경"""
        try:
            self.current_session.state = new_state
            self.current_session.phase_start_time = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            print(f"상태 변경 오류: {e}")
            db.session.rollback()
    
    def get_current_session_safe(self):
        """안전한 현재 세션 조회 (애플리케이션 컨텍스트 필요 없음)"""
        if self.current_session:
            return {
                'id': self.current_session.id,
                'round_number': self.current_session.round_number,
                'state': self.current_session.state.value if self.current_session.state else 'waiting',
                'phase_start_time': self.current_session.phase_start_time.isoformat() if self.current_session.phase_start_time else None
            }
        return None