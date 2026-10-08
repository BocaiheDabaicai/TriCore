# 文件解析服务 —— 把上传的文件解析成纯文本
# 支持：txt / md / pdf / docx / 图片（png、jpg、jpeg、webp），其他类型报错拒绝
# 两类文件各有两条路：
#   文本类（txt/md/docx、有文字层的 PDF）→ 直接解析，免费且零误差
#   图片类（扫描件、截图、无文字层的 PDF 页）→ 渲染成图交给大模型"看图转写"（视觉转写）

from io import BytesIO

import pymupdf
from pypdf import PdfReader
from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

from services.llm_service import is_configured as llm_is_configured, transcribe_images

# 允许上传的扩展名（.lower() 后匹配）
SUPPORTED_EXTENSIONS = {"txt", "md", "pdf", "docx", "png", "jpg", "jpeg", "webp"}

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# 扫描页判定阈值：一页正常文字量远超这个数，低于它就说明这页没有文字层（扫描件、纯图片页）
SCANNED_PAGE_MIN_CHARS = 50

# 渲染 DPI：150 对中文印刷体够清楚；再高只是徒增图片体积和视觉调用的 token
SCAN_RENDER_DPI = 150


def parse_file(filename: str, content: bytes) -> str:
    """按扩展名分发到对应解析器，返回纯文本"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型 .{ext}，支持：{'、'.join(sorted(SUPPORTED_EXTENSIONS))}")

    if ext in ("txt", "md"):
        # 纯文本：直接解码（非法字符忽略，避免个别编码问题导致整个文件失败）
        return content.decode("utf-8", errors="ignore")

    if ext == "pdf":
        return parse_pdf(content)

    if ext in IMAGE_EXTENSIONS:
        return parse_image(content)

    return parse_docx(content)


def parse_pdf(content: bytes) -> str:
    """
    PDF → 文字。逐页判断有没有"文字层"，两种页两种取法：
    - 有文字层（正常文本 PDF）：pypdf 直接取字——免费，且原文照抄不会有转写误差
    - 没有文字层（扫描件、图片页）：PyMuPDF 渲染成图 → 视觉转写
    取到的文字按原页码顺序拼回一篇；LLM 未配置时扫描页只能留空（不阻断解析）
    """
    reader = PdfReader(BytesIO(content))
    page_texts = [page.extract_text() or "" for page in reader.pages]

    scanned = [i for i, t in enumerate(page_texts) if len(t.strip()) < SCANNED_PAGE_MIN_CHARS]
    if not scanned or not llm_is_configured():
        return "\n".join(page_texts).strip()

    print(f"提示：检测到 {len(scanned)} 个扫描页（无文字层），走视觉转写：第 {[i + 1 for i in scanned]} 页")
    rendered = render_pdf_pages(content, scanned)

    # 相邻的扫描页合并成一批转写（一次请求带多张图；transcribe_images 内部还会再分批）
    for run in group_consecutive(scanned):
        page_texts[run[0]] = transcribe_images([rendered[i] for i in run], start_page=run[0] + 1)
        for i in run[1:]:
            page_texts[i] = ""   # 这些页的文字已并入整批转写结果，避免重复输出

    final = "\n".join(t for t in page_texts if t.strip()).strip()
    if not has_real_content(final):
        # 整篇都是"（第 N 页视觉转写失败）"占位：这文件等于没解析出内容，别当知识入库
        raise ValueError("扫描页识别失败（没取到文字），请确认扫描件清晰完整后重试")
    return final


def parse_image(content: bytes) -> str:
    """图片文件（扫描件、截图）→ 视觉转写（模型只认图片，这类文件本来就没有文字层可取）"""
    if not llm_is_configured():
        raise ValueError("图片需要大模型视觉转写才能入库，请先在 .env 配置 LLM")
    text = transcribe_images([content], start_page=1)
    if not has_real_content(text):
        raise ValueError("图片识别失败（没取到文字），请确认图片清晰、包含文字")
    return text


def has_real_content(text: str) -> bool:
    """
    排除页标记（===第N页===）和失败占位后，还剩不剩真实文字
    用途：整篇都转写失败时不能把占位提示当正文入库
    """
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("==="):
            continue
        if line.startswith("（第") and "转写" in line:
            continue
        return True
    return False


def render_pdf_pages(content: bytes, pages: list[int]) -> dict[int, bytes]:
    """
    指定页 → PNG 图片字节（视觉转写的第一步：模型收的是图片，不是 PDF）
    - pages 是 0 开始的页下标，返回值以同样下标为键
    """
    result = {}
    with pymupdf.open(stream=content, filetype="pdf") as doc:
        for i in pages:
            pix = doc[i].get_pixmap(dpi=SCAN_RENDER_DPI)
            result[i] = pix.tobytes("png")
    return result


def group_consecutive(indexes: list[int]) -> list[list[int]]:
    """把 [1,2,3,7,8] 分成 [[1,2,3],[7,8]]——只有相邻页才适合合并成一批转写"""
    runs = []
    for i in indexes:
        if runs and i == runs[-1][-1] + 1:
            runs[-1].append(i)
        else:
            runs.append([i])
    return runs


def parse_docx(content: bytes) -> str:
    """
    Word → 纯文本，按文档顺序提取段落和表格
    - 只用 doc.paragraphs 会漏掉表格里的内容（制度文件常把收费标准、申请单做成表格）
    - docx 内部是一个"块"列表（段落块/表格块交替出现），按顺序遍历才能保持原文顺序
    """
    doc = DocxDocument(BytesIO(content))
    parts = []
    for block in iter_blocks(doc):
        if isinstance(block, Paragraph):
            if block.text.strip():
                parts.append(block.text.strip())
        else:
            table_text = table_to_text(block)
            if table_text:
                parts.append(table_text)
    return "\n".join(parts).strip()


def iter_blocks(doc: DocxDocument):
    """
    按文档顺序产出段落和表格
    doc.element.body 是 docx 的底层 XML，子元素里 w:p 是段落、w:tbl 是表格，
    遍历时用对应类包装，就能用 python-docx 的 API 读内容
    """
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def table_to_text(table: Table) -> str:
    """
    表格 → 文本：每行一条，单元格用 | 分隔
    合并单元格去重：docx 里一个合并单元格在每个被合并的位置都重复出现，
    所以相邻重复的文字只保留一次（正常表格里相邻两格恰好同文字的情况极少，可接受）
    """
    lines = []
    for row in table.rows:
        cells = []
        prev = None
        for cell in row.cells:
            text = cell.text.strip().replace("\n", " ")
            if not text or text == prev:
                continue
            cells.append(text)
            prev = text
        if cells:
            lines.append(" | ".join(cells))
    return "\n".join(lines)
