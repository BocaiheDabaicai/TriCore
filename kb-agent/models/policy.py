# 制度表对应的 ORM 模型
# 一个 Python 类 = 数据库里一张表
# 一个类属性 = 表里的一个列

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Policy(Base):
    __tablename__ = "policies"  # 表名（不写的话默认用类名小写）

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #      ↑ 类型                        ↑ 主键，自增
    title: Mapped[str] = mapped_column(String(200))      # 标题，最长200字
    category: Mapped[str] = mapped_column(String(50))     # 分类，比如"人事""财务"
    content: Mapped[str] = mapped_column(Text)            # 正文，Text=不限长度
