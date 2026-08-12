from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import SessionLocal
from models.workflow import WorkflowTemplate, WorkflowStep

router = APIRouter(prefix="/api/v1/workflow", tags=["流程助手"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class GuideRequest(BaseModel):
    description: str
    need_steps: bool = False


# ---- 接口 ----

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


@router.post("/templates/create")
def create_template(name: str, description: str, db: Session = Depends(get_db)):
    """创建流程模板（步骤后续用专门接口添加）"""
    template = WorkflowTemplate(name=name, description=description)
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"message": "创建成功", "data": {"id": template.id, "name": template.name}}


@router.post("/templates/{template_id}/steps")
def add_step(template_id: int, order: int, name: str, role: str, db: Session = Depends(get_db)):
    """给指定模板添加一个步骤"""
    step = WorkflowStep(order=order, name=name, role=role, template_id=template_id)
    db.add(step)
    db.commit()
    db.refresh(step)
    return {"message": "步骤添加成功", "data": {"id": step.id, "order": step.order, "name": step.name}}


@router.post("/guide")
def guide_workflow(req: GuideRequest, db: Session = Depends(get_db)):
    """流程引导：根据描述匹配模板"""
    templates = db.query(WorkflowTemplate).all()
    matched = [t for t in templates if any(word in t.name for word in req.description)]

    if not matched:
        return {
            "message": "未找到匹配的流程模板，请联系管理员配置。",
            "suggestion": "试试输入：请假、采购、报销",
        }

    result = {
        "description": req.description,
        "recommend": matched[0].name,
        "detail": matched[0].description,
    }

    if req.need_steps:
        result["steps"] = [{"order": s.order, "name": s.name, "role": s.role} for s in matched[0].steps]

    return result
