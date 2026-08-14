# 知识向量表 —— 存每条制度/文档的嵌入向量
# 向量就是一串浮点数（比如1024个），语义相近的文字向量也相近

from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class KnowledgeVector(Base):
    __tablename__ = "knowledge_vectors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 来源：这条向量来自哪张表哪条记录
    source_type: Mapped[str] = mapped_column(String(20))   # "policy" 或 "document"
    source_id: Mapped[int] = mapped_column(Integer)

    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)

    # 向量本体：JSON 字符串存储（"[0.12, -0.45, ...]"）
    # SQLite 没有专门的向量类型，用文本存最简单
    vector_json: Mapped[str] = mapped_column(Text)
