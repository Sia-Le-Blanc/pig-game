# init_db.py 다시 확실히 실행

from app import create_app
from models.user import db

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ User 테이블 새로 생성 완료")
