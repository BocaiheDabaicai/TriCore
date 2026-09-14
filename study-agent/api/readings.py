# 研读记录接口 —— 返回结构与前端数据层约定一致：{ message, data }（列表多一个 total）

import re
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from models.reading import Reading

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
