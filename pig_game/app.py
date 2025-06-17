# app.py
from flask import Flask, redirect, url_for
from config import Config
from models import db

def create_app():
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # Blueprint 등록
    from routes.auth import auth_bp
    from routes.game import game_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    
    # 루트 URL 리다이렉트
    @app.route('/')
    def root():
        return redirect(url_for('game.index'))
    
    # 애플리케이션 컨텍스트에서 DB 테이블 생성
    with app.app_context():
        try:
            db.create_all()
            print("✅ 데이터베이스 테이블 생성 완료")
        except Exception as e:
            print(f"❌ 데이터베이스 오류: {e}")
    
    return app

if __name__ == "__main__":
    app = create_app()
    print("📍 DB 경로:", app.config["SQLALCHEMY_DATABASE_URI"])
    print("🎮 바카라 게임 서버 시작!")
    print("🔗 http://localhost:5000 에서 접속하세요")
    
    # 게임 매니저 시작
    try:
        from core.game_manager import GameManager
        game_manager = GameManager()
        game_manager.start_game_loop()
        print("🎯 게임 매니저 시작됨")
    except Exception as e:
        print(f"⚠️ 게임 매니저 시작 실패: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5001)