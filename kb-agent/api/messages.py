# 会话消息清理接口 —— 聊天端删除对话记录时，顺带清掉这边那份多轮上下文
# 独立的 /api/v1/messages 路由组（不并进 /api/v1/agent：这里操作的是"消息"本身，不是问答）

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.message import Message

router = APIRouter(prefix="/api/v1/messages", tags=["会话消息"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.delete("/{session_id}")
def delete_messages(session_id: str, db: Session = Depends(get_db)):
    """删除某个会话的全部消息（幂等：不存在也返回成功）"""
    deleted = db.query(Message).filter(Message.session_id == session_id).delete()
    db.commit()
    return {"message": "已删除", "data": {"deleted": deleted}}
