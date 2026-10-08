# 统计接口 —— 给管理端「数据」视角报几个数字
# 为什么不复用各服务自己的接口：数据视角要的是"一行拿全"，多一次往返也没什么成本，
# 但这个服务的数据就是两个计数，单独开一个接口最直白

from fastapi import APIRouter

from core.config import SHOTS_DIR
from core.database import SessionLocal
from models.run import Run, UnitMeta

router = APIRouter(prefix="/api/v1/stats", tags=["统计"])


@router.get("")
def stats():
    db = SessionLocal()
    try:
        runs = db.query(Run).count()
        verified = db.query(UnitMeta).filter(UnitMeta.verified == 1).count()
    finally:
        db.close()
    shots = len([p for p in SHOTS_DIR.glob("*") if p.is_file()])
    return {"message": "ok", "data": {"runs": runs, "verified_units": verified, "shots": shots}}
