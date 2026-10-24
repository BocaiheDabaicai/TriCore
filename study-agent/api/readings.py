# 研读记录接口 —— 返回结构与前端数据层约定一致：{ message, data }（列表多一个 total）

import re
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from models.reading import Reading
from services import file_parser, llm_service

router = APIRouter(prefix="/api/readings", tags=["研读记录"])

# 附件目录（启动目录 = study-agent/，要在 study-agent 下启动服务）
UPLOAD_DIR = Path("uploads")

# 允许的附件类型：论文 PDF + 截图图片
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"}

# 导出时用的中文显示名（未知值原样输出）
MODE_TEXT = {"close": "精读", "skim": "泛读"}
LANG_TEXT = {"zh": "中文", "en": "英文"}


def _row_dict(r: Reading) -> dict:
    # 时间统一转成字符串再返回，与前端契约保持一致（前端直接显示，不做格式化）
    return {
        "id": r.id,
        "title": r.title,
        "mode": r.mode,
        "lang": r.lang or "zh",
        "tag": r.tag,
        "rating": r.rating or 0,
        "domains": r.domains or [],
        "author": r.author,
        "published": r.published,
        "journal": r.journal,
        "note": r.note,
        "attachment": r.attachment,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _clean_rating(value) -> int:
    # 评分只收 0-10 的整数，超出范围夹回来
    return max(0, min(10, int(value or 0)))


def _clean_lang(value) -> str:
    # 语言只认 zh / en，其它一律按中文（前端只发这两个值）
    return value if value in ("zh", "en") else "zh"


def _clean_domains(domains) -> list[str]:
    # 去空白、去重、最多 3 个
    out: list[str] = []
    for d in domains or []:
        d = str(d).strip()
        if d and d not in out:
            out.append(d)
    return out[:3]


def _parse_export_ids(raw: str | None) -> list[int] | None:
    """解析逗号分隔的记录 id；None = 没传 ids（导出全部）。
    显式传了 ids 却解析不出有效值（如 ?ids=）要报错，不能悄悄导出全部。"""
    if raw is None:
        return None
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = int(part)
        except ValueError:
            raise HTTPException(400, "ids 参数格式不正确")
        if value <= 0:
            raise HTTPException(400, "ids 参数格式不正确")
        if value not in ids:
            ids.append(value)
    if not ids:
        raise HTTPException(400, "请选择要导出的记录")
    return ids


def _md_meta(value) -> str:
    """Markdown 元数据值：压成单行、空值用 —（笔记正文不要走这里）"""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or "—"


def _safe_md_filename(title: str, fallback: str) -> str:
    """清洗 Windows 非法字符；数字前缀由调用方加，重名与保留设备名都不怕"""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (title or "").strip())
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        name = fallback
    return name[:80].strip(" .") or fallback


def _reading_markdown(data: dict) -> str:
    """一条记录的完整 Markdown：全部元数据 + 原始笔记（不截断、不改标题层级）"""
    title = _md_meta(data.get("title"))
    if title == "—":
        title = "未命名文献"
    mode = MODE_TEXT.get(data.get("mode"), data.get("mode") or "—")
    lang = LANG_TEXT.get(data.get("lang"), data.get("lang") or "—")
    rating = f"{data['rating']}/10" if data.get("rating") else "未评分"
    domains = "、".join(data.get("domains") or []) or "—"
    note = data.get("note") or ""

    lines = [
        f"# {title}",
        "",
        f"- 阅读模式：{mode}",
        f"- 语言：{lang}",
        f"- 标签：{_md_meta(data.get('tag'))}",
        f"- 评分：{rating}",
        f"- 领域：{domains}",
        f"- 作者：{_md_meta(data.get('author'))}",
        f"- 出版时间：{_md_meta(data.get('published'))}",
        f"- 期刊：{_md_meta(data.get('journal'))}",
        f"- 附件：{_md_meta(data.get('attachment'))}",
        f"- 创建时间：{_md_meta(data.get('created_at'))}",
        f"- 更新时间：{_md_meta(data.get('updated_at'))}",
        "",
        "---",
        "",
        "## 笔记",
        "",
        note if note.strip() else "—",
    ]
    text = "\n".join(lines)
    return text if text.endswith("\n") else text + "\n"


