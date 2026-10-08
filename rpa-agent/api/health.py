# 探活接口 —— manager 每 5 秒来敲一次，2 秒超时
# 所以这里只读内存快照，绝不碰浏览器、不做慢查询：
# 探活被拖慢一次，服务就会被判死重启（kb-agent 踩过这个坑）

from fastapi import APIRouter

from core.browser import worker
from core.database import SessionLocal
from models.run import Run

router = APIRouter(tags=["探活"])


@router.get("/api/health")
def health():
    db = SessionLocal()
    try:
        running = db.query(Run).filter(Run.status.in_(["queued", "running"])).first()
        run_info = {"id": running.id, "unit_key": running.unit_key, "status": running.status} if running else None
    finally:
        db.close()

    st = worker.status()
    return {
        "status": "ok",
        "browser": {
            "launched": st["launched"],
            "busy": st["busy"],
            "current_job": st["current_job"],
            "heartbeat_ago": st["heartbeat_ago"],
            "profile_locked": st["profile_locked"],
            "last_error": st["last_error"],
        },
        "run": run_info,
    }
