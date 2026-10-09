# 研读记录接口 —— 返回结构与前端数据层约定一致：{ message, data }（列表多一个 total）

import re
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
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
