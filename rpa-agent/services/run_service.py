# 运行记录服务 —— 一次运行从"排队"到"结束"的全过程留痕
# 为什么要这些留痕：RPA 执行的是真实业务操作，出了问题必须能回答
#   "跑到哪一步了""当时页面长什么样""是什么错"——日志 + 每步截图 + 数据库状态，三样都要有

import json
import threading
from datetime import datetime

from core.config import LOGS_DIR, RUNS_DIR
from core.database import SessionLocal
from models.run import Run, RunStep

# 写日志文件用的小锁：浏览器线程与请求线程都可能追加，避免两行交错
_log_lock = threading.Lock()


def _log_path(run_id: int):
    return LOGS_DIR / f"run_{run_id}.log"


def append_log(run_id: int, line: str) -> None:
    """追加一行运行日志（带时间戳）"""
    stamp = datetime.now().strftime("%H:%M:%S")
    with _log_lock:
        with open(_log_path(run_id), "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {line}\n")


def read_log_tail(run_id: int, lines: int = 60) -> list[str]:
    """读日志末尾若干行（前端轮询展示用）"""
    path = _log_path(run_id)
    if not path.exists():
        return []
    with open(path, encoding="utf-8", errors="ignore") as f:
        return [ln.rstrip("\n") for ln in f.readlines()[-lines:]]


def create_run(unit_key: str, steps: list[dict], inputs: dict) -> int:
    """
    新建一次运行：run 行 + 每个步骤的 pending 行一次性建好
    为什么步骤先建：前端拿到 run 就能渲染完整步骤列表（未开始的显示灰色），而不是逐步冒出来
    """
    db = SessionLocal()
    try:
        run = Run(
            unit_key=unit_key,
            input_json=json.dumps(inputs, ensure_ascii=False),
            status="queued",
            artifact_dir=str((RUNS_DIR / "0").relative_to(RUNS_DIR.parent.parent)),  # 先占位，拿到 id 后再改
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        run.artifact_dir = str((RUNS_DIR / str(run.id)).relative_to(RUNS_DIR.parent.parent))
        (RUNS_DIR / str(run.id)).mkdir(parents=True, exist_ok=True)

        for idx, s in enumerate(steps):
            db.add(RunStep(run_id=run.id, idx=idx, step_key=s["key"], cn_name=s["cn_name"]))

        db.commit()
        append_log(run.id, f"运行已创建：单元 {unit_key}，共 {len(steps)} 步")
        return run.id
    finally:
        db.close()


def mark_running(run_id: int) -> None:
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        run.status = "running"
        run.started_at = datetime.now()
        db.commit()
    finally:
        db.close()
    append_log(run_id, "开始执行")


def step_started(run_id: int, idx: int, cn_name: str) -> None:
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        run.current_step = idx
        step = db.query(RunStep).filter_by(run_id=run_id, idx=idx).first()
        if step:
            step.status = "running"
            step.started_at = datetime.now()
        db.commit()
    finally:
        db.close()
    append_log(run_id, f"▶ 第 {idx + 1} 步：{cn_name}")


def step_finished(run_id: int, idx: int, status: str, duration_ms: int,
                  screenshot: str | None = None, error: str | None = None) -> None:
    db = SessionLocal()
    try:
        step = db.query(RunStep).filter_by(run_id=run_id, idx=idx).first()
        if step:
            step.status = status
            step.finished_at = datetime.now()
            step.duration_ms = duration_ms
            if screenshot:
                step.screenshot = screenshot
            if error:
                step.error = error
        db.commit()
    finally:
        db.close()
    mark = {"success": "✔", "failed": "✘", "skipped": "—"}.get(status, "·")
    append_log(run_id, f"{mark} 第 {idx + 1} 步 {status}（{duration_ms} ms）"
                       + (f"：{error}" if error else ""))


def finish_run(run_id: int, status: str, error_step: int | None = None,
               error_msg: str | None = None) -> None:
    """结束一次运行；失败时把还没跑的步骤标成 skipped，让界面一眼看出停在哪"""
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        run.status = status
        run.finished_at = datetime.now()
        if error_step is not None:
            run.error_step = error_step
        if error_msg:
            run.error_msg = error_msg
        if status in ("failed", "canceled", "interrupted"):
            db.query(RunStep).filter(
                RunStep.run_id == run_id, RunStep.status == "pending"
            ).update({"status": "skipped"})
        db.commit()
    finally:
        db.close()
    append_log(run_id, f"运行结束：{status}" + (f"（{error_msg}）" if error_msg else ""))


def interrupt_stale_runs() -> int:
    """
    服务启动时调用：把上次遗留的 queued/running 运行标成 interrupted
    为什么：进程重启后那些运行已经没了执行线程，留在 running 会让界面永远转圈
    """
    db = SessionLocal()
    try:
        stale = db.query(Run).filter(Run.status.in_(["queued", "running"])).all()
        for run in stale:
            run.status = "interrupted"
            run.finished_at = datetime.now()
            db.query(RunStep).filter(
                RunStep.run_id == run.id, RunStep.status.in_(["pending", "running"])
            ).update({"status": "skipped"})
        db.commit()
        return len(stale)
    finally:
        db.close()
