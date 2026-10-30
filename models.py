"""数据模型层：所有数据库表（模型）和 db / migrate 扩展集中在这里。

路由文件（login_routes / main_routes / history_routes ...）只负责"处理请求"，
需要用表时从本文件导入，不再各自定义模型——避免循环导入，也方便统一管理表结构。
"""
from datetime import datetime

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, Integer, MetaData, String, Text, Table, Column
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base (DeclarativeBase):
    metadata = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(column_0_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'
    })

db = SQLAlchemy (model_class = Base)

# 多对多中间表：一份报告可以调用多个 AI 模型，一个模型也可以参与多份报告
# 关键点：外键必须指向两边的"主键"（report.id / AI_models.model_number）。
# 时间戳列不能当外键目标（不唯一，而且原来 report 表里根本没有 created_at 列，
# 这就是 flask db migrate 报 NoReferencedColumnError 的原因）
Reports_AI_Models_Table = Table(
    "Reports_AI_Models",
    db.metadata,
    Column("report_id" , Integer , ForeignKey("report.id") , primary_key=True),
    Column("model_number" , Integer , ForeignKey("AI_models.model_number") , primary_key=True),
    # 这条"报告 ↔ 模型"调用关系建立的时间（即模型被调用的时刻）
    Column("assigned_at" , DateTime , default=datetime.now)
)

ReportSection_AI_Models_Table = Table(
    "ReportSection_AI_Models",
    db.metadata,
    Column("report_section_id" , Integer , ForeignKey("report_section.id") , primary_key=True),
    Column("model_number", Integer, ForeignKey("AI_models.model_number"), primary_key=True),
    Column("assigned_at", DateTime, default=datetime.now),
)

class User (Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer , primary_key=True , autoincrement=True)
    username: Mapped[str] = mapped_column(String(100) , nullable=False)
    password: Mapped[str] = mapped_column(String(200) , nullable=False)
    email: Mapped[str] = mapped_column(String(100) , nullable=True)

    # 一个用户可以有多份报告：外键在 Report 那边（report.user_id → user.id）
    # 这里只留 relationship 导航入口，不存外键列
    histories: Mapped[list["Report"]] = relationship("Report", back_populates="user")

class Report (Base): #prompt这块待修改，不直接存提示词，而是分别存每个section的提示词。
    __tablename__ = 'report'
    id: Mapped[int] = mapped_column(Integer, primary_key=True , autoincrement=True)
    # 外键放在"多"的这一边：多份报告属于同一个用户（与 Admin.permission_level 同款写法）
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id") , nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)    # 提示词长短不定，用 Text
    content: Mapped[str] = mapped_column(Text, nullable=False)   # AI 报告常超 5000 字，String(5000) 会报"数据过长"
    # 生成时间：报告落库时自动填（history_routes 里就是按它倒序取最近 10 条）
    created_at: Mapped[datetime] = mapped_column(DateTime , default=datetime.now , nullable=False)
    # 多对一：user_id 列的"高级替身"，与 User.histories 通过 back_populates 配对
    user: Mapped["User"] = relationship("User", back_populates="histories")
    # 多对多：一份报告（一个"时段"）可以调用多个模型。
    # 导航属性不能叫 created_at——那已经是上面的时间戳列名了，会撞名
    ai_models: Mapped[list["AI_Models"]] = relationship('AI_Models' , secondary=Reports_AI_Models_Table , back_populates="reports")
    # 一对多：一份报告由多个节组成（order_index 决定节的先后顺序）
    sections: Mapped[list["ReportSection"]] = relationship(back_populates="report" , order_by="ReportSection.order_index")

class Admin (Base):
    __tablename__ = 'admin'
    id: Mapped[int] = mapped_column(Integer , primary_key=True , autoincrement=True)

    # 外键：权限等级与权限内容
    permission_level: Mapped[int] = mapped_column(Integer , ForeignKey("permission.id") , nullable=False)
    # 一个管理员只能有一个权限等级，但是一个权限等级可以对应多个管理员，所以是多对一的关系，不用写中间表
    permission: Mapped["Permission"] = relationship("Permission" , back_populates="admins")


class Permission (Base):
    __tablename__ = 'permission'
    id: Mapped[int] = mapped_column(Integer , primary_key=True , autoincrement=True)
    permission_name: Mapped[str] = mapped_column(String(100) , nullable=False)

    # 补全与Admin的relationship（）
    admins: Mapped[list["Admin"]] = relationship("Admin" , back_populates="permission")

class AI_Models (Base): # 生成的结果对应的AI模型
    __tablename__ = 'AI_models'
    model_number: Mapped[int] = mapped_column(Integer , primary_key=True , nullable=False , autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(20) , nullable=False)

    # 多对多另一端：这个模型参与生成了哪些报告（"被调用的时段"记在中间表的 assigned_at 列里）
    reports: Mapped[list["Report"]] = relationship('Report' , secondary=Reports_AI_Models_Table , back_populates="ai_models")
    # 多对多：这个模型参与生成了哪些节（与 ReportSection.models 互相配对）
    sections: Mapped[list["ReportSection"]] = relationship("ReportSection", secondary=ReportSection_AI_Models_Table, back_populates="models")

class ReportSection (Base):
    """报告的一节：IMRD 的某一节 / 五段式的某一段，content 只存这一节的正文。"""
    __tablename__ = 'report_section'
    id: Mapped[int] = mapped_column(Integer , primary_key=True , autoincrement=True)
    # 多对一：这一节属于哪份报告（外键在"多"的这一边，与 Report.user_id 同款写法）
    report_id: Mapped[int] = mapped_column(Integer, ForeignKey("report.id"), nullable=False)
    section_key: Mapped[str] = mapped_column(String(50), nullable=False)
    section_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 冗余存名字，目录日后改动不影响历史
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 多对一：与 Report.sections 配对
    report: Mapped["Report"] = relationship(back_populates="sections")
    # 多对多：这一节由哪些模型协作生成（一节可多个模型，一个模型可参与多节）。
    # 注意：m2m 写法下 ReportSection 上【没有】model_number 列——
    # 编号存在中间表 ReportSection_AI_Models 里，由 relationship 自动维护
    models: Mapped[list["AI_Models"]] = relationship(
        "AI_Models", secondary=ReportSection_AI_Models_Table, back_populates="sections")
    # association_proxy 透过 models 关系"现取"每个模型的 model_name，用起来像普通属性
    model_names = association_proxy("models", "model_name")
    

migrate = Migrate (db=db)   # 同理，app 也在 app.py 里 migrate.init_app(app, db) 传入
