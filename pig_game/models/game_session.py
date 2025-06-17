# models/game_session.py
from . import db
from datetime import datetime
import json

class GameState:
    WAITING = "waiting"
    FIRST_DEAL = "first_deal"
    BETTING = "betting"
    SECOND_DEAL = "second_deal"
    RESULT = "result"
    FINISHED = "finished"

class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 게임 상태
    state = db.Column(db.String(20), default=GameState.WAITING)
    round_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    
    # 타이머 관련
    state_started_at = db.Column(db.DateTime, default=datetime.utcnow)
    state_duration = db.Column(db.Integer, default=0)  # 현재 상태의 제한 시간(초)
    
    # 카드 정보 (JSON으로 저장)
    player_cards = db.Column(db.Text)  # JSON: ["AS", "KH"]
    banker_cards = db.Column(db.Text)  # JSON: ["2C", "9D"]
    
    # 게임 결과
    player_score = db.Column(db.Integer)
    banker_score = db.Column(db.Integer)
    winner = db.Column(db.String(20))  # 'player', 'banker', 'tie'
    has_player_pair = db.Column(db.Boolean, default=False)
    has_banker_pair = db.Column(db.Boolean, default=False)
    
    # 베팅 정보 (JSON으로 저장)
    bets_data = db.Column(db.Text)  # JSON: {user_id: {target: amount}}
    
    # 총 베팅 금액
    total_player_bets = db.Column(db.Integer, default=0)
    total_banker_bets = db.Column(db.Integer, default=0)
    total_tie_bets = db.Column(db.Integer, default=0)
    total_player_pair_bets = db.Column(db.Integer, default=0)
    total_banker_pair_bets = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<GameSession {self.id} - {self.state}>'
    
    def get_player_cards(self):
        """플레이어 카드 리스트 반환"""
        if self.player_cards:
            return json.loads(self.player_cards)
        return []
    
    def set_player_cards(self, cards):
        """플레이어 카드 설정"""
        self.player_cards = json.dumps(cards)
    
    def get_banker_cards(self):
        """뱅커 카드 리스트 반환"""
        if self.banker_cards:
            return json.loads(self.banker_cards)
        return []
    
    def set_banker_cards(self, cards):
        """뱅커 카드 설정"""
        self.banker_cards = json.dumps(cards)
    
    def get_bets(self):
        """베팅 정보 딕셔너리 반환"""
        if self.bets_data:
            return json.loads(self.bets_data)
        return {}
    
    def set_bets(self, bets):
        """베팅 정보 설정"""
        self.bets_data = json.dumps(bets)
    
    def add_bet(self, user_id, bet_target, amount):
        """베팅 추가"""
        bets = self.get_bets()
        if str(user_id) not in bets:
            bets[str(user_id)] = {}
        
        bets[str(user_id)][bet_target] = amount
        self.set_bets(bets)
        
        # 총 베팅 금액 업데이트
        self._update_total_bets()
    
    def _update_total_bets(self):
        """총 베팅 금액 재계산"""
        bets = self.get_bets()
        totals = {
            'player': 0,
            'banker': 0,
            'tie': 0,
            'player_pair': 0,
            'banker_pair': 0
        }
        
        for user_bets in bets.values():
            for bet_target, amount in user_bets.items():
                if bet_target in totals:
                    totals[bet_target] += amount
        
        self.total_player_bets = totals['player']
        self.total_banker_bets = totals['banker']
        self.total_tie_bets = totals['tie']
        self.total_player_pair_bets = totals['player_pair']
        self.total_banker_pair_bets = totals['banker_pair']
    
    def change_state(self, new_state, duration=0):
        """게임 상태 변경"""
        self.state = new_state
        self.state_started_at = datetime.utcnow()
        self.state_duration = duration
        db.session.commit()
    
    def get_remaining_time(self):
        """현재 상태의 남은 시간(초)"""
        if not self.state_duration:
            return 0
        
        elapsed = (datetime.utcnow() - self.state_started_at).seconds
        remaining = self.state_duration - elapsed
        return max(0, remaining)
    
    def is_state_expired(self):
        """현재 상태가 만료되었는지 확인"""
        return self.get_remaining_time() == 0
    
    def to_dict(self):
        """딕셔너리로 변환 (API 응답용)"""
        return {
            'id': self.id,
            'state': self.state,
            'round_number': self.round_number,
            'player_cards': self.get_player_cards(),
            'banker_cards': self.get_banker_cards(),
            'player_score': self.player_score,
            'banker_score': self.banker_score,
            'winner': self.winner,
            'has_player_pair': self.has_player_pair,
            'has_banker_pair': self.has_banker_pair,
            'remaining_time': self.get_remaining_time(),
            'total_bets': {
                'player': self.total_player_bets,
                'banker': self.total_banker_bets,
                'tie': self.total_tie_bets,
                'player_pair': self.total_player_pair_bets,
                'banker_pair': self.total_banker_pair_bets
            }
        }