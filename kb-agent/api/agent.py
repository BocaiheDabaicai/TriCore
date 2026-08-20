# 智能问答（Agent）—— 统一问答入口
# 用户只问问题，不问"资料在哪个模块"
# 检索范围：制度 + 文档 + 流程模板（全部知识）

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import SessionLocal
from models.message import Message
from models.vector import KnowledgeVector
from services.llm_service import is_configured as llm_is_configured, chat_with_context, chat_with_history
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


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """统一问答：一次提问，全局检索，LLM 作答"""
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

    if not matched:
        # 无检索能力或无索引时，让 LLM 基于历史直接回答（没有资料就不编造）
        context = ""
        matched = []

    # 第二步+第三步：组装上下文 → LLM 生成
    # 上下文里标明每条资料的类型，LLM 才能区分"制度""文档""流程"来组织回答
    type_labels = {"policy": "制度", "document": "文档", "workflow": "流程模板"}
    context_parts = []
    for m in matched:
        label = type_labels.get(m["type"], "资料")
        context_parts.append(f"【{label}：{m['title']}】{m['content']}")
    context = "\n\n".join(context_parts)

    history_dicts = [{"role": m.role, "content": m.content} for m in history]

    if llm_is_configured():
        if context:
            if history_dicts:
                answer = chat_with_history(req.question, context, history_dicts)
            else:
                answer = chat_with_context(req.question, context)
        else:
            # 没有检索到资料：直接对话（模型会凭自己的知识回答或说不知道）
            if history_dicts:
                answer = chat_with_history(req.question, "（知识库中未检索到相关资料，请根据对话历史回答，不要编造知识库内容）", history_dicts)
            else:
                answer = "知识库中未检索到相关内容，请换个问法试试。"
        answer_source = "LLM"
    else:
        answer = "未配置大模型，请在 .env 中填写 LLM 配置。"
        answer_source = "none"

    # 保存这轮对话
    db.add(Message(session_id=session_id, role="user", content=req.question))
    db.add(Message(session_id=session_id, role="assistant", content=answer))
    db.commit()

    # 同一条知识可能命中多个块，sources 按 (type, id) 去重，避免来源列表重复
    seen = set()
    sources = []
    for m in matched:
        key = (m["type"], m["id"])
        if key not in seen:
            seen.add(key)
            sources.append({"type": m["type"], "id": m["id"], "title": m["title"]})

    return {
        "question": req.question,
        "answer": answer,
        "answer_source": answer_source,
        "retrieval_method": retrieval_method,
        "sources": sources,
        "session_id": session_id,
    }
