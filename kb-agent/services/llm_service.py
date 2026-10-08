# LLM 服务 —— 统一封装大模型调用
# 概念：RAG（检索增强生成）
#   1. 检索（Retrieval）：先从知识库里找出和问题相关的文档片段
#   2. 增强（Augmented）：把这些片段塞进提示词，告诉模型"参考这些资料回答"
#   3. 生成（Generation）：大模型基于资料生成答案
# 好处：模型回答有据可查，不会凭空编造（减少"幻觉"）

import base64
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
        '{"dimension": "breadth|aggregate|depth", "reason": "一句话理由"}\n'
        "- breadth（枚举）：只想知道有哪些、全部、全貌、清单、分类，不需要读内容，"
        "如「公司有哪些制度」「介绍一下全部资料」「还有什么」\n"
        "- aggregate（汇总/比较）：要跨多条资料综合、归纳或对比，必须读内容才能答，"
        "如「各部门报销标准有什么区别」「请假和调休的规定有什么不同」"
        "「公司对住宿都有哪些规定」「把所有福利类规定总结一下」\n"
        "- depth（深度）：具体细节类——针对某一条知识、某个具体事项提问，或想深入了解某一条，"
        "如「电费怎么收费」「押金多少」「具体讲一下」「宿舍那个再详细说说」\n"
        "判断规则：\n"
        "1. 只根据「当前问题」判断，「上一轮问题」仅作背景参考（用于理解指代）\n"
        "2. 只要求「列出名字/清单」→ breadth；要求「总结/归纳/比较/区别/共同点」→ aggregate\n"
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
        dim = result.get("dimension")
        return dim if dim in ("breadth", "aggregate") else "depth"
    except Exception:
        return "depth"


def build_system_prompt(context: str, mode: str = "depth") -> str:
    """
    RAG 提示词：给模型交代角色、规则和参考资料
    - depth：基于检索到的资料片段回答（原有逻辑）
    - breadth：基于知识清单（标题+关键词）组织概览回答
    - aggregate：基于全部条目摘要做跨文档汇总/比较
    三种模式末尾都带引导语，引导用户用自然语言纠正维度（判错也不怕）
    """
    if mode == "aggregate":
        return (
            "你是企业知识库助手。下面列出的是公司知识库全部条目的摘要"
            "（按业务分类分组，条目格式：标题【类型】(分类) 摘要）。\n"
            "用户问的是需要综合、归纳或对比的问题，请基于这些摘要作答：\n"
            "1. 分点归纳，涉及多个口径时用对比的方式讲清差异与共同点\n"
            "2. 摘要里没写到的内容不要编造；信息不足时说明「摘要未体现，需查阅某条具体资料」\n"
            "3. 回答末尾引导用户：想具体了解哪一条？说出名称即可。\n\n"
            f"【条目摘要】\n{context}"
        )
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
        '"category": "业务分类", "steps": null, "keywords": "关键词", "summary": "摘要"}\n'
        "- kind 取值：policy 制度（公司规章、管理办法）、document 文档（操作指引、说明手册）、"
        "workflow 流程（办事流程，含多个步骤）\n"
        "- category 是业务分类：由你根据文件内容自行判断拟定，用不超过 10 个字的简短词语概括"
        "（不要受固定分类列表限制）\n"
        '- 如果是 workflow，steps 输出流程步骤数组：[{"order":1,"name":"步骤名","role":"负责人"}]，否则为 null\n'
        "- keywords：3~5 个最能代表本条内容的关键词，用中文顿号分隔（如：住宿、申请、押金）\n"
        "- summary：不超过 100 字的内容摘要，要写出关键标准、数字、流程要点"
        "（如金额、天数、审批环节），用于跨文档汇总比较，不要只写「本文规定了……」\n"
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
        summary = str(result.get("summary") or "").strip()[:500] or None
        return {"kind": kind, "title": title, "category": category, "steps": steps,
                "keywords": keywords, "summary": summary}
    except Exception:
        # 网络/返回异常 → 降级：按文档处理，标题用文件名，上传不中断（摘要留空，可用补录脚本补）
        return {"kind": "document", "title": filename, "category": "未分类", "steps": None,
                "keywords": None, "summary": None}


