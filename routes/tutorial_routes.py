"""教程蓝图：接口测试用（原 app.py 中的 /tutorial 路由）。"""
from flask import Blueprint, jsonify, request

tutorial_bp = Blueprint("tutorial", __name__, url_prefix="/tutorial")


@tutorial_bp.route("/", methods=["GET", "POST"])
def tutorial():
    age = request.args.get("age")
    pwd = request.args.get("pwd")
    print(f"Received age: {age}, pwd: {pwd}")
    return jsonify({"age": age, "pwd": pwd})
