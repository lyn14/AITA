"""SQLAlchemy Configuration"""

HOSTNAME = '127.0.0.1'
USERNAME = 'root'
PASSWORD = '123456'
PORT = 3306
DATABASE = 'test_ver1'

# 连接flask与SQL
# 注意：驱动用 pymysql（纯 Python，requirements 里装的就是它）；
# 之前写的 mysqldb 需要 mysqlclient 这个 C 扩展包，venv 里没装会直接 import 报错
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4'