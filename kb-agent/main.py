from fastapi import FastAPI

from api.policy import router as policy_router
from api.myapi import router as myapi_router
from api.document import router as document_router
from api.workflow import router as workflow_router
from api.agent import router as agent_router

# 数据库相关
from core.database import engine, Base
from models.policy import Policy
from models.document import Document
from models.workflow import WorkflowTemplate, WorkflowStep
from models.message import Message
from models.vector import KnowledgeVector

app = FastAPI(title="企业知识库Agent", version="0.1.0")

# 在应用启动时自动建表
# Base.metadata.create_all 会扫描所有继承 Base 的类，对应生成数据库表
# 如果表已经存在就跳过（不会重复创建）
Base.metadata.create_all(bind=engine)

app.include_router(policy_router)
app.include_router(myapi_router)
app.include_router(document_router)
app.include_router(workflow_router)
app.include_router(agent_router)


@app.get("/")
def root():
    return {"message": "企业知识库Agent 启动成功！"}


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"你好 {name}，欢迎使用企业知识库！"}
