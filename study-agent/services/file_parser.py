# 解析层（精简版，取自 kb-agent 同一套思路）——只服务于"文献信息识别"：
# 取论文开头部分（标题→摘要这一段）：
#   PDF 有文字层 → 前两页文字直接取（免费、零转写误差）
#   PDF 没有文字层（扫描件）/ 图片文件 → 首页渲染成图走视觉理解
from io import BytesIO

import pymupdf
from pypdf import PdfReader

# 扫描页判定阈值：一页正常文字量远超这个数，低于它说明没有文字层（扫描件、纯图片页）
SCANNED_PAGE_MIN_CHARS = 50

# 渲染 DPI：150 对中文印刷体够清楚；再高徒增图片体积和视觉调用的 token
SCAN_RENDER_DPI = 150

# 开头部分最多截多少字：标题/作者/摘要在前两页；期刊信息常落在页脚（Elsevier 的版头在 5000 字上下），6000 才盖得住
FRONT_MATTER_MAX_CHARS = 6000

# 全文总结：平均每页低于这个字符数就当作扫描件（没有文字层，跳过全文总结）
FULL_TEXT_MIN_CHARS_PER_PAGE = 50

# 全文总结最多送多少字：超长文档（学位论文等）保留头部 60% + 尾部 40%，中间标注省略
FULL_TEXT_MAX_CHARS = 100000

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _has_pdf_magic(data: bytes) -> bool:
    """按文件头判断 PDF——文件名可能被编码截断，不能只信后缀"""
    return b"%PDF-" in data[:1024]


def _has_image_magic(data: bytes) -> bool:
    """按文件头判断常见图片格式（png / jpeg / webp / gif）"""
    return (
        data[:8] == b"\x89PNG\r\n\x1a\n"
        or data[:3] == b"\xff\xd8\xff"
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
        or data[:6] in (b"GIF87a", b"GIF89a")
    )


def front_matter(filename: str, content: bytes) -> tuple[str | None, bytes | None]:
    """
    返回 (文字, 图片)，二选一：
    - PDF 且开头有文字层 → 前两页文字
    - PDF 没有文字层（扫描件）→ 首页渲染成 PNG
    - 图片文件 → 本身就是"没有文字层的页"，原样交给视觉模型
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in IMAGE_EXTENSIONS or _has_image_magic(content):
        return None, content
    if ext == "pdf" or _has_pdf_magic(content):
        reader = PdfReader(BytesIO(content))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:2]).strip()
        if len(text) >= SCANNED_PAGE_MIN_CHARS:
            return text[:FRONT_MATTER_MAX_CHARS], None
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            pix = doc[0].get_pixmap(dpi=SCAN_RENDER_DPI)
            return None, pix.tobytes("png")
    raise ValueError("只支持 PDF / 图片文件（pdf、png、jpg、jpeg、gif、webp）")


def full_text(filename: str, content: bytes) -> str | None:
    """
    抽取论文全文，只处理有文字层的 PDF；扫描件 / 图片返回 None。
    - 扫描件没有可抽的文字，全文视觉转写是分钟级成本，第一版直接跳过（字段识别仍走 front_matter）
    - 超长时保留头部 60% + 尾部 40%：结论、实验不足、参考文献通常落在尾部
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext != "pdf" and not _has_pdf_magic(content):
        return None
    with pymupdf.open(stream=content, filetype="pdf") as doc:
        pages = [(page.get_text() or "").strip() for page in doc]
    text = "\n\n".join(p for p in pages if p).strip()
    if not pages or len(text) < FULL_TEXT_MIN_CHARS_PER_PAGE * len(pages):
        return None
    if len(text) > FULL_TEXT_MAX_CHARS:
        head = int(FULL_TEXT_MAX_CHARS * 0.6)
        tail = FULL_TEXT_MAX_CHARS - head
        text = text[:head] + "\n\n[中间部分过长，已省略]\n\n" + text[-tail:]
    return text
