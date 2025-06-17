# models/user.py
from flask_login import UserMixin
from . import db
from config import Config
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    chips = db.Column(db.Integer, default=Config.GAME_CONFIG['DEFAULT_CHIPS'])
    
    # 게임 상태 관련
    is_in_game = db.Column(db.Boolean, default=False)
    current_session_id = db.Column(db.Integer, db.ForeignKey('game_sessions.id'), nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 통계
    total_games = db.Column(db.Integer, default=0)
    total_wins = db.Column(db.Integer, default=0)
    total_bet_amount = db.Column(db.Integer, default=0)
    
    # 관계 설정
    current_session = db.relationship('GameSession', foreign_keys=[current_session_id], backref='current_players')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_chip_distribution(self):
        """보유 칩을 단위별로 분해"""
        denominations = Config.CHIP_DENOMINATIONS
        chip_counts = {}
        remaining = self.chips
        
        for denom in denominations:
            chip_counts[denom], remaining = divmod(remaining, denom)
        
        return chip_counts
    
    def can_bet(self, amount):
        """베팅 가능 여부 확인"""
        return (
            self.chips >= amount and 
            amount >= Config.GAME_CONFIG['MIN_BET'] and 
            amount <= Config.GAME_CONFIG['MAX_BET']
        )
    
    def update_activity(self):
        """마지막 활동 시간 업데이트"""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def add_chips(self, amount):
        """칩 추가"""
        self.chips += amount
        db.session.commit()
    
    def subtract_chips(self, amount):
        """칩 차감"""
        if self.chips >= amount:
            self.chips -= amount
            db.session.commit()
            return True
        return False
    
    def get_win_rate(self):
        """승률 계산"""
        if self.total_games == 0:
            return 0
        return round((self.total_wins / self.total_games) * 100, 1)