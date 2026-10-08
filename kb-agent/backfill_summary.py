# 存量数据补摘要：对 summary 为空的已有知识，调用 LLM 生成摘要
# 用法：在 kb-agent 目录执行  .venv\Scripts\python.exe backfill_summary.py
# 说明：新上传的知识已自动生成 summary（和分类同一次调用），本脚本只处理历史数据

from core.database import SessionLocal
from models.knowledge import Knowledge
from services.llm_service import is_configured, summarize


def main():
    if not is_configured():
        print("未配置 LLM，请检查 .env")
        return

    db = SessionLocal()
    items = (
        db.query(Knowledge)
        .filter((Knowledge.summary == None) | (Knowledge.summary == ""))  # noqa: E711
        .all()
    )
    if not items:
        print("没有需要补录的条目")
        db.close()
        return

    print(f"共 {len(items)} 条需要补录")
    for it in items:
        s = summarize(it.title, it.content)
        if s:
            it.summary = s
            db.commit()
        print(f"#{it.id} {it.title} → {s or '（失败，跳过）'}")
    db.close()
    print("补录完成")


if __name__ == "__main__":
    main()
