# LLM 服务 —— 统一封装大模型调用
# 概念：RAG（检索增强生成）
#   1. 检索（Retrieval）：先从知识库里找出和问题相关的文档片段
#   2. 增强（Augmented）：把这些片段塞进提示词，告诉模型"参考这些资料回答"
#   3. 生成（Generation）：大模型基于资料生成答案
# 好处：模型回答有据可查，不会凭空编造（减少"幻觉"）

import json

from openai import OpenAI

from core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# 创建 OpenAI 客户端（兼容所有 OpenAI 协议的国内服务）
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


def is_configured() -> bool:
    """检查 LLM 是否配置好了（key、地址、模型名都填了才算）"""
    return all([LLM_API_KEY, LLM_BASE_URL, LLM_MODEL])


def chat_with_context(question: str, context: str) -> str:
    """
    带资料回答问题（RAG 的"增强+生成"部分）
    - question: 用户的问题
    - context: 检索出来的相关资料（来自知识库）
    """
    # 提示词：给模型交代角色、规则和参考资料
    system_prompt = (
        "你是企业知识库助手。请仅根据下面提供的【参考资料】回答用户问题。"
        "如果资料中没有答案，就诚实地说'知识库中暂无相关内容'，不要编造。"
        "资料中标记为【制度】的是公司规章制度，标记为【文档】的是操作指引类文档，"
        "标记为【流程模板】的是办事流程，回答时应把流程步骤讲清楚。\n\n"
        f"【参考资料】\n{context}"
    )

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.3,  # 低温度 = 回答更稳定、更少发挥（知识问答场景合适）
    )

    return response.choices[0].message.content


def classify_upload(filename: str, text: str) -> dict:
    """
    让 LLM 分析上传内容：判断知识类型、拟标题、拟定业务分类、尝试提取流程步骤
    返回 {"kind": ..., "title": str, "category": str, "steps": list | None}
    - response_format=json_object 让模型只输出合法 JSON，不用自己清洗格式
    - 识别失败/返回异常时降级为 document（不阻断上传，分类错了可手动改）
    """
    sample = text[:3000]   # 分类只看前 3000 字，省 token

    system_prompt = (
        "你是企业知识库管理员。请分析用户上传的文件内容，判断它属于哪一类知识，并输出 JSON：\n"
        '{"kind": "policy|document|workflow", "title": "合适的标题", '
        '"category": "业务分类", "steps": null}\n'
        "- kind 取值：policy 制度（公司规章、管理办法）、document 文档（操作指引、说明手册）、"
        "workflow 流程（办事流程，含多个步骤）\n"
        "- category 是业务分类：由你根据文件内容自行判断拟定，用不超过 10 个字的简短词语概括"
        "（不要受固定分类列表限制）\n"
        '- 如果是 workflow，steps 输出流程步骤数组：[{"order":1,"name":"步骤名","role":"负责人"}]，否则为 null\n'
        "- 只输出 JSON，不要输出任何其他内容"
    )

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"文件名：{filename}\n\n内容：\n{sample}"},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)

        kind = result.get("kind")
        if kind not in ("policy", "document", "workflow"):
            kind = "document"
        title = str(result.get("title") or filename).strip()[:200]
        category = str(result.get("category") or "").strip()[:10] or "未分类"
        steps = result.get("steps") if kind == "workflow" else None
        return {"kind": kind, "title": title, "category": category, "steps": steps}
    except Exception:
        # 网络/返回异常 → 降级：按文档处理，标题用文件名，上传不中断
        return {"kind": "document", "title": filename, "category": "未分类", "steps": None}


def pick_template(description: str, template_list: str) -> str:
    """让 LLM 从模板列表里挑最匹配的一个，只返回模板名"""
    system_prompt = (
        "你是企业流程助手。用户会描述一件想办的事，请从下面的模板列表中"
        "挑选最匹配的一个模板。\n"
        "要求：只输出模板名称本身，不要输出任何其他内容。\n"
        "如果没有任何模板匹配，输出：无匹配\n\n"
        f"【模板列表】\n{template_list}"
    )

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()   # strip 去掉首尾空白/换行


def chat_with_history(question: str, context: str, history: list[dict]) -> str:
    """
    带历史记录的多轮问答
    - question: 当前问题
    - context: 检索到的资料
    - history: 之前的对话，格式 [{"role": "user"/"assistant", "content": "..."}, ...]
    """
    system_prompt = (
        "你是企业知识库助手。请仅根据下面提供的【参考资料】回答用户问题。"
        "如果资料中没有答案，就诚实地说'知识库中暂无相关内容'，不要编造。"
        "资料中标记为【制度】的是公司规章制度，标记为【文档】的是操作指引类文档，"
        "标记为【流程模板】的是办事流程，回答时应把流程步骤讲清楚。\n\n"
        f"【参考资料】\n{context}"
    )

    # 消息列表 = 系统指令 + 历史对话 + 当前问题
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
    )

    return response.choices[0].message.content
