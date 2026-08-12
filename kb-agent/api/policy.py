from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.policy import Policy

router = APIRouter(prefix="/api/v1/policy", tags=["制度查询"])


# ---- 【新概念】依赖注入：获取数据库会话 ----
# FastAPI 的 Depends 会帮你调用这个函数，拿到 db 对象
# 路由函数声明 db: Session = Depends(get_db) 就能直接用
def get_db():
    db = SessionLocal()   # 开启一个数据库连接
    try:
        yield db           # 把连接交给路由函数去用
    finally:
        db.close()         # 请求结束后自动关闭，防止连接泄漏


# ---- 接口 ----

@router.get("/list")
def list_policies(
    keyword: str = Query(default="", description="按标题/内容搜索"),
    category: str = Query(default="", description="按分类过滤"),
    db: Session = Depends(get_db),           # ← 注入数据库连接
):
    """
    从数据库查询制度列表
    之前是硬编码 list，现在变成真实的 SQL 查询
    """
    # 构建查询
    query = db.query(Policy)

    if keyword:
        # LIKE 模糊搜索：标题或内容包含关键字
        like_pattern = f"%{keyword}%"
        query = query.filter(
            Policy.title.like(like_pattern) | Policy.content.like(like_pattern)
        )

    if category:
        query = query.filter(Policy.category == category)

    policies = query.all()

    # 把 ORM 对象转成字典返回
    return {
        "total": len(policies),
        "data": [
            {"id": p.id, "title": p.title, "category": p.category, "content": p.content}
            for p in policies
        ],
    }


@router.get("/{policy_id}")
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """根据ID查一条制度"""
    p = db.query(Policy).filter(Policy.id == policy_id).first()
    if not p:
        return {"data": None, "message": "制度不存在"}
    return {"data": {"id": p.id, "title": p.title, "category": p.category, "content": p.content}}


@router.post("/create")
def create_policy(title: str, category: str, content: str, db: Session = Depends(get_db)):
    """
    【新接口】创建一条制度
    参数通过 URL 传递：POST /api/v1/policy/create?title=xxx&category=xxx&content=xxx
    （后面会改成用请求体传参）
    """
    new_policy = Policy(title=title, category=category, content=content)
    db.add(new_policy)    # 加入待保存列表
    db.commit()            # 真正写入数据库
    db.refresh(new_policy) # 刷新一下，拿到数据库自动生成的 id
    return {"message": "创建成功", "data": {"id": new_policy.id, "title": new_policy.title}}
