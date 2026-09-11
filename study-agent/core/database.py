# SQLAlchemy 数据库配置 —— 与 kb-agent / ai-assistant 同一个套路
# SQLite 一个 .db 文件就是整个数据库，无需安装数据库服务

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 数据库文件路径 —— 项目根目录下的 study_agent.db
# 注意：相对路径基于"启动命令所在目录"（要在 study-agent 目录下启动服务）
DATABASE_URL = "sqlite:///study_agent.db"

# 引擎 —— 负责和数据库文件通信
engine = create_engine(DATABASE_URL, echo=False)

# 会话工厂 —— 每次数据库操作从这里拿一个连接
SessionLocal = sessionmaker(bind=engine, autoflush=False)


# 所有 ORM 模型的基类：模型类继承它，create_all 就能扫描到并建表
class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖：每个请求拿一个数据库会话，用完自动关掉"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
