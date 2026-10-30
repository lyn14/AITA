from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash , check_password_hash

# 模型和 db/migrate 集中在 models.py，路由文件只导入使用
from models import db, User

login_bp = Blueprint ('login' , __name__)

# 蓝图没有 config 属性，config.py 要在 app.py 里用
# app.config.from_object(config) 加载到真正的应用上

@login_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_pwd = request.form["confirm_password"]
        user_type = request.form["user_types"]

        # 1.查重：用户名已存在则拒绝
        exists = db.session.scalar(
            db.select(User).filter(User.username == username)
        )
        if exists:
            return render_template("register.html", error="用户名已被注册！")

        if password != confirm_pwd:
            return render_template("register.html", error="两次输入的密码不一致！")

        # 2.入库：密码必须存哈希，不能存明文
        new_user = User(
            username=username,
            password=generate_password_hash(password),
        )
        db.session.add(new_user)
        # 注意千万不能忘记commit！
        db.session.commit()

        # 3.注册成功，自动登录并跳转首页
        session["user_id"] = new_user.id
        session["user_type"] = user_type
        session["is_login"] = True
        return redirect(url_for("main.index"))

    # GET 请求：展示注册表单
    return render_template("register.html", error=None)

@login_bp.route("/login", methods=["POST" , "GET"])
def login():
    # 获取用户名和密码
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_type = request.form["user_types"]

        # 根据用户类型查询数据库
        user = db.session.scalar (db.select(User).filter(User.username == username))

        if user is None:
            # 用户名不存在：不提示"用户不存在"，避免泄露注册信息
            error = "用户名或密码错误！"
        elif not check_password_hash(user.password, password):
            # 密码不匹配（数据库里存的是哈希，用 check_password_hash 校验）
            error = "用户名或密码错误！"
        else:
            # 校验通过：写入 session，标记登录状态
            # session是一个网站的全局变量，存储在服务器端，浏览器端只存储一个session_id的cookie
            session["user_id"] = user.id
            session["user_type"] = user_type
            session["is_login"] = True
            return redirect(url_for("main.index"))

        return render_template("login.html", error=error)

    # GET 请求：展示登录表单
    return render_template("login.html", error=None)

