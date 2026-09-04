# 管理端接口 —— 管理界面（admin-frontend）的数据来源
# 设计（README 已确认）：
#   1. 调用统计：来自本服务的 calls 表（每次问答调用记一笔，只有调度器有全链路视角）
#   2. Agent 数据：代理模式 —— 前端只调本服务，由本服务转发到各 Agent 的管理接口
#      （kb-agent 的 knowledge/missed 已现成），前端不直连 Agent，与问答链路同一模式

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config import KB_AGENT_URL
from core.database import SessionLocal
from models.call import Call
from services import registry

router = APIRouter(prefix="/api/v1/admin", tags=["管理端"])

# 全部 Agent 的清单（含规划中的）：总览页展示用
# 新 Agent 上线时在这里补一条，并把状态探测接到 registry
AGENTS = [
    {"key": "knowledge", "name": "kb-agent", "duty": "企业知识问答"},
    {"key": "doc-review", "name": "doc-review-agent", "duty": "企业项目文档审查"},
    {"key": "data-analysis", "name": "data-analysis-agent", "duty": "企业数据分析"},
    {"key": "notice", "name": "notice-agent", "duty": "企业通知助手"},
]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def call_to_dict(c: Call) -> dict:
    return {
        "id": c.id,
        "question": c.question,
        "intent_agent": c.intent_agent,
        "answer_source": c.answer_source,
        "degraded": c.degraded,
        "duration_ms": c.duration_ms,
        "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def kb_unavailable() -> HTTPException:
    """kb-agent 没启动/超时时的统一报错（前端 catch 后提示）"""
    return HTTPException(status_code=502, detail="kb-agent 服务不可用（未启动或超时）")


# ---- 总览 ----

@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    """总览：各 Agent 在线状态 + 调用统计"""
    agents = []
    for a in AGENTS:
        if a["key"] == "knowledge":
            status = "online" if registry.is_available(a["key"]) else "offline"
        else:
            status = "planning"   # 未上线的 Agent
        agents.append({"name": a["name"], "duty": a["duty"], "status": status})

    total_calls = db.query(Call).count()
    knowledge_calls = db.query(Call).filter(Call.intent_agent == "knowledge").count()
    success_calls = db.query(Call).filter(Call.answer_source == "knowledge").count()
    degraded_calls = db.query(Call).filter(Call.degraded.is_(True)).count()
    avg_ms = db.query(func.avg(Call.duration_ms)).scalar()

    return {
        "agents": agents,
        "stats": {
            "total_calls": total_calls,
            "knowledge_calls": knowledge_calls,
            "success_calls": success_calls,
            "degraded_calls": degraded_calls,
            "avg_duration_ms": round(avg_ms or 0, 1),
        },
    }


# ---- 调用记录 ----

@router.get("/calls")
def list_calls(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    """最近调用记录（最新的在前）"""
    items = db.query(Call).order_by(Call.id.desc()).limit(limit).all()
    return {"total": db.query(Call).count(), "data": [call_to_dict(c) for c in items]}


# ---- kb-agent 代理（前端 → 本服务 → kb-agent）----

@router.get("/kb/knowledge")
def kb_list_knowledge(
    keyword: str = Query(default=""),
    category: str = Query(default=""),
    kind: str = Query(default=""),
):
    """转发：知识列表"""
    try:
        r = httpx.get(
            f"{KB_AGENT_URL}/api/v1/knowledge/list",
            params={"keyword": keyword, "category": category, "kind": kind},
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        raise kb_unavailable()


@router.delete("/kb/knowledge/{item_id}")
def kb_delete_knowledge(item_id: int):
    """转发：删除知识（向量索引由 kb-agent 一并清理）"""
    try:
        r = httpx.delete(f"{KB_AGENT_URL}/api/v1/knowledge/{item_id}", timeout=30.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        raise kb_unavailable()


@router.post("/kb/upload")
async def kb_upload(
    file: UploadFile = File(...),
    kind: str | None = Form(default=None),
    category: str | None = Form(default=None),
):
    """转发：上传文件（multipart 原样透传，表单值原样带上）"""
    data = {}
    if kind:
        data["kind"] = kind
    if category:
        data["category"] = category
    try:
        r = httpx.post(
            f"{KB_AGENT_URL}/api/v1/knowledge/upload",
            files={"file": (file.filename, await file.read(), file.content_type)},
            data=data,
            timeout=120.0,   # 上传含 LLM 分类 + 向量化，放宽超时
        )
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        raise kb_unavailable()


@router.get("/kb/missed")
def kb_list_missed(limit: int = Query(default=100, ge=1, le=500)):
    """转发：未命中问题清单（按被问次数排序）"""
    try:
        r = httpx.get(f"{KB_AGENT_URL}/api/v1/missed", params={"limit": limit}, timeout=30.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        raise kb_unavailable()


@router.delete("/kb/missed")
def kb_clear_missed():
    """转发：清空全部未命中记录"""
    try:
        r = httpx.delete(f"{KB_AGENT_URL}/api/v1/missed", timeout=30.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        raise kb_unavailable()


@router.delete("/kb/missed/{missed_id}")
def kb_delete_missed(missed_id: int):
    """转发：删除一条未命中记录（对应知识已补充后）"""
    try:
        r = httpx.delete(f"{KB_AGENT_URL}/api/v1/missed/{missed_id}", timeout=30.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        raise kb_unavailable()
