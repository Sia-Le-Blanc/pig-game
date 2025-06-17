# init_db.py
import os
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.user import User
from models.game_session import GameSession
from config import Config

def init_database():
    """데이터베이스 초기화"""
    print("🗃️ 데이터베이스 초기화 시작...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 기존 테이블 삭제
            db.drop_all()
            print("🗑️ 기존 테이블 삭제 완료")
            
            # 새 테이블 생성
            db.create_all()
            print("✅ 새 테이블 생성 완료")
            
            # 테이블 확인
            tables = db.engine.table_names()
            print(f"📋 생성된 테이블: {', '.join(tables)}")
            
            # 테스트 사용자 생성 여부 확인
            create_test_users = input("\n🧪 테스트 사용자를 생성하시겠습니까? (y/n): ").lower().strip()
            
            if create_test_users == 'y':
                default_chips = Config.GAME_CONFIG['DEFAULT_CHIPS']
                
                test_users = [
                    User(username="admin", password="admin", chips=100000),
                    User(username="test1", password="1234", chips=default_chips),
                    User(username="test2", password="1234", chips=default_chips),
                    User(username="test3", password="1234", chips=default_chips),
                    User(username="test4", password="1234", chips=default_chips),
                ]
                
                for user in test_users:
                    # 중복 사용자 확인
                    existing_user = User.query.filter_by(username=user.username).first()
                    if not existing_user:
                        db.session.add(user)
                        print(f"   👤 {user.username} 생성 (칩: {user.chips:,})")
                    else:
                        print(f"   ⚠️ {user.username} 이미 존재")
                
                db.session.commit()
                print("✅ 테스트 사용자 생성 완료")
                
                print("\n📝 테스트 계정 정보:")
                for user in test_users:
                    print(f"   - ID: {user.username} / PW: {user.password}")
            
            print("\n🎮 데이터베이스 초기화 완료!")
            print("💡 이제 'python app.py'로 서버를 시작할 수 있습니다.")
            
        except Exception as e:
            print(f"❌ 데이터베이스 초기화 오류: {e}")
            db.session.rollback()
            return False
    
    return True

def reset_game_sessions():
    """모든 게임 세션 초기화"""
    print("🔄 게임 세션 초기화...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 모든 게임 세션 삭제
            GameSession.query.delete()
            
            # 모든 유저의 게임 상태 초기화
            User.query.update({
                'is_in_game': False,
                'current_session_id': None
            })
            
            db.session.commit()
            print("✅ 게임 세션 초기화 완료")
            
        except Exception as e:
            print(f"❌ 게임 세션 초기화 오류: {e}")
            db.session.rollback()

def show_database_info():
    """데이터베이스 정보 표시"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n📊 데이터베이스 현황:")
            print(f"   📁 DB 위치: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            user_count = User.query.count()
            session_count = GameSession.query.count()
            
            print(f"   👥 등록된 사용자: {user_count}명")
            print(f"   🎮 게임 세션: {session_count}개")
            
            if user_count > 0:
                print("\n👤 사용자 목록:")
                users = User.query.all()
                for user in users:
                    status = "🎮 게임중" if user.is_in_game else "💤 대기중"
                    print(f"   - {user.username}: {user.chips:,}칩 ({status})")
            
        except Exception as e:
            print(f"❌ 데이터베이스 정보 조회 오류: {e}")

if __name__ == "__main__":
    print("🎯 바카라 게임 데이터베이스 관리")
    print("=" * 50)
    
    while True:
        print("\n📋 메뉴:")
        print("1. 데이터베이스 초기화")
        print("2. 게임 세션 초기화")
        print("3. 데이터베이스 정보 보기")
        print("4. 종료")
        
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == '1':
            init_database()
        elif choice == '2':
            reset_game_sessions()
        elif choice == '3':
            show_database_info()
        elif choice == '4':
            print("👋 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")
    
    print("\n🎮 데이터베이스 관리 완료!")