# 办公自动化执行器（rpa-agent）—— 用浏览器自动化把固定流程做掉
#
# 定位：给"人坐在旁边盯着"的半自动工具（登录要过验证码，所以不做无人值守）
# 形态：单元（= 一条业务数据 × 一个操作环节）+ 操作台验证，一个个叠加
# 安全前提：所有执行都是确定性脚本；写生产系统前先做最小验证、并取得业务与 IT 授权

from fastapi import FastAPI

from api import browser_api, health, runs, shots, stats, unit_api

# 数据库相关：导入表模型 → 建表
from core.database import Base, engine
from models.run import Run, RunStep, UnitMeta   # noqa: F401  （导入才会被 create_all 认到）
from services import run_service

Base.metadata.create_all(bind=engine)

# 服务启动先收拾上次的残局：把遗留的排队中/执行中运行标成"被打断"
# 为什么：进程重启后那些运行已经没有执行线程了，留在"执行中"会让界面永远转圈
_stale = run_service.interrupt_stale_runs()
if _stale:
    print(f"启动清理：{_stale} 条残留运行已标记为被打断")

app = FastAPI(title="办公自动化执行器 rpa-agent", version="0.1.0")

app.include_router(health.router)
app.include_router(browser_api.router)
app.include_router(unit_api.router)
app.include_router(runs.router)
app.include_router(shots.router)
app.include_router(stats.router)


@app.get("/")
def root():
    return {"message": "办公自动化执行器 启动成功！"}
