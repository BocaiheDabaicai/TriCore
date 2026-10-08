# 截图接口 —— 操作台上的"截图资料库"
#
# 为什么单独做这么一块：写单元（RPA 脚本）之前必须看清目标页面长什么样。
# 用户把金蝶 / OA 的页面截图传上来，AI 读磁盘上的这些图来认清字段与按钮，再写选择器；
# 将来定位失败时，这些图也是"视觉兜底"的素材。所以按资料库来管，不只是临时存一下。

from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from core.config import SHOTS_DIR

router = APIRouter(prefix="/api/v1/shots", tags=["截图资料库"])

ALLOWED_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def _safe_name(name: str) -> str:
    """只取文件名部分，去掉任何目录成分（防目录穿越）"""
    return name.replace("\\", "/").split("/")[-1]


def _shot_list() -> list[dict]:
    items = []
    for p in sorted(SHOTS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_file():
            continue
        items.append({
            "name": p.name,
            "size": p.stat().st_size,
            "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"/api/v1/shots/file/{p.name}",
        })
    return items


@router.get("")
def list_shots():
    return {"message": "ok", "data": _shot_list()}


@router.post("")
def upload_shot(file: UploadFile = File(...)):
    """上传一张页面截图（文件名前加时间戳，避免重名覆盖，也便于按时间找）"""
    name = _safe_name(file.filename or "shot.png")
    suffix = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
    if suffix not in ALLOWED_SUFFIX:
        raise HTTPException(status_code=400,
                            detail=f"只支持图片：{'、'.join(sorted(ALLOWED_SUFFIX))}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = SHOTS_DIR / f"{stamp}_{name}"
    target.write_bytes(file.file.read())
    return {"message": "上传成功", "data": {"name": target.name, "size": target.stat().st_size}}


@router.get("/file/{name}")
def get_shot(name: str):
    path = SHOTS_DIR / _safe_name(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="截图不存在")
    return FileResponse(path)


@router.delete("/file/{name}")
def delete_shot(name: str):
    path = SHOTS_DIR / _safe_name(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="截图不存在")
    path.unlink()
    return {"message": "已删除", "data": {"name": name}}
