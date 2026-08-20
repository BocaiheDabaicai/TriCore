from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import SessionLocal
from models.workflow import WorkflowTemplate, WorkflowStep
from services.llm_service import is_configured, pick_template
from services.embedding_service import sync_template_vector, delete_vector

router = APIRouter(prefix="/api/v1/workflow", tags=["流程助手"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---- 请求体模型 ----

class GuideRequest(BaseModel):
    description: str
    need_steps: bool = False


class TemplateCreate(BaseModel):
    """创建模板时提交的数据"""
    name: str
    description: str


class TemplateUpdate(BaseModel):
    """更新模板 —— 传哪个改哪个"""
    name: str | None = None
    description: str | None = None


class StepCreate(BaseModel):
    """添加步骤时提交的数据"""
    order: int
    name: str
    role: str


# ---- 查 ----

@router.get("/templates")
def list_templates(keyword: str = Query(default=""), db: Session = Depends(get_db)):
    query = db.query(WorkflowTemplate)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            WorkflowTemplate.name.like(like) | WorkflowTemplate.description.like(like)
        )
    templates = query.all()
    return {
        "total": len(templates),
        "data": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "steps": [{"order": s.order, "name": s.name, "role": s.role} for s in t.steps],
            }
            for t in templates
        ],
    }


@router.get("/templates/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not t:
        return {"data": None, "message": "模板不存在"}
    return {
        "data": {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "steps": [{"order": s.order, "name": s.name, "role": s.role} for s in t.steps],
        }
    }


# ---- 增 ----

@router.post("/templates/create")
def create_template(req: TemplateCreate, db: Session = Depends(get_db)):
    template = WorkflowTemplate(name=req.name, description=req.description)
    db.add(template)
    db.commit()
    db.refresh(template)

    # 同步向量索引（新模板还没有步骤，向量内容 = 描述）
    sync_template_vector(db, template)

    return {"message": "创建成功", "data": {"id": template.id, "name": template.name}}


@router.post("/templates/{template_id}/steps")
def add_step(template_id: int, req: StepCreate, db: Session = Depends(get_db)):
    """给指定模板添加一个步骤"""
    # 先确认模板存在，防止给不存在的模板挂步骤
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        return {"message": "模板不存在", "data": None}

    step = WorkflowStep(order=req.order, name=req.name, role=req.role, template_id=template_id)
    db.add(step)
    db.commit()
    db.refresh(step)

    # 模板向量里包含步骤串，步骤变了向量也要重新算
    # commit 后 SQLAlchemy 默认会把对象"过期"，此时访问 template.steps 会自动重新查库，
    # 拿到包含新步骤的完整列表，不用手动重新查询
    sync_template_vector(db, template)

    return {"message": "步骤添加成功", "data": {"id": step.id, "order": step.order, "name": step.name}}


# ---- 改 ----

@router.put("/templates/{template_id}")
def update_template(template_id: int, req: TemplateUpdate, db: Session = Depends(get_db)):
    t = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not t:
        return {"message": "模板不存在", "data": None}

    if req.name is not None:
        t.name = req.name
    if req.description is not None:
        t.description = req.description

    db.commit()
    db.refresh(t)

    # 描述/名称变了，向量同步更新
    sync_template_vector(db, t)

    return {"message": "更新成功", "data": {"id": t.id, "name": t.name}}


# ---- 删 ----

@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """
    删除模板 —— 【新概念】级联删除
    步骤表的外键指向模板，模板没了步骤就成了"孤儿数据"
    所以删除模板前，必须先把它的步骤全部删掉
    """
    t = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not t:
        return {"message": "模板不存在", "data": None}

    # 1. 先删所有步骤
    steps = db.query(WorkflowStep).filter(WorkflowStep.template_id == template_id).all()
    for s in steps:
        db.delete(s)

    # 2. 再删模板本身
    db.delete(t)
    db.commit()

    # 3. 删掉索引里的模板向量，防止检索到已删除的流程
    delete_vector(db, "workflow", template_id)

    return {"message": "删除成功", "data": {"id": template_id}}


# ---- 流程引导 ----

@router.post("/guide")
def guide_workflow(req: GuideRequest, db: Session = Depends(get_db)):
    templates = db.query(WorkflowTemplate).all()

    if is_configured():
        # LLM 路线：把所有模板发给模型，让它挑一个，只返回模板名
        context = "\n\n".join(
            f"{t.name}：{t.description}" for t in templates
        )
        picked_name = pick_template(req.description, context)

        # 拿 LLM 返回的名字，回数据库找完整的模板对象
        # 步骤等详细信息必须来自数据库，不能让 LLM 编
        chosen = next((t for t in templates if t.name == picked_name), None)

        if chosen is None:
            return {
                "message": "未找到匹配的流程模板，请联系管理员配置。",
                "suggestion": "试试输入：请假、采购、报销",
            }
    else:
        # 降级路线：关键字匹配
        matched = [t for t in templates if any(word in t.name for word in req.description)]
        if not matched:
            return {
                "message": "未找到匹配的流程模板，请联系管理员配置。",
                "suggestion": "试试输入：请假、采购、报销",
            }
        chosen = matched[0]

    result = {
        "description": req.description,
        "recommend": chosen.name,
        "detail": chosen.description,
    }

    if req.need_steps:
        result["steps"] = [{"order": s.order, "name": s.name, "role": s.role} for s in chosen.steps]

    return result
