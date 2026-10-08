# 运行记录的表结构 —— 三张表，各管一件事
#   runs        一次运行：哪个单元、输入什么、跑到哪一步、结果如何
#   run_steps   这次运行里每一步的状态（前端"步骤列表"就是读这张表）
#   unit_meta   单元的人工标记（哪些单元已经人工核对过、真跑通了）

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_key: Mapped[str] = mapped_column(String(50), index=True)
    input_json: Mapped[str] = mapped_column(Text)          # 这次用的输入（JSON 文本原样存，便于复现）
    # queued 排队中 / running 执行中 / success 成功 / failed 失败
    # canceled 人工取消 / interrupted 服务重启打断（启动时会把这些标出来）
    status: Mapped[str] = mapped_column(String(20), default="queued")
    current_step: Mapped[int] = mapped_column(Integer, default=-1)   # 正在跑第几步（下标，-1 = 还没开始）
    error_step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_dir: Mapped[str | None] = mapped_column(String(300), nullable=True)  # 截图等产物落在哪
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RunStep(Base):
    __tablename__ = "run_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, index=True)
    idx: Mapped[int] = mapped_column(Integer)              # 第几步（0 开始，和单元声明的顺序一致）
    step_key: Mapped[str] = mapped_column(String(50))
    cn_name: Mapped[str] = mapped_column(String(100))
    # pending 未开始 / running 进行中 / success 成功 / failed 失败 / skipped 跳过（前面的步骤已失败）
    status: Mapped[str] = mapped_column(String(20), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    screenshot: Mapped[str | None] = mapped_column(String(300), nullable=True)   # 相对 rpa-agent/ 的路径
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class UnitMeta(Base):
    __tablename__ = "unit_meta"

    unit_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    verified: Mapped[int] = mapped_column(Integer, default=0)   # 人工确认"真跑通了"（0/1）
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
