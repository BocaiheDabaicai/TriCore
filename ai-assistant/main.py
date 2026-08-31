from fastapi import FastAPI

from api.chat import router as chat_router
from core.config import KB_AGENT_URL

app = FastAPI(title="企业AI助手", version="0.1.0")

app.include_router(chat_router)


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