def _build_export_zip(rows: list[Reading]) -> bytes:
    """每条记录一个 .md，内存打包（35 条笔记很小，不需要临时文件）"""
    width = max(2, len(str(len(rows))))
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as zf:
        for i, row in enumerate(rows, start=1):
            data = _row_dict(row)
            name = f"{i:0{width}d}-{_safe_md_filename(data['title'], f'记录-{row.id}')}.md"
            zf.writestr(name, _reading_markdown(data).encode("utf-8"))
    return buf.getvalue()


class ReadingCreate(BaseModel):
    title: str = ""
    mode: str = "close"
    lang: str = "zh"
    tag: str = ""
    rating: int = 0
    domains: list[str] = []
    author: str = ""
    published: str = ""
    journal: str = ""
    note: str = ""


class ReadingUpdate(BaseModel):
    title: str | None = None
    mode: str | None = None
    lang: str | None = None
    tag: str | None = None
    rating: int | None = None
    domains: list[str] | None = None
    author: str | None = None
    published: str | None = None
    journal: str | None = None
    note: str | None = None


@router.get("")
def list_readings(db: Session = Depends(get_db)):
    rows = db.query(Reading).order_by(Reading.updated_at.desc()).all()
    data = [_row_dict(r) for r in rows]
    return {"message": "ok", "total": len(data), "data": data}


