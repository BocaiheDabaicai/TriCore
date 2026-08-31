# 存量数据补 keywords：对 keywords 为空的已有知识，调用 LLM 生成关键词
# 用法：在 kb-agent 目录执行  .venv\Scripts\python.exe backfill_keywords.py
# 说明：新上传的知识已自动生成 keywords，本脚本只处理历史数据

from core.database import SessionLocal
from models.knowledge import Knowledge
from services.llm_service import is_configured, generate_keywords


def main():
    if not is_configured():
        print("未配置 LLM，请检查 .env")
        return

    db = SessionLocal()
    items = (
        db.query(Knowledge)
        .filter((Knowledge.keywords == None) | (Knowledge.keywords == ""))  # noqa: E711
        .all()
    )
    if not items:
        print("没有需要补录的条目")
        db.close()
        return

    print(f"共 {len(items)} 条需要补录")
    for it in items:
        kw = generate_keywords(it.title, it.content)
        it.keywords = kw
        db.commit()
        print(f"#{it.id} {it.title} → {kw}")
    db.close()
    print("补录完成")


if __name__ == "__main__":
    main()
