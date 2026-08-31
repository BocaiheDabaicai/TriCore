# 统一知识接口 —— 制度/文档/流程共用一组接口
# 设计思想：用户不关心内容属于哪类，上传后由系统（LLM）识别分类，
# 分类不对也可以手动指定或事后修改

import json

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import SessionLocal
from models.knowledge import Knowledge
from services.file_parser import parse_file
from services.llm_service import is_configured, classify_upload
from services.embedding_service import (
    is_configured as embed_is_configured,
    sync_vector,
    delete_vector,
    rebuild_index,
    knowledge_index_content,
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["统一知识库"])

ALLOWED_KINDS = ("policy", "document", "workflow")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---- 请求体模型 ----

class KnowledgeCreate(BaseModel):
    """手工创建知识"""
    title: str
    category: str
    kind: str
    content: str
    steps: list[dict] | None = None   # 仅 workflow 使用：[{"order":1,"name":"...","role":"..."}]
    keywords: str | None = None       # 可选：手动指定关键词，不传则没有（宽度回答只显示标题）


class KnowledgeUpdate(BaseModel):
    """更新知识 —— 传哪个改哪个"""
    title: str | None = None
    category: str | None = None
    kind: str | None = None
    content: str | None = None
    steps: list[dict] | None = None
    keywords: str | None = None


def item_to_dict(item: Knowledge) -> dict:
    """Knowledge 对象 → 接口返回的字典（steps_json 还原成列表）"""
    steps = None
    if item.steps_json:
        try:
            steps = json.loads(item.steps_json)
        except Exception:
            pass
    return {
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "kind": item.kind,
        "content": item.content,
        "steps": steps,
        "keywords": item.keywords,
        "filename": item.filename,
        "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def normalize_kind(kind: str | None) -> str:
    """kind 合法性校验：非法值一律按 document 处理"""
    return kind if kind in ALLOWED_KINDS else "document"


# ---- 统一上传 ----

@router.post("/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    kind: str | None = Form(default=None, description="可选：手动指定类型，不传则 LLM 自动识别"),
    category: str | None = Form(default=None, description="可选：业务分类，如 人事/财务"),
    db: Session = Depends(get_db),
):
    """
    统一上传入口：接收文件 → 解析文本 → LLM 识别类型 → 入库 → 自动分块向量化
    支持 txt / md / pdf / docx
    """
    raw = await file.read()
    try:
        text = parse_file(file.filename, raw)
    except ValueError as e:
        return {"message": str(e), "data": None}
    if not text.strip():
        return {"message": "文件内容为空，无法入库", "data": None}

    # 识别分类：统一调一次 LLM（kind/category/steps 一起拿），手动值优先覆盖
    # - 手动指定了 kind → 用值手动，title 用文件名（不依赖 LLM），但 category 仍可自动生成
    # - category 优先级：表单值 > LLM 生成 > "未分类"
    manual_kind = kind if (kind and kind in ALLOWED_KINDS) else None
    result = classify_upload(file.filename, text) if is_configured() else None

    if manual_kind:
        final_kind = manual_kind
        final_title = file.filename.rsplit(".", 1)[0]
    elif result:
        final_kind = result["kind"]
        final_title = result["title"]
    else:
        final_kind = "document"
        final_title = file.filename.rsplit(".", 1)[0]

    final_category = category or (result["category"] if result else None) or "未分类"
    steps = result["steps"] if (result and final_kind == "workflow") else None
    final_keywords = result["keywords"] if result else None

    item = Knowledge(
        title=final_title,
        category=final_category,
        kind=final_kind,
        content=text,
        steps_json=json.dumps(steps, ensure_ascii=False) if steps else None,
        keywords=final_keywords,
        filename=file.filename,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # 同步向量索引：入库即可被检索，无需手动 reindex
    sync_vector(db, item.kind, item.id, item.title, knowledge_index_content(item))

    return {"message": "上传成功", "data": item_to_dict(item)}


# ---- 查 ----

@router.get("/list")
def list_knowledge(
    keyword: str = Query(default="", description="按标题/内容搜索"),
    category: str = Query(default="", description="按业务分类过滤"),
    kind: str = Query(default="", description="按类型过滤：policy/document/workflow"),
    db: Session = Depends(get_db),
):
    query = db.query(Knowledge)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(Knowledge.title.like(like) | Knowledge.content.like(like))
    if category:
        query = query.filter(Knowledge.category == category)
    if kind:
        query = query.filter(Knowledge.kind == kind)

    items = query.all()
    return {"total": len(items), "data": [item_to_dict(i) for i in items]}


@router.get("/{item_id}")
def get_knowledge(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Knowledge).filter(Knowledge.id == item_id).first()
    if not item:
        return {"data": None, "message": "知识不存在"}
    return {"data": item_to_dict(item)}


# ---- 增 ----

@router.post("/create")
def create_knowledge(req: KnowledgeCreate, db: Session = Depends(get_db)):
    item = Knowledge(
        title=req.title,
        category=req.category,
        kind=normalize_kind(req.kind),
        content=req.content,
        steps_json=json.dumps(req.steps, ensure_ascii=False) if req.steps else None,
        keywords=req.keywords,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # 同步向量索引：入库即可被检索
    sync_vector(db, item.kind, item.id, item.title, knowledge_index_content(item))

    return {"message": "创建成功", "data": item_to_dict(item)}


# ---- 改 ----

@router.put("/{item_id}")
def update_knowledge(item_id: int, req: KnowledgeUpdate, db: Session = Depends(get_db)):
    item = db.query(Knowledge).filter(Knowledge.id == item_id).first()
    if not item:
        return {"message": "知识不存在", "data": None}

    if req.title is not None:
        item.title = req.title
    if req.category is not None:
        item.category = req.category
    if req.kind is not None:
        item.kind = normalize_kind(req.kind)
    if req.content is not None:
        item.content = req.content
    if req.steps is not None:
        item.steps_json = json.dumps(req.steps, ensure_ascii=False)
    if req.keywords is not None:
        item.keywords = req.keywords

    db.commit()
    db.refresh(item)

    # 内容/类型变了，向量跟着更新
    sync_vector(db, item.kind, item.id, item.title, knowledge_index_content(item))

    return {"message": "更新成功", "data": item_to_dict(item)}


# ---- 删 ----

@router.delete("/{item_id}")
def delete_knowledge(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Knowledge).filter(Knowledge.id == item_id).first()
    if not item:
        return {"message": "知识不存在", "data": None}

    db.delete(item)
    db.commit()

    # 索引里的向量一并删除，防止"幽灵数据"
    delete_vector(db, item.kind, item_id)

    return {"message": "删除成功", "data": {"id": item_id}}


# ---- 索引重建 ----

@router.post("/reindex")
def reindex_knowledge(db: Session = Depends(get_db)):
    """
    全量重建向量索引
    - 日常增删改已自动同步索引，一般不需要手动调用
    - 用于：首次建索引 / 怀疑索引和数据不一致时兜底修复
    """
    if not embed_is_configured():
        return {"message": "未配置 Embedding 服务，请在 .env 中填写", "data": None}

    count = rebuild_index(db)
    return {"message": "向量索引重建完成", "data": {"indexed": count}}
