from fastapi import FastAPI

from api.chat import router as chat_router
from api.admin import router as admin_router
from core.config import KB_AGENT_URL
from core.database import Base, engine
from models.call import Call  # noqa: F401  导入模型才会注册到 Base.metadata（create_all 建表依据）

app = FastAPI(title="企业AI助手", version="0.2.0")

# 启动时自动建表：create_all 扫描所有继承 Base 的模型类，表已存在则跳过
Base.metadata.create_all(bind=engine)

app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "企业AI助手 启动成功！"}


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"你好 {name}，欢迎使用企业AI助手！"}


@app.get("/api/status")
def status():
    """简单健康检查：看自己和 kb-agent 的配置状态（联调时有用）"""
    return {
        "service": "ai-assistant",
        "kb_agent_url": KB_AGENT_URL,
    }
