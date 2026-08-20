from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from core.database import SessionLocal
from models.document import Document
from models.policy import Policy
from models.message import Message
from models.vector import KnowledgeVector
from services.llm_service import is_configured, chat_with_context, chat_with_history
from services.embedding_service import (
    is_configured as embed_is_configured,
    retrieve_top_k,
    rebuild_index,
    sync_vector,
    delete_vector,
)

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
    session_id: str | None = None   # 可选：带上它才能延续之前的对话


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

    # 同步向量索引：不调这行，新文档要等手动 /reindex 才能被检索到
    sync_vector(db, "document", doc.id, doc.title, doc.content)

    return {"message": "创建成功", "data": {"id": doc.id, "title": doc.title}}


@router.post("/ask")
def ask_document(req: AskRequest, db: Session = Depends(get_db)):
    """文档问答 —— RAG + 多轮对话记忆"""
    # 生成/沿用会话ID：不传就新建一个
    session_id = req.session_id or f"session-{uuid.uuid4().hex[:12]}"

    # ---- 第零步：先加载历史（检索和回答都要用）----
    history = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(10)
        .all()
    )

    # 统一检索范围：文档 + 制度 两张表都搜
    # 用户不知道也不关心信息在哪个表里，全部一起找
    query = db.query(Document)
    if req.doc_id:
        query = query.filter(Document.id == req.doc_id)
    docs = query.all()
    policies = db.query(Policy).all()

    # ---- 第一步：检索（Retrieval）----
    # 检索词 = 当前问题 + 上一轮用户的问题
    # 解决"那超过5000呢？"这类依赖上文的提问检索不到资料的问题
    search_text = req.question
    last_user_msgs = [m for m in history if m.role == "user"]
    if last_user_msgs:
        search_text = f"{req.question} {last_user_msgs[-1].content}"

    # 【AI 检索】向量语义检索 —— 优先使用
    # 配置了 embedding 且索引非空时，按语义相似度找资料
    if embed_is_configured():
        index_count = db.query(KnowledgeVector).count()
        if index_count > 0:
            matched = retrieve_top_k(db, search_text, k=3)
            retrieval_method = "embedding"
        else:
            matched = []
            retrieval_method = "empty_index"
    else:
        matched = []
        retrieval_method = "char_score"

    # 【降级检索】字符打分 —— embedding 不可用时的备用方案
    if retrieval_method != "embedding":
        def score_item(content: str) -> int:
            unique_chars = set(search_text)
            return sum(1 for ch in unique_chars if ch in content)

        candidates = []
        for d in docs:
            s = score_item(d.content)
            if s > 0:
                candidates.append((s, "document", d.id, d.title, d.content))
        for p in policies:
            s = score_item(p.content)
            if s > 0:
                candidates.append((s, "policy", p.id, p.title, p.content))

        candidates.sort(key=lambda x: x[0], reverse=True)
        top = candidates[:3]
        matched = [{"type": t, "id": cid, "title": title, "content": content}
                   for _, t, cid, title, content in top]

    if not matched:
        return {
            "question": req.question,
            "answer": "未找到相关内容，请换个问题试试。",
            "sources": [],
            "session_id": session_id,
        }

    # ---- 第二步+第三步：增强 + 生成 ----
    context = "\n\n".join(
        f"【{m['title']}】{m['content']}" for m in matched
    )

    if is_configured():
        history_dicts = [{"role": m.role, "content": m.content} for m in history]

        if history_dicts:
            answer = chat_with_history(req.question, context, history_dicts)
        else:
            answer = chat_with_context(req.question, context)
        source_name = "LLM"
    else:
        answer = f"根据「{matched[0]['title']}」：{matched[0]['content']}"
        source_name = "keyword"

    # 保存这轮对话
    db.add(Message(session_id=session_id, role="user", content=req.question))
    db.add(Message(session_id=session_id, role="assistant", content=answer))
    db.commit()

    # 同一条知识可能命中多个块，sources 按 (type, id) 去重，避免来源列表重复
    seen = set()
    sources = []
    for m in matched:
        key = (m["type"], m["id"])
        if key not in seen:
            seen.add(key)
            sources.append({"type": m["type"], "id": m["id"], "title": m["title"]})

    return {
        "question": req.question,
        "answer": answer,
        "answer_source": source_name,
        "retrieval_method": retrieval_method,   # 标明这次检索用的是哪种方式
        "sources": sources,
        "session_id": session_id,
    }


@router.post("/reindex")
def reindex_knowledge(db: Session = Depends(get_db)):
    """
    全量重建向量索引：把制度表 + 文档表 + 流程模板全部内容重新向量化
    - 日常增删改知识已自动同步索引，一般不需要手动调用
    - 此接口用于：首次建索引 / 怀疑索引和数据不一致时兜底修复
    - 返回索引条数
    """
    if not embed_is_configured():
        return {"message": "未配置 Embedding 服务，请在 .env 中填写", "data": None}

    count = rebuild_index(db)
    return {"message": "向量索引重建完成", "data": {"indexed": count}}


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

    # 内容变了，向量也要跟着更新，否则检索到的还是旧内容
    sync_vector(db, "document", p.id, p.title, p.content)

    return {"message": "更新成功", "data": {"id": p.id, "title": p.title, "category": p.category}}


# ---- 删 ----
@router.delete("/{doc_id}")
def delete_doc(doc_id: int, db: Session = Depends(get_db)):
    p = db.query(Document).filter(Document.id == doc_id).first()

    if not p:
        return {"message": "文档不存在", "data": None}

    db.delete(p)
    db.commit()

    # 文档删了，索引里的向量也要删，否则会检索到"幽灵数据"
    delete_vector(db, "document", doc_id)

    return {"message": "删除成功", "data": {"id": doc_id}}
