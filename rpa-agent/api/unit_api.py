# 单元接口 —— 列出所有单元、给某个单元投一次运行、人工标记"已验证"
# 运行是异步的：这里建好运行记录、把任务投进浏览器队列就立刻返回 run_id，
# 前端拿 run_id 去轮询进度（这就是项目 README 里写的"任务队列"的正解形状：
# 入库返回 job id + 前端轮询，而不是让请求干等到天荒地老、逼用户调大超时）

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc

from core.browser import BrowserBusy, worker
from core.database import SessionLocal
from core.registry import load_units
from models.run import Run, UnitMeta
from services import run_service, unit_runner

router = APIRouter(prefix="/api/v1/units", tags=["单元"])


def _latest_runs(db) -> dict[str, Run]:
    """每个单元最近一次运行（给清单里的"最近结果"用）"""
    latest = {}
    for run in db.query(Run).order_by(desc(Run.id)).all():
        latest.setdefault(run.unit_key, run)
    return latest


def _verified_map(db) -> dict[str, UnitMeta]:
    return {m.unit_key: m for m in db.query(UnitMeta).all()}


def _run_brief(run: Run | None) -> dict | None:
    if not run:
        return None
    return {
        "id": run.id, "status": run.status, "current_step": run.current_step,
        "error_step": run.error_step, "error_msg": run.error_msg,
        "created_at": run.created_at.strftime("%m-%d %H:%M:%S") if run.created_at else None,
    }


@router.get("")
def list_units():
    """单元清单：声明 + 人工验证状态 + 最近一次运行结果"""
    db = SessionLocal()
    try:
        latest, verified = _latest_runs(db), _verified_map(db)
        data = []
        for unit in sorted(load_units().values(), key=lambda u: u.order):
            meta = verified.get(unit.key)
            item = unit.to_dict(
                verified=bool(meta and meta.verified),
                last_run=_run_brief(latest.get(unit.key)),
            )
            item["note"] = meta.note if meta else None
            data.append(item)
        return {"message": "ok", "data": data}
    finally:
        db.close()


class RunRequest(BaseModel):
    inputs: dict = {}          # 这次运行的输入（操作台上的 JSON 文本框内容）


def _validate_inputs(unit, inputs: dict) -> list[str]:
    """必填字段校验：缺什么直接列出来，别让脚本跑到一半才报错"""
    missing = []
    for field in unit.inputs:
        if not field.get("required"):
            continue
        value = inputs.get(field["key"])
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field.get("label") or field["key"])
    return missing


@router.post("/{key}/run")
def run_unit(key: str, req: RunRequest):
    """投一次运行：校验输入 → 建运行记录 → 投进浏览器队列 → 立刻返回 run_id"""
    unit = load_units().get(key)
    if not unit:
        raise HTTPException(status_code=404, detail=f"单元不存在：{key}")

    missing = _validate_inputs(unit, req.inputs)
    if missing:
        raise HTTPException(status_code=400, detail="缺少必填输入：" + "、".join(missing))

    if worker.status()["busy"]:
        raise HTTPException(status_code=409, detail="执行器正忙（上一个任务还在跑），先等它结束")

    run_id = run_service.create_run(unit.key, unit.steps, req.inputs)
    cancel_event = unit_runner.new_cancel_event(run_id)

    try:
        # 任务体在浏览器线程里执行；里面自带"浏览器起不来也要给这次运行落个结论"的兜底
        worker.submit(f"运行单元 {unit.cn_name}",
                      lambda: unit_runner.run_job(unit, run_id, req.inputs, cancel_event),
                      wait=False)
    except BrowserBusy as e:
        # 排队被拒：把刚建的记录标掉，别留一条永远"排队中"的僵尸
        run_service.finish_run(run_id, "canceled", error_msg=str(e))
        raise HTTPException(status_code=409, detail=str(e))

    return {"message": "已开始执行", "data": {"run_id": run_id}}


@router.get("/{key}/runs")
def unit_runs(key: str, limit: int = 10):
    """这个单元最近的运行记录（操作台上的历史列表）"""
    if key not in load_units():
        raise HTTPException(status_code=404, detail=f"单元不存在：{key}")
    db = SessionLocal()
    try:
        runs = (db.query(Run).filter(Run.unit_key == key)
                .order_by(desc(Run.id)).limit(limit).all())
        return {"message": "ok", "data": [_run_brief(r) for r in runs]}
    finally:
        db.close()


class VerifyRequest(BaseModel):
    verified: bool = True
    note: str | None = None


@router.post("/{key}/verify")
def verify_unit(key: str, req: VerifyRequest):
    """
    人工标记"这个单元真跑通了"
    为什么要有这一步：系统只能判定"脚本没报错"；生成的供应商对不对、字段有没有填错位，
    得人打开金蝶核对过才算数——所以状态是"系统断言 + 人工确认"双判定
    """
    if key not in load_units():
        raise HTTPException(status_code=404, detail=f"单元不存在：{key}")
    db = SessionLocal()
    try:
        meta = db.get(UnitMeta, key)
        if not meta:
            meta = UnitMeta(unit_key=key)
            db.add(meta)
        meta.verified = 1 if req.verified else 0
        meta.note = req.note
        db.commit()
        return {"message": "已标记" if req.verified else "已取消标记", "data": {"key": key, "verified": req.verified}}
    finally:
        db.close()
