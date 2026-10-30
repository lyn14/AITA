from flask import Flask, render_template, request , jsonify
from flask_sqlalchemy import SQLAlchemy
import openai  # 或 deepseek, 国内用 'dashscope' 也行
import os
from dotenv import load_dotenv
import pymysql

#这是一个练习用的程序，不拿来实现最终的网页
load_dotenv()
app = Flask(__name__)
client = openai.OpenAI(api_key=os.getenv("PARATERA_API_KEY") , base_url="https://llmapi.paratera.com/v1/")  # 以OpenAI格式为例


# db=SQLAlchemy(app)
# class Report(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100))
#     content = db.Column(db.Text, nullable=False)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    todo:1.下载postman作为一个weib端的接口测试工具，方便调试接口
    2. 继续学习flask的路由和请求处理，尤其是POST请求的处理方式。
    """
    with open( authentication.txt , mode = "r" , encoding = "utf-8") as f:
        api_key = f.read().strip()
        
    # result = ""
    # if request.method == "POST":
    #     user_input = request.form["prompt"]  # 获取用户写的题目
    #     # 调用AI，记得加“实验报告”的系统指令
    #     response = client.chat.completions.create(
    #         model="DeepSeek-V4-Pro",  # DeepSeek 对话模型
    #         messages=[
    #             {"role": "system", "content": "你是实验报告写作助手，请按‘目的、原理、步骤、数据、分析’结构输出。"},
    #             {"role": "user", "content": user_input}
    #         ]
    #     )
    #     result = response.choices[0].message.content

    # if request.method == "POST" and result:
    #     # 将生成的实验报告存入数据库
    #     new_report = Report(title=user_input, content=result)
    #     db.session.add(new_report)
    #     db.session.commit()
    # return render_template("index.html", ai_text=result)

# @app.route("/history" , methods=["GET"])
# def history( report_id=0 ):
#     report_content = Report.query.get(report_id)
#     return render_template("history.html", report_content=report_content)
@app.route("/tutorial" , methods=["GET" , "POST"])
def tutorial():
    age = request.args.get("age")
    pwd = request.args.get("pwd")
    print(f"Received age: {age}, pwd: {pwd}")
    request.json.get
    return jsonify({"age": age, "pwd": pwd})

if __name__ == "__main__":
    app.run(debug=True)

"""环境变更：venv"""