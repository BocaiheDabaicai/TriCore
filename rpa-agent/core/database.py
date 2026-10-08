# 数据库连接 —— SQLite 单文件（和 kb-agent / study-agent 同一套做法）
# 连接串写相对路径：数据库文件落在"启动目录"下，manager 用 cwd=rpa-agent 启动，所以文件就在 rpa-agent/ 里

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# check_same_thread=False：SQLite 默认禁止跨线程用同一个连接，而这个服务里
# 浏览器执行线程和 FastAPI 的请求线程都会写运行记录，必须放开这个限制
# （放开后靠 SQLAlchemy 的连接池 + SQLite 自身的写锁保证安全；我们的写都是短事务）
engine = create_engine("sqlite:///rpa_agent.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """所有表模型的基类，继承它就会被 create_all 建表"""


def get_db():
    """FastAPI 依赖注入用：每个请求一个会话，用完关掉"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
