"""manager 服务（8002）：统一管理各 Agent 服务的启动、停止、状态与日志"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from process_manager import ProcessManager

manager = ProcessManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：拉起所有 auto_start 服务，再开监控线程
    manager.start_all()
    manager.start_monitor()
    yield
    # 关闭：停掉所有被管服务，避免留孤儿进程占端口
    manager.shutdown()


app = FastAPI(title="服务管理 manager", lifespan=lifespan)

def _require_service(name: str):
    # 判断这个服务存不存在
    if name not in manager.services:
        raise HTTPException(status_code=404, detail=f"服务不存在：{name}")


@app.get("/api/v1/services")
def list_services():
    return {"services": manager.status_all()}


@app.post("/api/v1/services/start-all")
def start_all():
    return {"services": manager.start_all()}


@app.post("/api/v1/services/stop-all")
def stop_all():
    return {"services": manager.stop_all()}


@app.post("/api/v1/services/{name}/start")
def start_service(name: str):
    _require_service(name)
    result = manager.start(name)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=f"{name} 启动失败，请查看日志")
    return result


@app.post("/api/v1/services/{name}/stop")
def stop_service(name: str):
    _require_service(name)
    return manager.stop(name)


@app.post("/api/v1/services/{name}/restart")
def restart_service(name: str):
    _require_service(name)
    result = manager.restart(name)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=f"{name} 重启失败，请查看日志")
    return result


@app.get("/api/v1/services/{name}/logs")
def get_logs(name: str, lines: int = 100):
    _require_service(name)
    return manager.logs(name, lines)
