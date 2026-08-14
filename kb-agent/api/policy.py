from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import SessionLocal
from models.policy import Policy
from services.llm_service import is_configured, chat_with_context

router = APIRouter(prefix="/api/v1/policy", tags=["制度查询"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---- 请求体模型 ----

class PolicyCreate(BaseModel):
    """创建制度时提交的数据"""
    title: str
    category: str
    content: str


class PolicyUpdate(BaseModel):
    """更新制度时提交的数据 —— 三个字段都可选，传哪个改哪个"""
    title: str | None = None
    category: str | None = None
    content: str | None = None


class PolicyAsk(BaseModel):
    """制度问答请求"""
    question: str


# ---- 查 ----

@router.get("/list")
def list_policies(
    keyword: str = Query(default="", description="按标题/内容搜索"),
    category: str = Query(default="", description="按分类过滤"),
    db: Session = Depends(get_db),
):
    query = db.query(Policy)
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            Policy.title.like(like_pattern) | Policy.content.like(like_pattern)
        )
    if category:
        query = query.filter(Policy.category == category)

    policies = query.all()
    return {
        "total": len(policies),
        "data": [
            {"id": p.id, "title": p.title, "category": p.category, "content": p.content}
            for p in policies
        ],
    }


@router.get("/{policy_id}")
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    p = db.query(Policy).filter(Policy.id == policy_id).first()
    if not p:
        return {"data": None, "message": "制度不存在"}
    return {"data": {"id": p.id, "title": p.title, "category": p.category, "content": p.content}}


# ---- 增 ----

@router.post("/create")
def create_policy(req: PolicyCreate, db: Session = Depends(get_db)):
    """
    创建一条制度
    请求体 JSON：{"title": "xxx", "category": "xxx", "content": "xxx"}
    """
    new_policy = Policy(title=req.title, category=req.category, content=req.content)
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return {"message": "创建成功", "data": {"id": new_policy.id, "title": new_policy.title}}


# ---- 改 ----

@router.put("/{policy_id}")
def update_policy(policy_id: int, req: PolicyUpdate, db: Session = Depends(get_db)):
    """
    更新一条制度
    - 只传需要修改的字段，没传的保持原样
    - 例：{"title": "新标题"} 就只改标题
    """
    p = db.query(Policy).filter(Policy.id == policy_id).first()
    if not p:
        return {"message": "制度不存在", "data": None}

    # 逐个字段判断：传了才改（避免把没传的字段覆盖成 None）
    if req.title is not None:
        p.title = req.title
    if req.category is not None:
        p.category = req.category
    if req.content is not None:
        p.content = req.content

    db.commit()
    db.refresh(p)
    return {"message": "更新成功", "data": {"id": p.id, "title": p.title, "category": p.category}}


# ---- 删 ----

@router.delete("/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    """
    删除一条制度
    - db.delete() 只是标记删除，db.commit() 才真正删掉
    """
    p = db.query(Policy).filter(Policy.id == policy_id).first()
    if not p:
        return {"message": "制度不存在", "data": None}

    db.delete(p)
    db.commit()
    return {"message": "删除成功", "data": {"id": policy_id}}


# ---- 问答 ----

@router.post("/ask")
def ask_policy(req: PolicyAsk, db: Session = Depends(get_db)):
    """制度问答 —— 和文档问答一样的 RAG 模式"""
    policies = db.query(Policy).all()

    # 第一步：检索（关键字匹配找相关制度）
    matched = []
    for p in policies:
        for word in req.question:
            if word in p.title or word in p.content:
                matched.append(p)
                break

    if not matched:
        return {
            "question": req.question,
            "answer": "未找到相关制度，请换个问题试试。",
            "sources": [],
        }

    # 第二三步：增强 + 生成
    context = "\n\n".join(
        f"【{p.title}】{p.content}" for p in matched[:3]
    )

    if is_configured():
        answer = chat_with_context(req.question, context)
        answer_source = "LLM"
    else:
        answer = f"根据制度「{matched[0].title}」：{matched[0].content}"
        answer_source = "keyword"

    return {
        "question": req.question,
        "answer": answer,
        "answer_source": answer_source,
        "sources": [{"id": p.id, "title": p.title} for p in matched],
    }
