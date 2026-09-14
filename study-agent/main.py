from fastapi import FastAPI

from core.database import Base, engine
from models.reading import Reading  # noqa: F401  导入模型才会注册到 Base.metadata（create_all 建表依据）
from models.source import Source    # noqa: F401
from api import readings, sources

app = FastAPI(title="研读助手", version="0.2.0")

# 启动时自动建表：create_all 扫描所有继承 Base 的模型类，表已存在则跳过
Base.metadata.create_all(bind=engine)


def ensure_new_columns():
    """轻量迁移：表已存在时 create_all 不会补新列，这里检查后手动 ALTER 补上（只加列，不动已有数据）"""
    with engine.connect() as conn:
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(readings)")}
        if "rating" not in cols:
            conn.exec_driver_sql("ALTER TABLE readings ADD COLUMN rating INTEGER DEFAULT 0")
        if "domains" not in cols:
            conn.exec_driver_sql("ALTER TABLE readings ADD COLUMN domains JSON DEFAULT '[]'")
        conn.commit()


ensure_new_columns()

# 寻文站点：首次启动（表为空）时灌入 paper.md 记录 0003 的清单
sources.seed_if_empty()

app.include_router(readings.router)
app.include_router(sources.router)


@app.get("/")
def root():
    return {"message": "研读助手 启动成功！"}


@app.get("/api/status")
def status():
    return {"service": "study-agent"}
