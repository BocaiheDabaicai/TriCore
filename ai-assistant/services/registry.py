# Agent 注册表 —— 调度器只认"统一协议"，不关心 Agent 内部怎么实现
# 统一协议（README 定义）：
#   输入：{"question": "...", "context": {...}}
#   输出：{"answer": "...", "references": [...], "confidence": 0.9}
# 内嵌阶段它是进程内函数调用；拆分阶段（现在）它是 HTTP 请求/响应体——形态不变
#
# 注册新 Agent 只需三步：
#   1. AGENTS 里加一条配置
#   2. 按协议写一个 ask_xxx / stream_xxx（转 HTTP + 透传）
#   3. llm_service.AGENTS 里加意图识别的描述

import httpx

from core.config import KB_AGENT_URL

AGENTS = {
    "knowledge": {
        "name": "企业知识问答",
        "base_url": KB_AGENT_URL,
    },
}


def is_available(agent: str) -> bool:
    """探测 Agent 是否在线：GET 它的根路径，1 秒超时"""
    entry = AGENTS.get(agent)
    if not entry:
        return False
    try:
        r = httpx.get(f"{entry['base_url']}/", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


def ask_knowledge(question: str, session_id: str | None) -> dict | None:
    """
    调用 kb-agent 一次性问答（转 HTTP）
    失败（没启动/超时/报错）返回 None，由调用方降级兜底
    """
    try:
        r = httpx.post(
            f"{KB_AGENT_URL}/api/v1/agent/chat",
            json={"question": question, "session_id": session_id},
            timeout=60.0,
        )
        r.raise_for_status()  # 如果这次 HTTP 请求的响应状态码是错误（4xx/5xx），就立刻抛出异常。
        return r.json()
    except Exception:
        return None


def stream_knowledge(question: str, session_id: str | None):
    """
    调用 kb-agent 流式问答，逐行透传 SSE（原样转发，不解析不改写）
    生成器产出的是 SSE 原始行（event:/data:/空行），调用方直接 yield 给前端
    """
    with httpx.stream(
            "POST",
            f"{KB_AGENT_URL}/api/v1/agent/chat/stream",
            json={"question": question, "session_id": session_id},
            timeout=60.0,
    ) as r:
        r.raise_for_status()
        # iter_lines 会剥掉每行的换行符，必须补回 "\n" 才还原 SSE 原始格式
        # 空行（SSE 的消息分隔符）也要原样保留，否则前端按 "\n\n" 切块会切不出来
        for line in r.iter_lines():
            yield line + "\n"
