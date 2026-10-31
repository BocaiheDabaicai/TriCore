# LLM 服务 —— 文献信息识别（照 kb-agent/services/llm_service.py 的模式精简而来）
# 两条路：文字（PDF 首页文字层）直接交给模型；图片（扫描件/图片文件）走视觉理解
# 返回结构化 JSON：语言 / 标题 / 作者 / 出版时间 / 期刊 / 分类标签

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


def image_mime(data: bytes) -> str:
    """按文件头判断图片格式（视觉接口要求 mime 与真实格式一致）"""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "image/jpeg"


def _instructions(tag_candidates: list[str]) -> str:
    """抽取要求（整段提示词）——文字路作 system、视觉路拼进 user 文本"""
    cand = "、".join(tag_candidates) if tag_candidates else "（暂无候选，可自行拟定）"
    return (
        "你是文献信息抽取助手。用户会给你一篇学术论文的开头部分（标题、作者、摘要等）。\n"
        "请抽取文献信息，只输出 JSON：\n"
        '{"lang": "zh|en", "title": "...", "author": "...", "published": "...", "journal": "...", "tag": "..."}\n'
        "- lang：按论文正文语言，中文 zh、英文 en\n"
        "- title：中文文献填原文标题；英文文献填准确的中文学术译名（贴合工程管理/管理学领域表述）\n"
        "- author：全部作者，多人用「、」分隔；英文作者保留原文拼写\n"
        "- published：出版时间，能确定到月用 YYYY-MM，只有年份用 YYYY\n"
        "- journal：期刊名称——注意页眉页脚线索（如期刊官网一行、DOI 链接里的刊名缩写），找到就填\n"
        f"- tag：分类标签，优先从候选里挑最贴近的一个：{cand}；都不合适再自己拟（不超过 8 个字）\n"
        "- 抓不到或不确定的字段填空字符串 \"\"，绝不编造；只输出 JSON，不要任何其他文字"
    )


def extract_fields(
    text: str | None,
    image: bytes | None,
    filename: str,
    tag_candidates: list[str],
) -> dict | None:
    """
    从论文开头部分抽取文献信息，成功返回
    {"lang", "title", "author", "published", "journal", "tag"}，失败返回 None（不阻断手动填写）
    - text 与 image 二选一：有文字层走文字（便宜、准确）；否则走视觉
    """
    if not is_configured():
        return None

    instructions = _instructions(tag_candidates)
    if text:
        messages = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": f"文件名：{filename}\n\n论文开头部分：\n{text}"},
        ]
        # 文字路：json_object 让模型只输出合法 JSON，不用自己清格式
        extra = {"response_format": {"type": "json_object"}}
    elif image:
        # 视觉路：单条 user 消息带图片（kb 的转写实测可用的形态）；
        # json_object 与图片入参的组合支持情况因供应商而异，靠提示词约束 + 解析时清格式
        b64 = base64.b64encode(image).decode()
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{instructions}\n\n下面是论文的首页图片，请按要求抽取。"},
                    {"type": "image_url", "image_url": {"url": f"data:{image_mime(image)};base64,{b64}"}},
                ],
            }
        ]
        extra = {}
    else:
        return None

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.1,
            **extra,
        )
        content = (response.choices[0].message.content or "").strip()
        return _parse(content)
    except Exception as e:
        print(f"警告：文献信息识别失败：{e}")
        return None


# ---------------------------------------------------------------
# 全文速读总结：按固定 7 段结构输出 Markdown，直接贴进笔记区
# 结构来自用户自己的阅读笔记模板（study-agent/structrue.md）
# ---------------------------------------------------------------

