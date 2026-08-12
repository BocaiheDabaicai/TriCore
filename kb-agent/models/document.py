from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
