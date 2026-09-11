# 寻文站点表 —— 文献网站汇总（类型分组 + 链接）
# 字段与前端数据层（frontend/src/api/sources.js）的契约一一对应

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 类型分组：工程管理 / AI·计算机 / Web3·区块链
    type: Mapped[str] = mapped_column(String(50))

    name: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(500))
    note: Mapped[str] = mapped_column(String(200), default="")
