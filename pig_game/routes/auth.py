# routes/auth.py
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from models import db, User
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """회원가입"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # 입력 검증
        if not username or not password:
            return render_template("register.html", error="사용자명과 비밀번호를 입력해주세요.")
        
        if len(username) < 3:
            return render_template("register.html", error="사용자명은 3자 이상이어야 합니다.")
        
        if len(password) < 4:
            return render_template("register.html", error="비밀번호는 4자 이상이어야 합니다.")
        
        # 중복 사용자 확인
        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="이미 존재하는 사용자입니다.")
        
        # 새 사용자 생성
        user = User(
            username=username, 
            password=password, 
            chips=Config.GAME_CONFIG['DEFAULT_CHIPS']
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash("회원가입이 완료되었습니다. 로그인해주세요.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            return render_template("register.html", error="회원가입 중 오류가 발생했습니다.")
    
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """로그인"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            return render_template("login.html", error="사용자명과 비밀번호를 입력해주세요.")
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session["user_id"] = user.id
            user.update_activity()
            
            flash(f"환영합니다, {user.username}님!", "success")
            return redirect(url_for("game.index"))
        else:
            return render_template("login.html", error="잘못된 로그인 정보입니다.")
    
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    """로그아웃"""
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            # 게임 중이었다면 상태 초기화
            user.is_in_game = False
            user.current_session_id = None
            db.session.commit()
    
    session.clear()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for("auth.login"))

def login_required(f):
    """로그인 필수 데코레이터"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """현재 로그인한 사용자 반환"""
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None