def _summary_instructions() -> str:
    """总结要求：固定结构 + 篇幅约束 + 只提取不编造"""
    return (
        "你是文献速读助手。用户会给你一篇论文的全文，请严格按下面的固定结构输出 Markdown。\n"
        "写作要求：\n"
        "- 只输出正文 Markdown，不要用代码块包裹，不要开场白、总结语或目录。\n"
        "- 所有内容用中文；英文原文翻译成中文，中文原文可摘录原句。\n"
        "- 严格取材：每个标题下只写原文中与该标题直接对应的内容；可以翻译、摘录、压缩措辞，但不得改写原意、不得归纳推断、不得补充原文没有的信息。\n"
        "- 原文没有直接写出的数字、参数、结论一律不要写；不得计算或推导（例如不要由 α 和 K 反推 P）。\n"
        "- 某一段完全没有对应内容：只保留该段大标题（## 级），不要写它的子标题。\n"
        "- 某一段有内容但个别子项缺失：保留子项标题，内容留空；不要写“原文未涉及”等占位文字。\n"
        "- 每个非空小节只摘录 1~3 句最关键的原句（或其中文翻译），宁短勿长；不为凑字数扩写。\n"
        "- 不要使用 LaTeX / 数学公式语法；公式、推导过程和完整参数表不要搬入，用普通文字说明关键变量或结论即可。\n"
        "- 「表达想法」只写作者在原文中明确表达的想法或观点，不是你的评价；作者没有明确表达就留空。\n"
        "- 「可信度如何」只列论文自述的检验证据（样本量、对照、稳健性检验等），不要下判断。\n"
        "- 「图表名称与意义」只翻译/摘录原文图表标题及作者给出的说明；作者没写意义就只写标题。\n"
        "- 「指导论文」保持不变：统计参考文献总篇数并粗分领域（最多 4 类），数字前加“约”；无法统计就留空。\n"
        "- 不要输出固定结构以外的任何文字。\n\n"
        "固定结构：\n"
        "## 前言\n"
        "### 1. 背景介绍\n"
        "### 2. 当前现状\n"
        "### 3. 不足 / 启发\n"
        "### 4. 提出的想法\n"
        "### 5. 可能产生的贡献\n"
        "## 研究准备\n"
        "### 1. 理论准备\n"
        "### 2. 实践准备\n"
        "### 3. 数据来源\n"
        "## 研究过程\n"
        "### 1. 数据定义\n"
        "### 2. 计算 / 分析的重要步骤\n"
        "### 3. 图表名称与意义\n"
        "## 研究结果和检验\n"
        "### 1. 结果介绍\n"
        "### 2. 研究检验\n"
        "### 3. 可信度如何\n"
        "## 研究再检验\n"
        "### 1. 研究扩展检验\n"
        "### 2. 表达想法\n"
        "## 研究结论\n"
        "### 1. 总结研究\n"
        "### 2. 自身贡献\n"
        "### 3. 实验不足\n"
        "### 4. 未来展望\n"
        "## 指导论文\n"
        "### 1. 总计篇数\n"
        "### 2. 领域分类"
    )


def summarize_paper(text: str, filename: str) -> str | None:
    """
    全文速读总结：成功返回 Markdown（固定 7 段结构），失败返回 None（不阻断手动流程）
    """
    if not is_configured() or not text:
        return None
    messages = [
        {"role": "system", "content": _summary_instructions()},
        {"role": "user", "content": f"文件名：{filename}\n\n论文全文：\n{text}"},
    ]
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.1,
        )
        content = (response.choices[0].message.content or "").strip()
        return _strip_code_fence(content) or None
    except Exception as e:
        print(f"警告：论文总结失败：{e}")
        return None


def _strip_code_fence(content: str) -> str:
    """模型偶尔会用 ```markdown 包住整段输出，这里剥掉"""
    if not content.startswith("```"):
        return content
    content = content.strip("`").strip()
    if content.startswith("markdown"):
        content = content[len("markdown"):].strip()
    elif content.startswith("md"):
        content = content[len("md"):].strip()
    return content


def _parse(content: str) -> dict | None:
    """解析模型输出（容忍 ```json 包裹），字段规范化到数据库列宽"""
    if content.startswith("```"):
        content = content.strip("`").strip()
        if content.startswith("json"):
            content = content[4:].strip()
    try:
        raw = json.loads(content)
    except Exception:
        return None
    lang = raw.get("lang") if raw.get("lang") in ("zh", "en") else "zh"
    return {
        "lang": lang,
        "title": str(raw.get("title") or "").strip()[:200],
        "author": str(raw.get("author") or "").strip()[:200],
        "published": str(raw.get("published") or "").strip()[:20],
        "journal": str(raw.get("journal") or "").strip()[:200],
        "tag": str(raw.get("tag") or "").strip()[:50],
    }
