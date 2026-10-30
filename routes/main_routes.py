"""首页蓝图：AI 实验报告生成。"""
from flask import Blueprint, render_template, request, session

# ORM模型集中在 models.py：Report 定义在那儿，这里只导入
from models import db, Report
from ai_client import client
from file_reader import extract_file_content

main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        user_input = request.form["prompt"]  # 获取用户写的题目
        # 调用AI，记得加“实验报告”的系统指令
        response = client.chat.completions.create(
            model="DeepSeek-V4-Pro",  # DeepSeek 对话模型
            messages=[
                {"role": "system", "content": "你是实验报告写作助手，请按‘目的、原理、步骤、数据、分析’结构输出。"},
                {"role": "user", "content": user_input},
            ],
        )
        result = response.choices[0].message.content
        # 登录用户才落库；created_at 由 default 自动填，user_id 从 session 拿
        if session.get("is_login"):
            db.session.add(Report(
                user_id=session["user_id"],
                title=user_input,
                prompt=user_input,
                content=result,
            ))
            db.session.commit()

    return render_template("index.html", ai_text=result)


# @main_bp.route("/editor-demo")
# def editor_demo():
#     """TinyMCE 富文本编辑器演示页（纯静态展示，不涉及 AI 与数据库）。"""
#     return render_template("cache_word.html")

