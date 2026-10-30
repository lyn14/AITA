"""应用入口：创建 Flask 实例并注册各功能蓝图。"""
import os

from flask import Flask

import config
from models import db, migrate
from routes.login_routes import login_bp
from routes.history_routes import history_bp
from routes.main_routes import main_bp
from routes.tutorial_routes import tutorial_bp
from routes.AI_client_routes import AI_client_bp

app = Flask(__name__)

# 把 config.py 里的 SQLALCHEMY_DATABASE_URI 等配置加载到应用上
app.config.from_object(config)

# session 签名密钥：优先读 .env，开发环境兜底一个随机值
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# 上传文件大小上限：20MB（文献 PDF / 课件 PPTX / 图片都够用）
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

# 建立 SQL 联系：把 db / migrate 绑定到真正的应用实例
db.init_app(app)
migrate.init_app(app, db)

# 注册蓝图：main 挂在根路径，history 和 tutorial 各自带 url_prefix
app.register_blueprint(main_bp)
app.register_blueprint(history_bp)
app.register_blueprint(tutorial_bp)
app.register_blueprint(login_bp)
app.register_blueprint(AI_client_bp)


if __name__ == "__main__":
    app.run(debug=True , port = 5050 , host = "0.0.0.0")

#! 以后有新的依赖就安装在venv里，别忘了更新requirements！