# 运行记录接口 —— 前端轮询进度、看步骤与日志、取消、取截图
# 进度不给百分比：各步耗时差异太大（有的 200 毫秒、有的要等页面），百分比会撒谎，
# 用"步骤列表 + 当前第几步"表达进度才是诚实的

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import desc

from core.config import RUNS_DIR
from core.database import SessionLocal
from models.run import Run, RunStep
from services import run_service, unit_runner

router = APIRouter(prefix="/api/v1/runs", tags=["运行记录"])


def _run_detail(db, run: Run) -> dict:
    steps = (db.query(RunStep).filter(RunStep.run_id == run.id)
             .order_by(RunStep.idx).all())
    try:
        inputs = json.loads(run.input_json or "{}")
    except Exception:
        inputs = {}
    return {
        "id": run.id,
        "unit_key": run.unit_key,
        "status": run.status,
        "current_step": run.current_step,
        "error_step": run.error_step,
        "error_msg": run.error_msg,
        "inputs": inputs,
        "created_at": run.created_at.strftime("%Y-%m-%d %H:%M:%S") if run.created_at else None,
        "started_at": run.started_at.strftime("%H:%M:%S") if run.started_at else None,
        "finished_at": run.finished_at.strftime("%H:%M:%S") if run.finished_at else None,
        "steps": [
            {
                "idx": s.idx, "step_key": s.step_key, "cn_name": s.cn_name,
                "status": s.status, "duration_ms": s.duration_ms,
                "screenshot": s.screenshot, "error": s.error,
            }
            for s in steps
        ],
        "logs": run_service.read_log_tail(run.id, 80),
    }


@router.get("")
def recent_runs(limit: int = 20, unit_key: str = ""):
    """最近的运行记录（不传 unit_key 就是全部单元）"""
    db = SessionLocal()
    try:
        q = db.query(Run)
        if unit_key:
            q = q.filter(Run.unit_key == unit_key)
        runs = q.order_by(desc(Run.id)).limit(limit).all()
        return {"message": "ok", "data": [
            {"id": r.id, "unit_key": r.unit_key, "status": r.status,
             "created_at": r.created_at.strftime("%m-%d %H:%M:%S") if r.created_at else None}
            for r in runs
        ]}
    finally:
        db.close()


@router.get("/{run_id}")
def run_detail(run_id: int):
    """一次运行的完整情况：状态 + 每步状态与耗时 + 最近日志"""
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"运行记录不存在：{run_id}")
        return {"message": "ok", "data": _run_detail(db, run)}
    finally:
        db.close()


@router.post("/{run_id}/cancel")
def cancel(run_id: int):
    """
    取消一次运行：只置一个"取消开关"，由单元在步骤之间自己检查退出
    为什么不硬杀：页面操作做到一半被强断，可能留下半填的表单；
    协作式退出保证每次都停在一个完整步骤的边界上
    """
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"运行记录不存在：{run_id}")
        if run.status not in ("queued", "running"):
            return {"message": f"这次运行已经结束（{run.status}），无需取消", "data": {"id": run_id}}
    finally:
        db.close()

    ok = unit_runner.cancel_run(run_id)
    if not ok:
        # 内存里没有取消开关：说明任务是这次服务重启之前投的（已被标 interrupted）
        return {"message": "这次运行不在执行中", "data": {"id": run_id}}
    return {"message": "已请求取消（会在当前步骤结束后停下）", "data": {"id": run_id}}


@router.get("/{run_id}/shots/{filename}")
def run_shot(run_id: int, filename: str):
    """取某次运行的截图（失败现场、单元主动截的图都走这里）"""
    # 防目录穿越：只允许取文件名字（去掉任何路径成分）
    safe = filename.replace("\\", "/").split("/")[-1]
    path = RUNS_DIR / str(run_id) / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="截图不存在")
    return FileResponse(path)
