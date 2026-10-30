"""历史记录蓝图：查询用户的历史实验报告（待实现）。"""
from flask import Blueprint, render_template, url_for, session, redirect
from models import db, Report

history_bp = Blueprint("history", __name__, url_prefix="/history")


@history_bp.route("/", methods=["GET"])
def get_history():# session里现在有的内容：{"user_id": 1, "user_type": "student", "is_login": True}
    # 1.获取用户的ID，前提：用户必须登录。若没有登录就提供登录的url
    if not session.get("is_login"):
        return redirect(url_for("login.login"))  # 跳转到登录页
    user_id = session.get("user_id")  # 获取用户ID
    if not user_id:
        return redirect(url_for("login.login"))  # 跳转到登录页

    # 2.直接查 Report 表：过滤该用户 + 按创建时间倒序 + 最多 10 条
    #    （不用先查 User 再取 .histories：排序和条数限制只有在 SQL 里做才准确）
    reports = db.session.scalars(
        db.select(Report)
        .filter(Report.user_id == user_id)
        .order_by(Report.created_at.desc())   # desc = 倒序，最新的排最前
        .limit(10)
    ).all()

    # 3.最后返回结果：把报告列表传给模板
    return render_template("history.html", reports=reports)

@history_bp.route("/models" , methods=["GET"])
def check_models():
    if not session.get("is_login"):
        return redirect(url_for("login.login"))
    