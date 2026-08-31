# 统一问答接口 —— 用户只面对这一个入口
# 流程：意图识别 → 路由到 Agent（第 4 步接入 kb-agent）→ 回答
# 两个端点：/chat 一次性返回全文；/chat/stream 用 SSE 逐段返回（打字机效果）
# SSE 事件形状与 kb-agent 保持一致（meta → delta → done），前端一套代码两边通用

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services import llm_service, registry

router = APIRouter(prefix="/api/v1", tags=["统一问答"])


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None   # 不传则开启新会话（透传给 Agent 用）
    history: list[dict] | None = None   # 兜底对话的历史（本服务不存对话，由调用方传入）


def sse_event(event: str, data: dict) -> str:
    """拼一条 SSE 消息：event 行 + data 行 + 空行结尾"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
def chat(req: ChatRequest):
    """统一问答：意图识别 → 路由到 Agent → 回答（一次性返回全文）"""
    intent = llm_service.classify_intent(req.question)
    agent = intent["agent"]
    degraded = False

    # 路由：knowledge → 转发 kb-agent；其余 → 兜底对话
    if agent == "knowledge":
        if registry.is_available(agent):
            result = registry.ask_knowledge(req.question, req.session_id)
            if result:
                return {
                    "question": req.question,
                    "answer": result.get("answer", ""),
                    "agent": agent,
                    "reason": intent["reason"],
                    "answer_source": "knowledge",
                    "sources": result.get("sources", []),
                    "session_id": result.get("session_id", req.session_id),
                }
            degraded = True
        else:
            degraded = True

    if not llm_service.is_configured():
        answer = "未配置大模型，请在 .env 中填写 LLM 配置。"
    else:
        answer = llm_service.chat_general(req.question, req.history)

    return {
        "question": req.question,
        "answer": answer,
        "agent": agent,
        "reason": intent["reason"],
        "answer_source": "general" if llm_service.is_configured() else "none",
        "degraded": degraded,   # 想走 Agent 但 Agent 不可用 → 降级兜底
        "session_id": req.session_id,
    }


@router.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """统一问答（流式版）：SSE 逐段返回回答"""
    intent = llm_service.classify_intent(req.question)
    agent = intent["agent"]

    def generate():
        # 先发 meta：调度信息 + 降级标记（前端可以显示"正在调用 xx Agent"）
        yield sse_event("meta", {
            "agent": agent,
            "reason": intent["reason"],
            "session_id": req.session_id,
        })

        # 路由：knowledge 且在线 → kb-agent SSE 原样透传（含它自己的 meta/delta/done）
        if agent == "knowledge" and registry.is_available(agent):
            try:
                for line in registry.stream_knowledge(req.question, req.session_id):
                    yield line
                return
            except Exception:
                pass   # 透传中途失败 → 走下面的兜底对话

        if not llm_service.is_configured():
            yield sse_event("delta", {"text": "未配置大模型，请在 .env 中填写 LLM 配置。"})
            yield sse_event("done", {"answer_source": "none"})
            return

        answer = ""
        for delta in llm_service.stream_general(req.question, req.history):
            answer += delta
            yield sse_event("delta", {"text": delta})
        yield sse_event("done", {
            "answer_source": "general",
            "degraded": agent == "knowledge",
        })

    return StreamingResponse(generate(), media_type="text/event-stream")
