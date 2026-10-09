# 对话记录接口 —— 聊天端左侧「对话记录」列表用（列表 / 详情 / 删除）
# 返回值统一 {message, data} 形状，与 kb-agent 的管理接口一致
# 不存在返回 data:null（前端当"已删"处理）；删除幂等

import json

from fastapi import APIRouter
from sqlalchemy import func

from core.database import SessionLocal
from models.conversation import ChatMessage, Conversation
from services import registry

router = APIRouter(prefix="/api/v1/conversations", tags=["对话记录"])


def fmt(dt):
    """时间统一给 ISO 无时区格式（前端 new Date 按本地时间解析）"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S") if dt else ""


@router.get("")
def list_conversations():
    """全部会话（按最近更新倒序），带消息数"""
    db = SessionLocal()
    try:
        counts = dict(
            db.query(ChatMessage.session_id, func.count(ChatMessage.id))
            .group_by(ChatMessage.session_id)
            .all()
        )
        rows = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
        return {
            "message": "ok",
            "data": [
                {
                    "session_id": c.session_id,
                    "title": c.title,
                    "message_count": counts.get(c.session_id, 0),
                    "created_at": fmt(c.created_at),
                    "updated_at": fmt(c.updated_at),
                }
                for c in rows
            ],
        }
    finally:
        db.close()


@router.get("/{session_id}")
def get_conversation(session_id: str):
    """单个会话 + 全部消息（前端点开旧会话回放、继续追问）；不存在返回 data:null"""
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            return {"message": "不存在", "data": None}
        msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())   # 按自增 id 排 = 插入顺序（created_at 精度只有秒，会并列）
            .all()
        )
        return {
            "message": "ok",
            "data": {
                "session_id": conv.session_id,
                "title": conv.title,
                "created_at": fmt(conv.created_at),
                "updated_at": fmt(conv.updated_at),
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "meta": json.loads(m.meta) if m.meta else None,
                        "created_at": fmt(m.created_at),
                    }
                    for m in msgs
                ],
            },
        }
    finally:
        db.close()


@router.delete("/{session_id}")
def delete_conversation(session_id: str):
    """删除会话：本地两表 + best-effort 清 kb-agent 那份上下文（失败不影响本地删除）"""
    db = SessionLocal()
    try:
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.query(Conversation).filter(Conversation.session_id == session_id).delete()
        db.commit()
    finally:
        db.close()

    # best-effort：会话 id 随机生成、不复用，清不掉也不会让旧上下文污染新会话
    registry.delete_kb_messages(session_id)
    return {"message": "已删除", "data": None}