@router.post("/extract")
def extract_fields(
    file: UploadFile | None = File(None),
    reading_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """AI 识别文献信息（语言/标题/作者/出版时间/期刊/标签）——传新文件或已有记录的附件都行。
    同步 def：解析与模型调用都是阻塞操作，交给 FastAPI 线程池，避免冻住事件循环（kb-agent 踩过的坑）。
    任何失败都返回 200 + data:null（附一句 message），不阻断手动填写流程。"""
    if not llm_service.is_configured():
        return {"message": "未配置 LLM（study-agent/.env），跳过自动识别", "data": None}

    if file is not None:
        filename = file.filename or "file"
        content = file.file.read()
    elif reading_id is not None:
        row = db.get(Reading, reading_id)
        if not row or not row.attachment:
            return {"message": "该记录没有附件", "data": None}
        path = UPLOAD_DIR / f"{reading_id}_{row.attachment}"
        if not path.exists():
            return {"message": "附件文件不存在", "data": None}
        filename, content = row.attachment, path.read_bytes()
    else:
        raise HTTPException(400, "需要上传文件或指定 reading_id")

    try:
        text, image = file_parser.front_matter(filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        return {"message": "文件解析失败，跳过自动识别", "data": None}

    # 标签候选：已有记录用过的标签（模型优先从这里挑，保持标签体系不膨胀）
    tag_candidates = [t for (t,) in db.query(Reading.tag).distinct() if t]
    result = llm_service.extract_fields(
        text=text, image=image, filename=filename, tag_candidates=tag_candidates
    )
    if not result:
        return {"message": "AI 识别失败，可手动填写", "data": None}
    return {"message": "ok", "data": result}


@router.get("/export")
def export_readings(
    ids: str | None = Query(None, description="逗号分隔的记录 ID；不传导出全部"),
    db: Session = Depends(get_db),
):
    """批量导出：每条记录一个 Markdown，打包成 ZIP（完整元数据 + 原始笔记；附件原文件不打包）。
    同步 def：SQLite 查询与内存打包都是阻塞操作，交给 FastAPI 线程池。"""
    id_list = _parse_export_ids(ids)
    if id_list is None:
        # 与列表一致：最近更新的在前
        rows = db.query(Reading).order_by(Reading.updated_at.desc(), Reading.id.desc()).all()
    else:
        found = db.query(Reading).filter(Reading.id.in_(id_list)).all()
        by_id = {r.id: r for r in found}
        # 按请求顺序输出，ZIP 里的 01、02 与页面上的选择顺序一致；缺失的 id 跳过
        rows = [by_id[i] for i in id_list if i in by_id]
    if not rows:
        raise HTTPException(404, "没有可导出的记录")

    content = _build_export_zip(rows)
    day = datetime.now().strftime("%Y-%m-%d")
    ascii_name = f"readings-{day}.zip"
    cn_name = f"研读回顾-{day}.zip"
    # 响应头只能是 latin-1：中文名放 RFC 5987 的 filename*，filename= 留 ASCII 兜底
    headers = {
        "Content-Disposition": (
            f'attachment; filename="{ascii_name}"; '
            f"filename*=UTF-8''{quote(cn_name, safe='')}"
        )
    }
    return Response(content=content, media_type="application/zip", headers=headers)


@router.get("/{reading_id}")
def get_reading(reading_id: int, db: Session = Depends(get_db)):
    row = db.get(Reading, reading_id)
    if not row:
        # 与前端静态阶段的行为保持一致：200 + data 为 null，页面逻辑零改动
        return {"message": "记录不存在", "data": None}
    return {"message": "ok", "data": _row_dict(row)}


@router.post("")
def create_reading(payload: ReadingCreate, db: Session = Depends(get_db)):
    row = Reading(
        title=payload.title.strip() or "未命名文献",
        mode=payload.mode,
        lang=_clean_lang(payload.lang),
        tag=payload.tag.strip(),
        rating=_clean_rating(payload.rating),
        domains=_clean_domains(payload.domains),
        author=payload.author.strip(),
        published=payload.published.strip(),
        journal=payload.journal.strip(),
        note=payload.note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"message": "已创建", "data": _row_dict(row)}


@router.put("/{reading_id}")
def update_reading(reading_id: int, payload: ReadingUpdate, db: Session = Depends(get_db)):
    row = db.get(Reading, reading_id)
    if not row:
        return {"message": "记录不存在", "data": None}
    data = payload.model_dump(exclude_unset=True)
    if data.get("rating") is not None:
        data["rating"] = _clean_rating(data["rating"])
    if data.get("lang") is not None:
        data["lang"] = _clean_lang(data["lang"])
    if data.get("domains") is not None:
        data["domains"] = _clean_domains(data["domains"])
    for field, value in data.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return {"message": "已保存", "data": _row_dict(row)}


@router.get("/{reading_id}/attachment")
def download_attachment(reading_id: int, db: Session = Depends(get_db)):
    row = db.get(Reading, reading_id)
    if not row or not row.attachment:
        raise HTTPException(404, "该记录没有附件")
    file_path = UPLOAD_DIR / f"{reading_id}_{row.attachment}"
    if not file_path.exists():
        raise HTTPException(404, "附件文件不存在")
    # 不传 filename → 浏览器内直接打开（PDF 阅读器 / 图片），而不是下载
    return FileResponse(file_path)


@router.post("/{reading_id}/attachment")
def upload_attachment(reading_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    row = db.get(Reading, reading_id)
    if not row:
        return {"message": "记录不存在", "data": None}

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(400, "只支持 PDF / 图片文件（pdf、png、jpg、jpeg、gif、webp）")

    # 只留文件名、去掉路径分隔符和 Windows 非法字符，防止写到目录外
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", Path(file.filename).name).strip() or "file" + suffix

    # 换新附件时先删旧文件，避免残留
    if row.attachment:
        old = UPLOAD_DIR / f"{reading_id}_{row.attachment}"
        if old.exists():
            old.unlink()

    UPLOAD_DIR.mkdir(exist_ok=True)
    target = UPLOAD_DIR / f"{reading_id}_{safe_name}"
    with target.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    row.attachment = safe_name
    db.commit()
    db.refresh(row)
    return {"message": "已上传", "data": _row_dict(row)}


@router.delete("/{reading_id}")
def delete_reading(reading_id: int, db: Session = Depends(get_db)):
    row = db.get(Reading, reading_id)
    if not row:
        return {"message": "记录不存在", "data": None}
    # 记录删了附件也一起删，不留孤儿文件
    if row.attachment:
        f = UPLOAD_DIR / f"{reading_id}_{row.attachment}"
        if f.exists():
            f.unlink()
    db.delete(row)
    db.commit()
    return {"message": "已删除", "data": None}
