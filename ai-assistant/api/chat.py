# 统一问答接口 —— 用户只面对这一个入口
# 流程：意图识别 → 路由到 Agent（第 4 步接入 kb-agent）→ 回答
# 两个端点：/chat 一次性返回全文；/chat/stream 用 SSE 逐段返回（打字机效果）
# SSE 事件形状与 kb-agent 保持一致（meta → delta → done），前端一套代码两边通用

import json
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.database import SessionLocal
from models.call import Call
from services import llm_service, registry

router = APIRouter(prefix="/api/v1", tags=["统一问答"])


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None   # 不传则开启新会话（透传给 Agent 用）
    history: list[dict] | None = None   # 兜底对话的历史（本服务不存对话，由调用方传入）


def sse_event(event: str, data: dict) -> str:
    """拼一条 SSE 消息：event 行 + data 行 + 空行结尾"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def record_call(question: str, intent_agent: str, answer_source: str, degraded: bool, duration_ms: int):
    """每次问答调用记一笔（管理端调用统计的数据来源）—— 单独开连接，不干扰问答主流程"""
    db = SessionLocal()
    try:
        db.add(Call(
            question=question[:300],
            intent_agent=intent_agent,
            answer_source=answer_source,
            degraded=degraded,
            duration_ms=duration_ms,
        ))
        db.commit()
    finally:
        db.close()


@router.post("/chat")
def chat(req: ChatRequest):
    """统一问答：意图识别 → 路由到 Agent → 回答（一次性返回全文）"""
    start = time.time()
    intent = llm_service.classify_intent(req.question)
    agent = intent["agent"]
    degraded = False
    answer = ""
    sources = []
    session_id = req.session_id
    answer_source = "none"

    # 路由：knowledge → 转发 kb-agent；其余 → 兜底对话
    if agent == "knowledge":
        if registry.is_available(agent):
            result = registry.ask_knowledge(req.question, req.session_id)
            if result:
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                session_id = result.get("session_id", req.session_id)
                answer_source = "knowledge"
            else:
                degraded = True   # kb-agent 在线但调用失败 → 降级兜底
        else:
            degraded = True       # kb-agent 不在线 → 降级兜底

    # 没被 Agent 接住 → 兜底对话
    if answer_source != "knowledge":
        if not llm_service.is_configured():
            answer = "未配置大模型，请在 .env 中填写 LLM 配置。"
        else:
            answer = llm_service.chat_general(req.question, req.history)
            answer_source = "general"

    # 记一笔调用（意图/实际来源/降级/耗时）—— 管理端调用统计的数据来源
    record_call(req.question, agent, answer_source, degraded, int((time.time() - start) * 1000))

    resp = {
        "question": req.question,
        "answer": answer,
        "agent": agent,
        "reason": intent["reason"],
        "answer_source": answer_source,
        "session_id": session_id,
    }
    if answer_source == "knowledge":
        resp["sources"] = sources
    if degraded:
        resp["degraded"] = True   # 想走 Agent 但 Agent 不可用 → 降级兜底
    return resp


@router.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """统一问答（流式版）：SSE 逐段返回回答"""
    start = time.time()
    intent = llm_service.classify_intent(req.question)
    agent = intent["agent"]
    # 生成器里随时可能 return/异常，用可变字典记录最终状态，finally 里统一落库
    record = {"answer_source": "none", "degraded": False}

    def generate():
        # 先发 meta：调度信息 + 降级标记（前端可以显示"正在调用 xx Agent"）
        yield sse_event("meta", {
            "agent": agent,
            "reason": intent["reason"],
            "session_id": req.session_id,
        })

        # 路由：knowledge 且在线 → kb-agent SSE 原样透传（含它自己的 meta/delta/done）
        if agent == "knowledge":
            if registry.is_available(agent):
                try:
                    for line in registry.stream_knowledge(req.question, req.session_id):
                        yield line
                    record["answer_source"] = "knowledge"
                    return
                except Exception:
                    record["degraded"] = True   # 透传中途失败 → 走下面的兜底对话
            else:
                record["degraded"] = True

        if not llm_service.is_configured():
            yield sse_event("delta", {"text": "未配置大模型，请在 .env 中填写 LLM 配置。"})
            yield sse_event("done", {"answer_source": "none"})
            return

        for delta in llm_service.stream_general(req.question, req.history):
            yield sse_event("delta", {"text": delta})
        record["answer_source"] = "general"
        yield sse_event("done", {
            "answer_source": "general",
            "degraded": agent == "knowledge",
        })

    def generate_with_record():
        # finally：无论流正常结束、降级还是客户端断开，都记一笔调用
        try:
            yield from generate()
        finally:
            record_call(req.question, agent, record["answer_source"], record["degraded"],
                        int((time.time() - start) * 1000))

    return StreamingResponse(generate_with_record(), media_type="text/event-stream")
