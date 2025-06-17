# config.py
import os

class Config:
    # Flask 기본 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
    
    # 데이터베이스 설정
    SQLALCHEMY_DATABASE_URI = (
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'db.sqlite3')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 게임 설정
    GAME_CONFIG = {
        'MAX_PLAYERS': 4,
        'BETTING_TIME_SECONDS': 30,
        'RESULT_DISPLAY_TIME_SECONDS': 10,
        'WAITING_TIME_SECONDS': 5,
        'DEFAULT_CHIPS': 10000,
        'MIN_BET': 100,
        'MAX_BET': 50000
    }
    
    # 칩 단위
    CHIP_DENOMINATIONS = [10000, 5000, 1000, 500, 100]
    
    # 배당률
    PAYOUT_RATES = {
        'player': 1.0,
        'banker': 0.95,
        'tie': 8.0,
        'player_pair': 11.0,
        'banker_pair': 11.0
    }