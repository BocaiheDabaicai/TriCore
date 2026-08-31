# LLM 服务 —— 调度器的大脑，两个能力：
#   1. 意图识别：判断用户问题该交给哪个 Agent（输出 JSON）
#   2. 通用对话：没有任何 Agent 能接时的兜底（调度器自己直接回答）
# 和 kb-agent 的 llm_service 区别：kb-agent 做"检索+生成"，这里做"判断+兜底"

import json

from openai import OpenAI

from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)

# 已接入的 Agent 名单 —— 意图识别的提示词从这里生成，以后加 Agent 只改这里
AGENTS = {
    "knowledge": "企业知识问答（公司制度、文档、办事流程相关问题）",
    "general": "通用对话（闲聊、问候、与公司知识无关的问题）",
}


def is_configured() -> bool:
    return all([LLM_API_KEY, LLM_BASE_URL, LLM_MODEL])


def classify_intent(question: str) -> dict:
    """
    意图识别：判断问题该交给哪个 Agent
    返回 {"agent": "knowledge|general", "reason": "判断理由"}
    - response_format=json_object 让模型只输出合法 JSON
    - 识别失败 → 降级 general（保证入口永远能回答）
    """
    agent_list = "\n".join(f"- {name}：{desc}" for name, desc in AGENTS.items())

    system_prompt = (
        "你是企业AI助手的调度器。请判断用户的问题应该交给哪个 Agent 处理，并输出 JSON：\n"
        '{"agent": "Agent名称", "reason": "一句话判断理由"}\n'
        "可选的 Agent：\n"
        f"{agent_list}\n"
        "规则：与公司知识（制度/文档/流程）相关的交给 knowledge，其余交给 general。"
        "只输出 JSON，不要输出任何其他内容"
    )

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)

        agent = result.get("agent")
        if agent not in AGENTS:
            agent = "general"
        return {"agent": agent, "reason": str(result.get("reason", ""))[:200]}
    except Exception:
        # 网络/返回异常 → 降级 general，入口不中断
        return {"agent": "general", "reason": "意图识别失败，走通用对话"}


def _build_messages(history: list[dict], question: str) -> list[dict]:
    """组装消息列表：系统指令 + 历史对话 + 当前问题"""
    messages = [{
        "role": "system",
        "content": "你是企业AI助手。请直接、友好地回答用户的问题，回答使用中文。",
    }]
    messages.extend(history or [])
    messages.append({"role": "user", "content": question})
    return messages


def chat_general(question: str, history: list[dict] | None = None) -> str:
    """通用对话（一次性返回全文）—— 历史由调用方传入，本服务不存对话"""
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=_build_messages(history or [], question),
        temperature=0.7,
    )
    return response.choices[0].message.content


def stream_general(question: str, history: list[dict] | None = None):
    """通用对话（流式版）—— 生成器逐段产出，SSE 接口用"""
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=_build_messages(history or [], question),
        temperature=0.7,
        stream=True,
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