def summarize(title: str, content: str) -> str | None:
    """
    为一条已有知识生成摘要（存量数据补录用）
    - 返回 100 字内摘要，失败返回 None
    """
    system_prompt = (
        "你是企业知识库管理员。请为下面这条知识写一段不超过 100 字的摘要，"
        "要写出关键标准、数字、流程要点（如金额、天数、审批环节），"
        "用于跨文档汇总比较，不要只写「本文规定了……」。只输出 JSON："
        '{"summary": "摘要"}'
    )
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"标题：{title}\n\n内容：\n{content[:2000]}"},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return str(result.get("summary") or "").strip()[:500] or None
    except Exception as e:
        print(f"警告：生成摘要失败（{title}）：{e}")
        return None


def image_mime(data: bytes) -> str:
    """按文件头判断图片格式（视觉接口要求 mime 与真实格式一致，不能都写 png）"""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "image/jpeg"   # 认不出来按 jpeg 试（目前图片都来自我们自己的渲染，走不到这里）


# 视觉转写每批页数：一次请求带多张图（实测可行）能省调用次数；
# 批太大单次输出可能顶到 max_tokens 被截断——截断时自动对半拆开重试
VISION_BATCH = 4
# 转写是"照抄"，输出量约等于页面文字量。实测：密排论文 4 页 = 4253 token，
# 上限 8000 会把 4 页批截断（截断就白花一次调用去拆半），16000 给足余量
VISION_MAX_TOKENS = 16000


def transcribe_images(images: list[bytes], start_page: int = 1) -> str:
    """
    扫描页图片 → 文字（视觉转写）——图文识别解析的核心
    - images: 每页一张图的字节（PNG/JPEG）
    - start_page: 第一张图对应文档的第几页（用于让模型标注真实页码）
    - 按 VISION_BATCH 分批：每批一次请求，批内多页一起转写
    - 返回带「===第N页===」标记的转写文本；失败页返回占位提示（不静默丢内容）
    """
    if not images or not is_configured():
        return ""

    parts = []
    for i in range(0, len(images), VISION_BATCH):
        batch = images[i:i + VISION_BATCH]
        parts.append(transcribe_batch(batch, start_page + i))
    return "\n\n".join(p for p in parts if p)


def transcribe_batch(images: list[bytes], start_page: int) -> str:
    """一批图（≤VISION_BATCH 张）一次请求转写；输出被截断时对半拆开再试"""
    end_page = start_page + len(images) - 1
    if len(images) == 1:
        page_desc = f"这是文档的第 {start_page} 页扫描图。"
    else:
        page_desc = f"这是同一份文档中连续的 {len(images)} 页扫描图，依次是第 {start_page} 页到第 {end_page} 页。"

    content = [{
        "type": "text",
        "text": (
            f"{page_desc}请逐页转写图中的全部文字：\n"
            "1. 每页开头单独一行写 ===第N页===（N 用上面给出的真实页码）\n"
            "2. 照抄原文——标题、条款编号、表格（单元格之间用 | 分隔）、数字与单位都要保留，"
            "不要改写、不要概括、不要加解释\n"
            "3. 图里看不清的字写 [看不清]，不要猜测编造\n"
            "只输出转写内容，不要任何额外说明。"
        ),
    }]
    for img in images:
        b64 = base64.b64encode(img).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{image_mime(img)};base64,{b64}"},
        })

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": content}],
            temperature=0.1,
            max_tokens=VISION_MAX_TOKENS,
        )
        text = (response.choices[0].message.content or "").strip()
        truncated = response.choices[0].finish_reason == "length"
    except Exception as e:
        # 整批请求失败：不拆开重试（多半是网络/密钥问题，拆了也一样失败），整批给占位提示
        print(f"警告：第 {start_page}~{end_page} 页视觉转写失败：{e}")
        return f"===第{start_page}页===\n（第 {start_page}~{end_page} 页视觉转写失败）"

    # 被 max_tokens 截断 → 对半拆开重新转（每半输出量减半，一般就不截了）
    if truncated and len(images) > 1:
        mid = len(images) // 2
        print(f"提示：第 {start_page}~{end_page} 页转写被截断，拆成两批重试")
        return transcribe_batch(images[:mid], start_page) + "\n\n" + transcribe_batch(images[mid:], start_page + mid)

    if not text:
        return f"===第{start_page}页===\n（第 {start_page}~{end_page} 页视觉转写为空）"
    return text


