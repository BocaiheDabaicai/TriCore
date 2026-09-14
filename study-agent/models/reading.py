# 研读记录表 —— 一条记录 = 一次研读（精读 / 泛读）的过程与成果
# 字段与前端数据层（frontend/src/api/readings.js）的契约一一对应

from datetime import datetime

from sqlalchemy import JSON, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(200))

    # 阅读模式：close 精读 / skim 泛读
    mode: Mapped[str] = mapped_column(String(20), default="close")

    # 分类标签（选填，自创或复用已有）
    tag: Mapped[str] = mapped_column(String(50), default="")

    # 评分（0-10，0 = 未打分）——回顾详情里点星星打的，半星 = 1 分
    rating: Mapped[int] = mapped_column(Integer, default=0)

    # 小领域（0-3 个，自创或复用已有，如 数字化 / 智能体）——JSON 列存字符串列表
    domains: Mapped[list] = mapped_column(JSON, default=list)

    # 文献信息（选填）：作者 / 出版时间（手填 YYYY-MM）/ 期刊
    author: Mapped[str] = mapped_column(String(200), default="")
    published: Mapped[str] = mapped_column(String(20), default="")
    journal: Mapped[str] = mapped_column(String(200), default="")

    # 笔记正文（Markdown 文本）
    note: Mapped[str] = mapped_column(Text, default="")

    # 论文文件名（精读，上传后写入；原文件在 uploads/ 目录，命名 {id}_{文件名}）
    attachment: Mapped[str] = mapped_column(String(300), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
