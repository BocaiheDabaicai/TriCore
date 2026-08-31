from fastapi import FastAPI
from sqlalchemy import inspect, text

from api.knowledge import router as knowledge_router
from api.myapi import router as myapi_router
from api.agent import router as agent_router
from api.missed import router as missed_router

# 数据库相关
from core.database import engine, Base
from models.knowledge import Knowledge
from models.message import Message
from models.vector import KnowledgeVector
from models.missed import MissedQuestion

app = FastAPI(title="企业知识库Agent", version="0.2.0")

# 在应用启动时自动建表
# Base.metadata.create_all 会扫描所有继承 Base 的类，对应生成数据库表
# 如果表已经存在就跳过（不会重复创建）
Base.metadata.create_all(bind=engine)


def ensure_columns():
    """
    轻量迁移：给旧库补新增的列
    create_all 只建"不存在的表"，不会给已存在的表加新列，
    所以模型加了字段后要手动补列（SQLite 的 ADD COLUMN 是安全操作，不动数据）
    """
    with engine.connect() as conn:
        cols = [c["name"] for c in inspect(conn).get_columns("knowledge")]
        if "keywords" not in cols:
            conn.execute(text("ALTER TABLE knowledge ADD COLUMN keywords VARCHAR(200)"))
            conn.commit()


ensure_columns()

app.include_router(knowledge_router)
app.include_router(myapi_router)
app.include_router(agent_router)
app.include_router(missed_router)


@app.get("/")
def root():
    return {"message": "企业知识库Agent 启动成功！"}


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"你好 {name}，欢迎使用企业知识库！"}
