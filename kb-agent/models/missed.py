# 未命中问题表 —— 记录"用户问了、知识库没答上"的问题
# 用途：知识库建设的输入——用户问什么没答上，就是该往知识库补什么
# 管理员定期看这张表（按 count 排序），补充完对应资料后删除记录

from datetime import datetime

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class MissedQuestion(Base):
    __tablename__ = "missed_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 问题原文，unique：同一个问题反复问只累计次数，不重复记录
    question: Mapped[str] = mapped_column(String(500), unique=True)

    # 被问次数：次数越高，说明越多人关心、越该优先补充
    count: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
