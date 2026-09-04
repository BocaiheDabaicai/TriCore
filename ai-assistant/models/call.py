# calls 表 —— 调度器的第一个数据库表：每次问答调用记一笔
# 管理端「总览」页的调用统计、最近调用记录都来自这里
# 只有调度器能看到全链路（意图→路由→结果），所以调用情况必须由它记录

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 用户问题（截断到 300 字，管理端展示够用）
    question: Mapped[str] = mapped_column(String(300), default="")

    # 意图识别的目标 Agent（knowledge / general）
    intent_agent: Mapped[str] = mapped_column(String(50), default="")

    # 实际回答来源：knowledge（kb-agent 接住）/ general（兜底对话）/ none（未配置 LLM）
    answer_source: Mapped[str] = mapped_column(String(50), default="none")

    # 想走 Agent 但 Agent 不可用/失败 → 降级兜底
    degraded: Mapped[bool] = mapped_column(Boolean, default=False)

    # 整次调用耗时（毫秒）：意图识别 + 路由 + 回答
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
