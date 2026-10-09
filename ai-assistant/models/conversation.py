# 对话记录两张表 —— 聊天端左侧「对话记录」列表的数据来源
# 为什么放调度器：它是唯一能看到全链路的服务（意图→路由→回答）；
# kb-agent 那边另有一份 messages 只服务它自己的多轮上下文，两者互不替代

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 会话ID：由前端首轮发问时懒生成（session-{12hex}），全链路共用同一个
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # 标题 = 首问截断 50 字（列表里显示）
    title: Mapped[str] = mapped_column(String(200), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    session_id: Mapped[str] = mapped_column(String(64), index=True)

    role: Mapped[str] = mapped_column(String(20))

    content: Mapped[str] = mapped_column(Text)

    # assistant 行才有：JSON 字符串 {source, sources, retrieval, degraded}
    # source 存"实际回答来源"而不是意图名 —— 降级轮（想走 knowledge 实际走了 general）不能标错
    meta: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
