from fastapi import FastAPI

from core.database import Base, engine
from models.reading import Reading  # noqa: F401  导入模型才会注册到 Base.metadata（create_all 建表依据）

app = FastAPI(title="研读助手", version="0.1.0")

# 启动时自动建表：create_all 扫描所有继承 Base 的模型类，表已存在则跳过
Base.metadata.create_all(bind=engine)

# 研读记录接口（api/readings.py）留到"构建后端"阶段再补——前端目前走静态数据（frontend/src/api/readings.js）


@app.get("/")
def root():
    return {"message": "研读助手 启动成功！"}


@app.get("/api/status")
def status():
    return {"service": "study-agent"}
