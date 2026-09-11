# 寻文（文献站点）接口 + 首次启动的种子数据
# 种子内容 = paper.md 记录 0003 的期刊与站点清单（表为空时才灌入）

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import SessionLocal, get_db
from models.source import Source

router = APIRouter(prefix="/api/sources", tags=["寻文"])

SOURCE_SEED = [
    # 工程管理
    {"type": "工程管理", "name": "管理工程学报", "url": "http://glgcxb.zju.edu.cn/", "note": "中文核心 · 浙江大学主办"},
    {"type": "工程管理", "name": "工程管理学报", "url": "https://jem.hit.edu.cn/", "note": "科技核心 · 哈工大主办（泛读做三句话笔记）"},
    {"type": "工程管理", "name": "IJPM", "url": "https://www.sciencedirect.com/journal/international-journal-of-project-management", "note": "国际项目管理期刊 · Elsevier"},
    {"type": "工程管理", "name": "ECAM", "url": "https://www.emerald.com/ecam", "note": "工程建造与管理 · Emerald"},
    # AI · 计算机
    {"type": "AI·计算机", "name": "arXiv", "url": "https://arxiv.org", "note": "预印本平台"},
    {"type": "AI·计算机", "name": "ACL", "url": "https://aclanthology.org", "note": "计算语言学论文全库（ACL Anthology）"},
    {"type": "AI·计算机", "name": "CHI", "url": "https://sigchi.org", "note": "人机交互年会（SIGCHI 官网）"},
    # Web3 · 区块链
    {"type": "Web3·区块链", "name": "WWW", "url": "https://thewebconf.org/", "note": "The Web Conference（原 WWW）"},
    {"type": "Web3·区块链", "name": "HICSS", "url": "https://hicss.hawaii.edu", "note": "系统科学年会 · 区块链治理常见"},
    {"type": "Web3·区块链", "name": "MISQ", "url": "https://misq.umn.edu/misq", "note": "管理信息系统顶刊"},
    {"type": "Web3·区块链", "name": "arXiv · cs.CR", "url": "https://arxiv.org/list/cs.CR/recent", "note": "密码学与安全最新预印本"},
]


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(Source).count() == 0:
            db.add_all([Source(**item) for item in SOURCE_SEED])
            db.commit()
    finally:
        db.close()


@router.get("")
def list_sources(db: Session = Depends(get_db)):
    rows = db.query(Source).order_by(Source.id).all()
    data = [
        {"id": r.id, "type": r.type, "name": r.name, "url": r.url, "note": r.note}
        for r in rows
    ]
    return {"message": "ok", "total": len(data), "data": data}
