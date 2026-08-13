from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import SessionLocal
from models.document import Document

router = APIRouter(prefix="/api/v1/document", tags=["文档问答"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AskRequest(BaseModel):
    question: str
    doc_id: int | None = None


class DocCreate(BaseModel):
    """创建文档时提交的数据"""
    title: str
    category: str
    content: str


class DocUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    content: str | None = None


# ---- 接口 ----

@router.get("/list")
def list_docs(
        keyword: str = Query(default=""),
        category: str = Query(default=""),
        db: Session = Depends(get_db),
):
    query = db.query(Document)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            Document.title.like(like) | Document.content.like(like)
        )
    if category:
        query = query.filter(Document.category == category)

    docs = query.all()
    return {
        "total": len(docs),
        "data": [{"id": d.id, "title": d.title, "category": d.category, "content": d.content} for d in docs],
    }


@router.get("/{doc_id}")
def get_doc(doc_id: int, db: Session = Depends(get_db)):
    d = db.query(Document).filter(Document.id == doc_id).first()
    if not d:
        return {"data": None, "message": "文档不存在"}
    return {"data": {"id": d.id, "title": d.title, "category": d.category, "content": d.content}}


@router.post("/create")
def create_doc(req: DocCreate, db: Session = Depends(get_db)):
    doc = Document(title=req.title, category=req.category, content=req.content)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"message": "创建成功", "data": {"id": doc.id, "title": doc.title}}


@router.post("/ask")
def ask_document(req: AskRequest, db: Session = Depends(get_db)):
    query = db.query(Document)
    if req.doc_id:
        query = query.filter(Document.id == req.doc_id)

    docs = query.all()

    matched = []
    for d in docs:
        for word in req.question:
            if word in d.content:
                matched.append(d)
                break

    if matched:
        answer = f"根据文档「{matched[0].title}」：{matched[0].content}"
    else:
        answer = "未找到相关内容，请换个问题试试。"

    return {
        "question": req.question,
        "answer": answer,
        "sources": [{"id": d.id, "title": d.title} for d in matched],
    }


# ---- 改 ----
@router.put("/{doc_id}")
def update_doc(doc_id: int, req: DocUpdate, db: Session = Depends(get_db)):
    p = db.query(Document).filter(Document.id == doc_id).first()

    if not p:
        return {"message": "文档不存在", "data": None}

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
@router.delete("/{doc_id}")
def delete_doc(doc_id: int, db: Session = Depends(get_db)):
    p = db.query(Document).filter(Document.id == doc_id).first()

    if not p:
        return {"message": "文档不存在", "data": None}

    db.delete(p)
    db.commit()
    return {"message": "删除成功", "data": {"id": doc_id}}
