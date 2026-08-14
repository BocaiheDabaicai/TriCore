# 向量嵌入服务 —— 把文字转成向量 + 余弦相似度检索
# 流程：
#   建索引：每条制度/文档 → 调 embedding API → 得到向量 → 存库
#   检索：  问题 → 调 embedding API → 得到向量 → 和库里所有向量算相似度 → 取最高的

import json
import math

from openai import OpenAI
from sqlalchemy.orm import Session

from core.config import EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL
from models.vector import KnowledgeVector
from models.policy import Policy
from models.document import Document
from models.workflow import WorkflowTemplate

# 独立的客户端（embedding 服务和 LLM 服务通常是两家的）
client = OpenAI(
    api_key=EMBEDDING_API_KEY,
    base_url=EMBEDDING_BASE_URL,
)


def is_configured() -> bool:
    return all([EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL])


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    把一批文字转成一批向量
    - 返回的每个向量是一串浮点数，长度由模型决定（bge-m3 是 1024）
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    # 按输入顺序取回结果（API 保证顺序一致）
    return [item.embedding for item in response.data]


def embed_text(text: str) -> list[float]:
    """单条文字转向量"""
    return embed_texts([text])[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    余弦相似度 —— 衡量两个向量的"方向接近程度"
    - 返回 -1 ~ 1，越接近 1 表示语义越相近
    - 公式：cos = (a·b) / (|a| × |b|)
      a·b 是点积（对应位置相乘再求和）
      |a| 是模长（各元素平方和开根号）
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rebuild_index(db: Session) -> int:
    """
    重建向量索引：把制度+文档+流程模板全部转成向量存入 knowledge_vectors 表
    - 先清空旧向量，再全量重建
    - 返回索引条数
    """
    # 清空旧索引
    db.query(KnowledgeVector).delete()
    db.commit()

    # 收集全部知识
    policies = db.query(Policy).all()
    documents = db.query(Document).all()
    templates = db.query(WorkflowTemplate).all()

    # 逐条转向量并入库
    count = 0
    for p in policies:
        vec = embed_text(p.content)
        db.add(KnowledgeVector(
            source_type="policy",
            source_id=p.id,
            title=p.title,
            content=p.content,
            vector_json=json.dumps(vec),
        ))
        count += 1

    for d in documents:
        vec = embed_text(d.content)
        db.add(KnowledgeVector(
            source_type="document",
            source_id=d.id,
            title=d.title,
            content=d.content,
            vector_json=json.dumps(vec),
        ))
        count += 1

    # 流程模板：把步骤拼进内容再向量化
    # 这样"我想请假"能检索到模板，且步骤信息也在上下文里
    for t in templates:
        steps_text = " → ".join(
            f"{s.order}.{s.name}({s.role})" for s in t.steps
        )
        full_content = f"{t.description}。流程步骤：{steps_text}"
        vec = embed_text(full_content)
        db.add(KnowledgeVector(
            source_type="workflow",
            source_id=t.id,
            title=t.name,
            content=full_content,
            vector_json=json.dumps(vec),
        ))
        count += 1

    db.commit()
    return count


def retrieve_top_k(db: Session, question: str, k: int = 3) -> list[dict]:
    """
    向量检索：问题转向量 → 和库里所有向量算相似度 → 返回最相近的 k 条
    """
    question_vec = embed_text(question)

    rows = db.query(KnowledgeVector).all()

    scored = []
    for row in rows:
        vec = json.loads(row.vector_json)
        score = cosine_similarity(question_vec, vec)  # 比较问题和向量集的相似度，相似度作为得分
        scored.append((score, row))

    # 按相似度从高到低排序，取前 k 条
    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "score": round(score, 4),
            "type": row.source_type,
            "id": row.source_id,
            "title": row.title,
            "content": row.content,
        }
        for score, row in scored[:k]
    ]
