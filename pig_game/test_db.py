from app import create_app
from models.user import db, User

app = create_app()

with app.app_context():

    db.create_all()
    print("User 테이블 생성 완료")

    test_user = User(username="test_user", password="1234")
    db.session.add(test_user)
    db.session.commit()
    print("테스트 유저 추가 완료")

    user = User.query.filter_by(username="test_user").first()
    print(f"테스트 유저 정보: {user.username}, {user.password}, {user.chips}")