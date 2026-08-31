# 智能问答（Agent）—— 统一问答入口
# 用户只问问题，不问"资料在哪个模块"
# 检索范围：制度 + 文档 + 流程模板（全部知识）
# 两个端点：/chat 一次性返回全文；/chat/stream 用 SSE 逐段返回（打字机效果）
# 宽度/深度分流：
#   宽度（breadth，列举/概览类）→ 查表列"标题+关键词"清单
#   深度（depth，具体细节类）→ 向量检索 top3 分块（原有逻辑）

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import SessionLocal
from models.knowledge import Knowledge
from models.message import Message
from models.vector import KnowledgeVector
from models.missed import MissedQuestion
from services.llm_service import (
    is_configured as llm_is_configured,
    chat_with_history,
    stream_chat,
    classify_dimension,
)
from services.embedding_service import (
    is_configured as embed_is_configured,
    retrieve_top_k,
)

router = APIRouter(prefix="/api/v1/agent", tags=["智能问答"])

type_labels = {"policy": "制度", "document": "文档", "workflow": "流程模板"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None   # 不传则开启新会话


# 未命中判定短语：深度回答的 prompt 要求"资料不足时只回复这句话"，
# 回答里出现这些短语就认为这轮问题知识库没覆盖，记录下来
# 为什么用短语判断而不是分数判断：实测 bge-m3 分数区分度不足，
# 未命中的问题分数（0.64）可能比弱命中的（0.53）还高，分数不可靠，LLM 的诚实回答才可靠
MISS_PHRASES = ("暂无相关内容", "没有相关内容", "未检索到相关")


def is_miss_reply(answer: str) -> bool:
    """回答里是否包含"知识库没覆盖"的诚实短语"""
    return any(p in answer for p in MISS_PHRASES)


def record_missed(db: Session, question: str) -> None:
    """未命中问题入库：同一问题重复问只累计次数——次数越高越该优先补充"""
    row = db.query(MissedQuestion).filter(MissedQuestion.question == question).first()
    if row:
        row.count += 1
        row.last_at = datetime.now()
    else:
        db.add(MissedQuestion(question=question[:500]))
    db.commit()


def prepare_breadth(db: Session) -> tuple[str, list]:
    """
    宽度查询的上下文：不走向量检索，直接查表拿全部知识
    按 category 分组列"标题【类型】(关键词)"——关键词是目录索引，用户点名后走深度
    """
    items = db.query(Knowledge).order_by(Knowledge.category, Knowledge.id).all()

    by_cat: dict[str, list] = {}
    for it in items:
        by_cat.setdefault(it.category or "未分类", []).append(it)

    parts = []
    for cat, its in by_cat.items():
        lines = []
        for it in its:
            line = f"- {it.title}【{type_labels.get(it.kind, '资料')}】"
            if it.keywords:
                line += f"（{it.keywords}）"
            lines.append(line)
        parts.append(f"【{cat}】\n" + "\n".join(lines))

    sources = [{"type": it.kind, "id": it.id, "title": it.title} for it in items]
    return "\n\n".join(parts), sources


def prepare_answer(req: ChatRequest, db: Session) -> dict:
    """两个端点共用的准备步骤：会话 → 历史 → 维度判断 → 检索/列表 → 组装上下文和来源"""
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

    # 检索词 = 当前问题 + 上一轮用户问题（支持指代）
    search_text = req.question
    last_user_msgs = [m for m in history if m.role == "user"]
    if last_user_msgs:
        search_text = f"{req.question} {last_user_msgs[-1].content}"

    # 第一步：维度判断（纯 AI 判断 → 失败降级 depth）
    # 不写固定词表、不给条目名单——自然语言千变万化（名称不全、意思相近），
    # 只给 AI 当前问题 + 上一轮问题（理解指代），让它按语义自行判断
    prev_question = last_user_msgs[-1].content if last_user_msgs else None
    dimension = classify_dimension(req.question, prev_question) if llm_is_configured() else "depth"

    # 第二步：按维度准备上下文
    if dimension == "breadth":
        context, sources = prepare_breadth(db)
        retrieval_method = "list"
    elif embed_is_configured() and db.query(KnowledgeVector).count() > 0:
        matched = retrieve_top_k(db, search_text)
        retrieval_method = "embedding"
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

        # 深度检索零命中（全部低于分数阈值）→ 记录未命中问题（知识库建设的输入）
        if not matched and llm_is_configured():
            record_missed(db, req.question)
    else:
        context, sources = "", []
        retrieval_method = "none"

    return {
        "session_id": session_id,
        "context": context,
        "sources": sources,
        "retrieval_method": retrieval_method,
        "dimension": dimension,
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
    return None, "知识库中暂无相关内容，该问题已记录，我们会尽快补充相关资料。"


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """统一问答：一次提问，全局检索，LLM 作答（一次性返回全文）"""
    p = prepare_answer(req, db)

    context, fixed = plan_answer(p)
    if context is None:
        answer = fixed
        answer_source = "LLM" if llm_is_configured() else "none"
    else:
        answer = chat_with_history(req.question, context, p["history_dicts"], mode=p["dimension"])
        answer_source = "LLM"
        # LLM 诚实回复"暂无相关内容"→ 这轮问题知识库没覆盖，记录下来
        if is_miss_reply(answer):
            record_missed(db, req.question)

    # 保存这轮对话
    db.add(Message(session_id=p["session_id"], role="user", content=req.question))
    db.add(Message(session_id=p["session_id"], role="assistant", content=answer))
    db.commit()

    return {
        "question": req.question,
        "answer": answer,
        "answer_source": answer_source,
        "retrieval_method": p["retrieval_method"],
        "dimension": p["dimension"],
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
                "dimension": p["dimension"],
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
                for delta in stream_chat(req.question, context, p["history_dicts"], mode=p["dimension"]):
                    answer += delta
                    yield sse_event("delta", {"text": delta})
                if is_miss_reply(answer):
                    record_missed(sdb, req.question)
                yield sse_event("done", {"answer_source": "LLM"})

            sdb.add(Message(session_id=p["session_id"], role="assistant", content=answer))
            sdb.commit()
        except Exception as e:
            # LLM 流中途出错：告诉前端失败原因，这轮不保存回答
            yield sse_event("error", {"message": f"回答生成失败：{e}"})
        finally:
            sdb.close()

    return StreamingResponse(generate(), media_type="text/event-stream")
