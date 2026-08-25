# 智能问答（Agent）—— 统一问答入口
# 用户只问问题，不问"资料在哪个模块"
# 检索范围：制度 + 文档 + 流程模板（全部知识）
# 两个端点：/chat 一次性返回全文；/chat/stream 用 SSE 逐段返回（打字机效果）

import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import SessionLocal
from models.message import Message
from models.vector import KnowledgeVector
from services.llm_service import is_configured as llm_is_configured, chat_with_history, stream_chat
from services.embedding_service import (
    is_configured as embed_is_configured,
    retrieve_top_k,
)

router = APIRouter(prefix="/api/v1/agent", tags=["智能问答"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None   # 不传则开启新会话


def prepare_answer(req: ChatRequest, db: Session) -> dict:
    """两个端点共用的准备步骤：会话 → 历史 → 检索 → 组装上下文和来源列表"""
    # 生成/沿用会话ID
    session_id = req.session_id or f"session-{uuid.uuid4().hex[:12]}"

    # 第零步：加载历史
    history = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(10)
        .all()
    )

    # 第一步：检索
    # 检索词 = 当前问题 + 上一轮用户问题（支持指代）
    search_text = req.question
    last_user_msgs = [m for m in history if m.role == "user"]
    if last_user_msgs:
        search_text = f"{req.question} {last_user_msgs[-1].content}"

    if embed_is_configured() and db.query(KnowledgeVector).count() > 0:
        matched = retrieve_top_k(db, search_text, k=3)
        retrieval_method = "embedding"
    else:
        matched = []
        retrieval_method = "none"

    # 第二步：组装上下文（标明每条资料的类型，LLM 才能区分"制度""文档""流程"来组织回答）
    type_labels = {"policy": "制度", "document": "文档", "workflow": "流程模板"}
    context_parts = []
    for m in matched:
        label = type_labels.get(m["type"], "资料")
        context_parts.append(f"【{label}：{m['title']}】{m['content']}")
    context = "\n\n".join(context_parts)

    # 同一条知识可能命中多个块，sources 按 (type, id) 去重，避免来源列表重复
    seen = set()
    sources = []
    for m in matched:
        key = (m["type"], m["id"])
        if key not in seen:
            seen.add(key)
            sources.append({"type": m["type"], "id": m["id"], "title": m["title"]})

    return {
        "session_id": session_id,
        "context": context,
        "sources": sources,
        "retrieval_method": retrieval_method,
        "history_dicts": [{"role": m.role, "content": m.content} for m in history],
    }


def plan_answer(p: dict) -> tuple[str | None, str]:
    """
    决定怎么回答：返回 (上下文, 固定答案)
    - 上下文不是 None → 调 LLM（第二个返回值忽略）
    - 上下文是 None → 不调 LLM，直接用固定答案
    """
    if not llm_is_configured():
        return None, "未配置大模型，请在 .env 中填写 LLM 配置。"
    if p["context"]:
        return p["context"], ""
    if p["history_dicts"]:
        return "（知识库中未检索到相关资料，请根据对话历史回答，不要编造知识库内容）", ""
    return None, "知识库中未检索到相关内容，请换个问法试试。"


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """统一问答：一次提问，全局检索，LLM 作答（一次性返回全文）"""
    p = prepare_answer(req, db)

    context, fixed = plan_answer(p)
    if context is None:
        answer = fixed
        answer_source = "LLM" if llm_is_configured() else "none"
    else:
        answer = chat_with_history(req.question, context, p["history_dicts"])
        answer_source = "LLM"

    # 保存这轮对话
    db.add(Message(session_id=p["session_id"], role="user", content=req.question))
    db.add(Message(session_id=p["session_id"], role="assistant", content=answer))
    db.commit()

    return {
        "question": req.question,
        "answer": answer,
        "answer_source": answer_source,
        "retrieval_method": p["retrieval_method"],
        "sources": p["sources"],
        "session_id": p["session_id"],
    }


def sse_event(event: str, data: dict) -> str:
    """拼一条 SSE 消息：event 行 + data 行 + 空行结尾（SSE 协议用空行分隔消息）"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    """
    统一问答（流式版）：SSE 逐段返回回答
    事件：meta（来源/会话信息）→ delta（回答增量，多次）→ done（结束）
    """
    p = prepare_answer(req, db)

    def generate():
        # 生成器在 StreamingResponse 响应阶段才执行，此时请求级 db 会话已关闭，
        # 所以保存消息要在这里自开会话
        sdb = SessionLocal()
        try:
            sdb.add(Message(session_id=p["session_id"], role="user", content=req.question))
            sdb.commit()

            yield sse_event("meta", {
                "retrieval_method": p["retrieval_method"],
                "sources": p["sources"],
                "session_id": p["session_id"],
            })

            context, fixed = plan_answer(p)
            if context is None:
                answer = fixed
                yield sse_event("delta", {"text": answer})
                yield sse_event("done", {"answer_source": "LLM" if llm_is_configured() else "none"})
            else:
                answer = ""
                for delta in stream_chat(req.question, context, p["history_dicts"]):
                    answer += delta
                    yield sse_event("delta", {"text": delta})
                yield sse_event("done", {"answer_source": "LLM"})

            sdb.add(Message(session_id=p["session_id"], role="assistant", content=answer))
            sdb.commit()
        except Exception as e:
            # LLM 流中途出错：告诉前端失败原因，这轮不保存回答
            yield sse_event("error", {"message": f"回答生成失败：{e}"})
        finally:
            sdb.close()

    return StreamingResponse(generate(), media_type="text/event-stream")
