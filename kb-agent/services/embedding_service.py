# 向量嵌入服务 —— 把文字转成向量 + 余弦相似度检索
# 流程：
#   建索引：每条知识 → 调 embedding API → 得到向量 → 归一化后存库（"提前算好"）
#   检索：  问题 → 调 embedding API → 得到向量 → 归一化 → 一次矩阵乘法算完所有相似度 → 取最高的

import json

import numpy as np
from openai import OpenAI
from sqlalchemy.orm import Session

from core.config import EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL
from models.vector import KnowledgeVector
from models.knowledge import Knowledge

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


def normalize(vec: np.ndarray) -> np.ndarray:
    """
    归一化 —— 向量除以自己的长度（模长），变成"单位向量"（长度为1）
    为什么要归一化？
      余弦相似度公式：cos = (a·b) / (|a| × |b|)
      如果 a、b 都先归一化成单位向量，那么 |a| = |b| = 1
      公式就简化成：cos = a·b（纯点积）
    这就是"能提前算好的提前算"：把除以模长这件事，在建索引时一次性算掉，
    查询时就只剩一次点积，又快又省。
    """
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


def to_vector(text: str) -> np.ndarray:
    """文字 → 向量 → 归一化，一步到位（float32 比 float64 省一半内存，精度对相似度足够）"""
    return normalize(np.array(embed_text(text), dtype=np.float32))


def knowledge_index_content(item) -> str:
    """
    知识入库向量化的内容：
    - 流程类型：正文 + 步骤拼串（步骤存在 steps_json 里）
    - 其他类型：直接用正文
    建索引和同步都走这一个函数，保证两边存的向量内容格式一致
    """
    if item.kind == "workflow" and item.steps_json:
        try:
            steps = json.loads(item.steps_json)
            steps_text = " → ".join(
                f"{s['order']}.{s['name']}({s['role']})" for s in steps
            )
            if steps_text:
                return f"{item.content}。流程步骤：{steps_text}"
        except Exception:
            pass   # steps_json 解析失败就只用正文
    return item.content


