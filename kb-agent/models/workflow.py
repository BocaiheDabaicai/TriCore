from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    # relationship —— 不是数据库列，是让 Python 对象可以这样用：
    # template.steps  → 自动查出属于这个模板的所有步骤
    steps: Mapped[list["WorkflowStep"]] = relationship(back_populates="template")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(100))

    # ForeignKey —— 外键，关联到 template 表的 id
    template_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"))

    # back_populates —— 双向关联，step.template 可以反向找到它属于哪个模板
    template: Mapped["WorkflowTemplate"] = relationship(back_populates="steps")
