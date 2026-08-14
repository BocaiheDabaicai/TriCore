# 对话消息表 —— 保存每一次问答，实现多轮对话记忆

from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 会话ID：同一次连续对话的所有消息共享一个 session_id
    session_id: Mapped[str] = mapped_column(String(64), index=True)

    # 角色：user（用户问的）/ assistant（AI答的）
    role: Mapped[str] = mapped_column(String(20))

    content: Mapped[str] = mapped_column(Text)

    # 创建时间：datetime.now 是函数，SQLAlchemy 会在插入时调用它
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
