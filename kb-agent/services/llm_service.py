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


def generate_keywords(title: str, content: str) -> str | None:
    """
    为一条已有知识生成关键词（补录存量数据用）
    - 返回 "关键词、关键词" 格式字符串，失败返回 None
    """
    system_prompt = (
        "你是企业知识库管理员。请根据知识条目的标题和内容，提取 3~5 个最能代表它的关键词，"
        "用中文顿号分隔（如：住宿、申请、押金）。只输出 JSON："
        '{"keywords": "关键词、关键词"}'
    )
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"标题：{title}\n\n内容：\n{content[:1500]}"},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return str(result.get("keywords") or "").strip()[:200] or None
    except Exception:
        return None


def classify_dimension(question: str, prev_question: str | None = None) -> str:
    """
    判断问题的维度：breadth（宽度，列举/概览）还是 depth（深度，具体细节）
    - 纯 AI 判断：不写固定词表、不给条目名单——自然语言千变万化（名称不全、意思相近），
      词表囊括不了，让 AI 按语义自行判断
    - 只给两个输入：当前问题（判断对象）+ 上一轮问题（理解指代，如「那条」「它」）
    - 失败降级 depth：深度是现状，降级等于"和原来一样"，不会更差
    """
    system_prompt = (
        "你是企业知识库助手的路由判断器。请判断「当前问题」属于哪种维度，只输出 JSON：\n"
        '{"dimension": "breadth|depth", "reason": "一句话理由"}\n'
        "- breadth（宽度）：列举/概览类——用户想知道有哪些、全部、全貌、清单、分类，"
        "如「公司有哪些制度」「介绍一下全部资料」「还有什么」\n"
        "- depth（深度）：具体细节类——用户针对某一条知识、某个具体事项提问，或想深入了解某一条，"
        "如「电费怎么收费」「押金多少」「具体讲一下」「宿舍那个再详细说说」\n"
        "判断规则：\n"
        "1. 只根据「当前问题」判断，「上一轮问题」仅作背景参考（用于理解指代）\n"
        "2. 用户要求「更全面/全部/列出/还有哪些」类表达 → breadth\n"
        "3. 用户点名某条知识（名称可能不全或意思相近）、追问细节、要求「具体/详细/展开」 → depth\n"
        "4. 拿不准时优先判 depth"
    )
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"当前问题：{question}\n上一轮问题：{prev_question or '（无）'}"},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return "breadth" if result.get("dimension") == "breadth" else "depth"
    except Exception:
        return "depth"


def build_system_prompt(context: str, mode: str = "depth") -> str:
    """
    RAG 提示词：给模型交代角色、规则和参考资料
    - depth：基于检索到的资料片段回答（原有逻辑）
    - breadth：基于知识清单（标题+关键词）组织概览回答
    两种模式末尾都带引导语，引导用户用自然语言纠正维度（判错也不怕）
    """
    if mode == "breadth":
        return (
            "你是企业知识库助手。下面列出的是公司知识库的条目清单"
            "（按业务分类分组，条目格式：标题【类型】(关键词)）。\n"
            "请根据用户的问题介绍相关条目：按分类组织成清晰的清单，"
            "每条简要说明主题即可，不要展开细节。\n"
            "用户问某一类（如制度）时只列那一类；清单较长时按分类归纳展示。\n"
            "回答末尾引导用户：想具体了解哪一条？说出名称即可。\n\n"
            f"【知识清单】\n{context}"
        )
    return (
        "你是企业知识库助手。请仅根据下面提供的【参考资料】回答用户问题。"
        "如果资料中没有答案，只回复一句话：'知识库中暂无相关内容，该问题已记录，我们会尽快补充相关资料。'，不要编造，也不要回答资料之外的内容。"
        "资料中标记为【制度】的是公司规章制度，标记为【文档】的是操作指引类文档，"
        "标记为【流程模板】的是办事流程，回答时应把流程步骤讲清楚。"
        "回答末尾可以简短提示：还想了解其他相关制度吗？\n\n"
        f"【参考资料】\n{context}"
    )


def classify_upload(filename: str, text: str) -> dict:
    """
    让 LLM 分析上传内容：判断知识类型、拟标题、拟定业务分类、提取流程步骤、生成关键词
    返回 {"kind": ..., "title": str, "category": str, "steps": list | None, "keywords": str | None}
    - response_format=json_object 让模型只输出合法 JSON，不用自己清洗格式
    - 识别失败/返回异常时降级为 document（不阻断上传，分类错了可手动改）
    """
    sample = text[:3000]   # 分类只看前 3000 字，省 token

    system_prompt = (
        "你是企业知识库管理员。请分析用户上传的文件内容，判断它属于哪一类知识，并输出 JSON：\n"
        '{"kind": "policy|document|workflow", "title": "合适的标题", '
        '"category": "业务分类", "steps": null, "keywords": "关键词"}\n'
        "- kind 取值：policy 制度（公司规章、管理办法）、document 文档（操作指引、说明手册）、"
        "workflow 流程（办事流程，含多个步骤）\n"
        "- category 是业务分类：由你根据文件内容自行判断拟定，用不超过 10 个字的简短词语概括"
        "（不要受固定分类列表限制）\n"
        '- 如果是 workflow，steps 输出流程步骤数组：[{"order":1,"name":"步骤名","role":"负责人"}]，否则为 null\n'
        "- keywords：3~5 个最能代表本条内容的关键词，用中文顿号分隔（如：住宿、申请、押金）\n"
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
        keywords = str(result.get("keywords") or "").strip()[:200] or None
        return {"kind": kind, "title": title, "category": category, "steps": steps, "keywords": keywords}
    except Exception:
        # 网络/返回异常 → 降级：按文档处理，标题用文件名，上传不中断
        return {"kind": "document", "title": filename, "category": "未分类", "steps": None, "keywords": None}


def chat_with_history(question: str, context: str, history: list[dict], mode: str = "depth") -> str:
    """
    带历史记录的多轮问答（history 为空时就是单轮问答）
    - question: 当前问题
    - context: 检索到的资料（depth）或知识清单（breadth）
    - history: 之前的对话，格式 [{"role": "user"/"assistant", "content": "..."}, ...]
    - mode: depth（深度，基于检索片段）/ breadth（宽度，基于清单概览）
    """
    # 消息列表 = 系统指令 + 历史对话 + 当前问题
    messages = [{"role": "system", "content": build_system_prompt(context, mode)}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
    )

    return response.choices[0].message.content


def stream_chat(question: str, context: str, history: list[dict], mode: str = "depth"):
    """
    流式版多轮问答：生成器逐段产出回答文本（SSE 接口用）
    - stream=True 让 API 不再等全文生成完，而是一段一段返回增量
    - yield 出去的每一段都立刻可以发给前端，形成"打字机"效果
    """
    messages = [{"role": "system", "content": build_system_prompt(context, mode)}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
