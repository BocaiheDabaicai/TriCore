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

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def front_matter(filename: str, content: bytes) -> tuple[str | None, bytes | None]:
    """
    返回 (文字, 图片)，二选一：
    - PDF 且开头有文字层 → 前两页文字
    - PDF 没有文字层（扫描件）→ 首页渲染成 PNG
    - 图片文件 → 本身就是"没有文字层的页"，原样交给视觉模型
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in IMAGE_EXTENSIONS:
        return None, content
    if ext == "pdf":
        reader = PdfReader(BytesIO(content))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:2]).strip()
        if len(text) >= SCANNED_PAGE_MIN_CHARS:
            return text[:FRONT_MATTER_MAX_CHARS], None
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            pix = doc[0].get_pixmap(dpi=SCAN_RENDER_DPI)
            return None, pix.tobytes("png")
    raise ValueError("只支持 PDF / 图片文件（pdf、png、jpg、jpeg、gif、webp）")