def split_chunks(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """
    把长文本切成小块（RAG 分块）—— 为什么要分块？
      1. 整篇文档一个向量，语义被"平均"掉，问具体细节时检索不精准
      2. 切块后每块聚焦一个小主题，检索命中率更高
      3. 也省 token：回答时只把命中的块喂给 LLM，而不是整篇文档
    规则：
      - 短文本（<= chunk_size）不分，整段作为一块
      - 优先按段落边界组块，尽量不在段落中间切断
      - 超长段落硬切，块与块之间保留 overlap 个字的重叠，
        避免一句话被拦腰截断、上下文丢失
    """
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    current = ""
    for p in (seg.strip() for seg in text.split("\n") if seg.strip()):
        # 当前块装不下这个段落 → 封口，段落另起新块
        if current and len(current) + 1 + len(p) > chunk_size:
            chunks.append(current)
            current = ""
        current = f"{current}\n{p}" if current else p
        # 段落本身超长 → 硬切，下一段带上 overlap 个字的重叠
        while len(current) > chunk_size:
            chunks.append(current[:chunk_size])
            current = current[chunk_size - overlap:]
    if current:
        chunks.append(current)
    return chunks


def add_chunks(db: Session, source_type: str, source_id: int, title: str, content: str) -> int:
    """把一条知识的内容分块，逐块向量化入库，返回块数"""
    chunks = split_chunks(content)
    for i, chunk in enumerate(chunks):
        vec = to_vector(chunk)
        db.add(KnowledgeVector(
            source_type=source_type,
            source_id=source_id,
            chunk_index=i,
            title=title,
            content=chunk,
            vector_blob=vec.tobytes(),
        ))
    return len(chunks)


def rebuild_index(db: Session) -> int:
    """
    重建向量索引：把统一知识表（制度/文档/流程）全部转成向量存入 knowledge_vectors 表
    - 先清空旧向量，再全量重建
    - 返回索引条数（= 块数）
    """
    # 清空旧索引
    db.query(KnowledgeVector).delete()
    db.commit()

    # 收集全部知识（统一表：制度/文档/流程都在这里，用 kind 区分）
    items = db.query(Knowledge).all()

    # 逐条知识分块向量化入库 —— 向量已归一化（提前把"除以模长"算好，查询时只需点积）
    # 长内容自动切成多块（每块一个向量），短内容一块搞定
    # source_type 存 kind 值：语义从"来自哪张表"变为"哪种知识类型"
    count = 0
    for item in items:
        count += add_chunks(db, item.kind, item.id, item.title, knowledge_index_content(item))

    db.commit()
    return count


def sync_vector(db: Session, source_type: str, source_id: int, title: str, content: str) -> None:
    """
    同步一条知识的向量 —— 新增/修改知识时调用
    - 先分块、逐块向量化（成功后才动索引，失败不动旧索引）
    - 再删掉这条知识的旧块、插入新块（内容变了，块数可能也变了）
    - embedding 未配置时直接跳过（此时检索走字符打分降级，不需要索引）
    """
    if not is_configured():
        return

    try:
        chunks = split_chunks(content)
        vecs = [to_vector(c) for c in chunks]
    except Exception:
        # 向量化失败（网络/API 问题）不阻断业务：业务数据已保存，索引可稍后 /reindex 重建
        print(f"警告：{source_type}#{source_id} 向量同步失败，可稍后调用 /reindex 全量重建")
        return

    db.query(KnowledgeVector).filter(
        KnowledgeVector.source_type == source_type,
        KnowledgeVector.source_id == source_id,
    ).delete()
    for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
        db.add(KnowledgeVector(
            source_type=source_type,
            source_id=source_id,
            chunk_index=i,
            title=title,
            content=chunk,
            vector_blob=vec.tobytes(),
        ))
    db.commit()


def delete_vector(db: Session, source_type: str, source_id: int) -> None:
    """删除一条知识的向量 —— 删除知识时调用，防止索引里残留孤儿向量"""
    db.query(KnowledgeVector).filter(
        KnowledgeVector.source_type == source_type,
        KnowledgeVector.source_id == source_id,
    ).delete()
    db.commit()


def retrieve_top_k(db: Session, question: str, k: int = 3) -> list[dict]:
    """
    向量检索（矩阵版）：
      1. 问题 → 向量 → 归一化
      2. 把库里所有向量叠成一个矩阵（n 行 × 1024 列）
      3. 一次矩阵乘法 matrix @ question_vec，同时算出 n 个相似度
         （索引里的向量已归一化，点积 = 余弦相似度，结果和原来完全一样）
      4. argsort 取最高的 k 条
    为什么快：矩阵乘法由 numpy 在 C 语言底层实现，配合 CPU 的向量指令（SIMD）并行执行，
    替代了原来"Python for 循环逐条算"的方式。n 条数据从 n 次 Python 计算 → 1 次 C 计算。
    """
    question_vec = to_vector(question)

    rows = db.query(KnowledgeVector).all()
    if not rows:
        return []

    # 库里所有向量叠成矩阵 —— 二进制零解析成本：
    #   1. b"".join 把每条 4096 字节的 BLOB 拼成一段连续内存
    #   2. np.frombuffer 直接按 float32 解读这段内存（不复制、不解析，只是"换个角度看字节"）
    #   3. reshape 成 n 行 × 1024 列的矩阵
    blob = b"".join(row.vector_blob for row in rows)
    matrix = np.frombuffer(blob, dtype=np.float32).reshape(len(rows), -1)

    # 一次矩阵-向量乘法，算出所有行的相似度
    scores = matrix @ question_vec

    # argsort 返回"从小到大排序后各元素的原下标"，[::-1] 倒序成"从大到小"，再取前 k 个
    top_idx = np.argsort(scores)[::-1][:k]

    return [
        {
            "score": round(float(scores[i]), 4),
            "type": rows[i].source_type,
            "id": rows[i].source_id,
            "chunk_index": rows[i].chunk_index,
            "title": rows[i].title,
            "content": rows[i].content,
        }
        for i in top_idx
    ]
