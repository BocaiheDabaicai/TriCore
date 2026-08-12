# SQLAlchemy 是 Python 最常用的 ORM（对象关系映射）库
# ORM 的作用：让你用 Python 类来操作数据库表，不用手写 SQL

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 1. 数据库文件路径 —— 项目根目录下的 kb_agent.db
#    SQLite 不需要安装，一个 .db 文件就是整个数据库
DATABASE_URL = "sqlite:///kb_agent.db"

# 2. 创建"引擎"—— 负责和数据库文件通信
#    echo=True 会在终端打印每条 SQL 语句，方便学习
engine = create_engine(DATABASE_URL, echo=True)

# 3. 创建"会话工厂"—— 每次请求从这里拿一个数据库连接
SessionLocal = sessionmaker(bind=engine, autoflush=False)


# 4. 所有 ORM 模型的基类
#    你定义的每个表类都继承它，SQLAlchemy 就能识别
class Base(DeclarativeBase):
    pass
