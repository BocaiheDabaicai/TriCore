# 临时脚本：打印一批样本问题的向量检索分数分布，用于标定"命中/未命中"阈值
# 用法：.venv\Scripts\python.exe debug_score_distribution.py

from core.database import SessionLocal
from services.embedding_service import retrieve_top_k

# 前 4 个预期命中（知识库有相关内容），后 5 个预期未命中（知识库没有）
SAMPLES = [
    ("命中预期", "电费怎么收费"),
    ("命中预期", "住宿申请单怎么填"),
    ("命中预期", "信息安全制度"),
    ("命中预期", "健身房怎么使用"),
    ("命中预期", "押金是多少"),
    ("未命中预期", "工资什么时候发放"),
    ("未命中预期", "食堂的开放时间是几点"),
    ("未命中预期", "公司附近哪里可以停车"),
    ("未命中预期", "员工的年终奖怎么算"),
    ("宽泛", "公司有什么规章制度"),
]

db = SessionLocal()
try:
    for label, q in SAMPLES:
        matched = retrieve_top_k(db, q, k=10, threshold=0)   # 看全部分数分布，绕过阈值过滤
        print(f"\n【{label}】{q}")
        for m in matched:
            print(f"  {m['score']:.4f}  {m['title']}  (块{m['chunk_index']})")
finally:
    db.close()
