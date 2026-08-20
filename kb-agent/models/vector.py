# 知识向量表 —— 存每条制度/文档的嵌入向量
# 向量就是一串浮点数（比如1024个），语义相近的文字向量也相近

from sqlalchemy import String, Text, Integer, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class KnowledgeVector(Base):
    __tablename__ = "knowledge_vectors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 来源：这条向量来自哪张表哪条记录
    source_type: Mapped[str] = mapped_column(String(20))   # "policy" 或 "document"
    source_id: Mapped[int] = mapped_column(Integer)

    # 块编号：长文档切成多块后，每块一个向量，从 0 开始编号
    # 短内容只有一块（chunk_index = 0）
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)

    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)

    # 向量本体：float32 二进制存储（1024 维 × 4 字节 = 4096 字节）
    # 为什么不用 JSON 文本？
    #   1. 省空间：二进制只有 JSON 文本的 1/4 大小
    #   2. 省时间：读取时 np.frombuffer 直接按 float32 解读，零解析成本，
    #      json.loads 要把每个数字从字符转成浮点数，1万条要花约3秒（实测瓶颈）
    vector_blob: Mapped[bytes] = mapped_column(LargeBinary)
