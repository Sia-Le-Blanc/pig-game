from flask import Flask, render_template, request, redirect, session, url_for
from config import Config
from models.user import db, User
from models.game import play_game
from services.betting import evaluate_bet

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    # -------------------------------
    # 홈: 로그인 유저만 접근 가능
    # -------------------------------
    @app.route("/", methods=["GET"])
    def home():
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")

        user = User.query.get(user_id)
        return render_template("index.html", user=user)

    # -------------------------------
    # 회원가입
    # -------------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            if User.query.filter_by(username=username).first():
                return render_template("register.html", error="이미 존재하는 사용자입니다.")

            user = User(username=username, password=password, chips=1000)
            db.session.add(user)
            db.session.commit()

            return redirect("/login")

        return render_template("register.html")

    # -------------------------------
    # 로그인
    # -------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            user = User.query.filter_by(username=username).first()

            if user and user.password == password:
                session["user_id"] = user.id
                return redirect("/")
            else:
                return render_template("login.html", error="잘못된 로그인 정보입니다.")

        return render_template("login.html")

    # -------------------------------
    # 로그아웃
    # -------------------------------
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    # -------------------------------
    # 게임 실행
    # -------------------------------
    @app.route("/game", methods=["POST"])
    def game():
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")

        user = User.query.get(user_id)
        bet_target = request.form["bet_target"]
        bet_amount = int(request.form["bet_amount"])

        if user.chips < bet_amount:
            return "보유 칩이 부족합니다.", 400

        result = play_game()
        bet_win, bet_change = evaluate_bet(bet_target, result["winner"], bet_amount)

        if bet_win:
            user.chips += bet_change
        else:
            user.chips -= bet_change

        db.session.commit()

        result.update({
            "bet_win": bet_win,
            "bet_change": bet_change,
            "final_chips": user.chips
        })

        return render_template("index.html", result=result, user=user)

    return app

# -------------------------------
# 앱 실행
# -------------------------------
if __name__ == "__main__":
    app = create_app()
    print("📍 DB 경로:", app.config["SQLALCHEMY_DATABASE_URI"])
    app.run(debug=True)
    