def preselect_documents(question: str, catalog: list[dict]) -> list[int]:
    """
    AI 预选：从知识目录里挑出回答这个问题最需要的资料（给「指定文档」面板做默认勾选）
    - catalog: [{"id", "title", "category", "keywords"}]，只给标题/分类/关键词，不给正文（省 token）
    - 返回 id 列表（0~5 条，宁缺毋滥）；失败返回 []，前端就不预选、让用户自己勾
    """
    lines = []
    for it in catalog:
        line = f'{it["id"]}. {it["title"]}（{it.get("category") or "未分类"}）'
        if it.get("keywords"):
            line += f" 关键词：{it['keywords']}"
        lines.append(line)

    system_prompt = (
        "你是企业知识库的资料筛选器。用户准备提一个问题，请你从下面的知识目录里挑出"
        "回答该问题最需要的资料，最多 5 条，宁缺毋滥——目录里没有相关的就返回空数组。\n"
        "只输出 JSON：\n"
        '{"ids": [资料编号], "reason": "一句话理由"}\n'
        "判断依据：问题涉及的制度/流程/文档名称、关键词、业务领域。\n"
        f"【知识目录】\n" + "\n".join(lines)
    )
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"问题：{question}"},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        valid = {it["id"] for it in catalog}
        # 只认目录里真实存在的 id（模型可能编编号），再截到 5 条
        ids = [i for i in (result.get("ids") or []) if i in valid]
        return ids[:5]
    except Exception as e:
        print(f"警告：AI 预选文档失败：{e}")
        return []


def draft_supplement(question: str) -> dict | None:
    """
    为未命中问题起草一份补充资料的骨架（供人工编辑后入库）
    原则：AI 并不知道公司的真实规定，所以**只搭骨架、列要点，绝不编造具体数字/标准/流程**，
    用【待补充：…】占位，把"这篇资料该写什么"列清楚，内容由人工填写
    返回 {"title", "kind", "category", "keywords", "content"}；失败返回 None（前端提示手工填写）
    """
    system_prompt = (
        "你是企业知识库管理员。用户问过下面这个问题，但知识库里查不到资料（这是一条未命中记录）。"
        "请起草一份补充资料的骨架，供人工填写后入库。只输出 JSON：\n"
        '{"title": "标题", "kind": "policy|document|workflow", "category": "业务分类", '
        '"keywords": "关键词、关键词", "content": "正文骨架"}\n'
        "- title：贴合这个问题的制度 / 文档标题\n"
        "- kind：policy 制度（规章、办法）/ document 文档（指引、说明）/ workflow 流程（多个步骤）\n"
        "- category：业务分类，不超过 10 个字\n"
        "- keywords：3~5 个关键词，中文顿号分隔\n"
        "- content：正文骨架。重要：**你并不知道公司的真实规定，绝对不要编造具体数字、金额、"
        "标准、时限、审批环节**。请用要点框架列出这篇资料应该包含哪些内容"
        "（如：适用范围 / 具体标准 / 办理流程 / 注意事项），每项下面用【待补充：需要写明的内容】占位；"
        "也可以列出「要准确回答这个问题，资料里必须写明哪些信息」，帮助人工把资料写全\n"
        "只输出 JSON，不要输出任何其他内容"
    )
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"未命中的问题：{question}"},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)

        kind = result.get("kind")
        if kind not in ("policy", "document", "workflow"):
            kind = "document"
        content = str(result.get("content") or "").strip()
        if not content:
            return None
        return {
            "title": str(result.get("title") or question).strip()[:200],
            "kind": kind,
            "category": str(result.get("category") or "").strip()[:10] or "未分类",
            "keywords": str(result.get("keywords") or "").strip()[:200] or None,
            "content": content,
        }
    except Exception as e:
        # 起草是人工在管理端点的操作，失败会立刻被看到，这里打日志便于排查（网络/限流等偶发）
        print(f"警告：AI 起草补充资料失败：{e}")
        return None


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
