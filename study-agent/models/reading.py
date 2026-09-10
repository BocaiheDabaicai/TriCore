# 研读记录表 —— 一条记录 = 一次研读（精读 / 泛读）的过程与成果
# 最小单元只有基础字段；精读模板字段、附件（PDF/截图）下一步加

from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(200))

    # 阅读模式：close 精读 / skim 泛读
    mode: Mapped[str] = mapped_column(String(20), default="close")

    # 状态：draft 草稿（还在写）/ done 完成
    # "一点一点写"意味着记录长期处于草稿态，多次保存，最后标记完成
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # 笔记正文（Markdown 文本）
    note: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
