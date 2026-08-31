# 未命中问题接口 —— 知识库没答上的问题清单（管理员用）
# 独立路由组 /api/v1/missed：不放在 /api/v1/knowledge 下，
# 因为 knowledge 有 GET/DELETE /{item_id} 路由，/missed 会被它抢先匹配（"missed" 转不成 int → 422）

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.missed import MissedQuestion

router = APIRouter(prefix="/api/v1/missed", tags=["未命中问题"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_missed(
    limit: int = Query(default=50, ge=1, le=500, description="最多返回条数"),
    db: Session = Depends(get_db),
):
    """未命中问题清单：按被问次数排序，次数高 = 最该优先补充的知识"""
    items = (
        db.query(MissedQuestion)
        .order_by(MissedQuestion.count.desc(), MissedQuestion.last_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "total": len(items),
        "data": [
            {
                "id": m.id,
                "question": m.question,
                "count": m.count,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "last_at": m.last_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for m in items
        ],
    }


@router.delete("")
def clear_missed(db: Session = Depends(get_db)):
    """清空全部记录（批量补充完知识后一次性清理用）"""
    n = db.query(MissedQuestion).delete()
    db.commit()
    return {"message": f"已清空 {n} 条未命中记录", "data": {"deleted": n}}


@router.delete("/{missed_id}")
def delete_missed(missed_id: int, db: Session = Depends(get_db)):
    """删除一条记录（对应知识已补充后）"""
    row = db.query(MissedQuestion).filter(MissedQuestion.id == missed_id).first()
    if not row:
        return {"message": "记录不存在", "data": None}
    db.delete(row)
    db.commit()
    return {"message": "删除成功", "data": {"id": missed_id}}
