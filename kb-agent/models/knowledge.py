# 统一知识表 —— 制度/文档/流程不再分表，用 kind 字段区分类型
# 转变原因和收益见 README「架构演进」章节

from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Knowledge(Base):
    __tablename__ = "knowledge"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(200))

    # 业务分类：由 LLM 根据内容自由拟定（如 员工宿舍管理），也可手动指定
    category: Mapped[str] = mapped_column(String(50))

    # 知识类型：policy 制度 / document 文档 / workflow 流程
    kind: Mapped[str] = mapped_column(String(20))

    content: Mapped[str] = mapped_column(Text)

    # 流程步骤（仅 kind=workflow 时使用）：
    # JSON 字符串，如 [{"order":1,"name":"提交申请","role":"员工"}, ...]
    # 流程的步骤不再是独立子表，检索和展示都够用
    steps_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 原始文件名（上传的知识记录来源，手工创建为 None）
    filename: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # 关键词索引（宽度查询用）：LLM 生成，格式如 "住宿、申请、押金"
    # 用途：宽度回答时列"标题+关键词"当目录，用户点名后走深度查询
    keywords: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
