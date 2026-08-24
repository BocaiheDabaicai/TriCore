# 文件解析服务 —— 把上传的文件解析成纯文本
# 支持：txt / md / pdf / docx，其他类型报错拒绝

from io import BytesIO

from pypdf import PdfReader
from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

# 允许上传的扩展名（.lower() 后匹配）
SUPPORTED_EXTENSIONS = {"txt", "md", "pdf", "docx"}


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

    return parse_docx(content)


def parse_pdf(content: bytes) -> str:
    """PDF → 逐页提取文字拼接"""
    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


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
