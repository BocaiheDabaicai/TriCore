from fastapi import APIRouter

# 1. 新引入：BaseModel —— 用来定义"请求体"的结构
#    之前 GET 请求的参数都是跟在 URL 后面的（?keyword=xxx）
#    但上传文档内容很大，不适合放 URL 里，需要用 POST 把数据放在"请求体"中
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/document", tags=["文档问答"])

# 2. 硬编码几条假文档数据
FAKE_DOCS = [
    {"id": 1, "title": "入职指南", "category": "人事", "content": "新员工入职需携带身份证、学历证明、离职证明。"},
    {"id": 2, "title": "报销流程", "category": "财务", "content": "填写报销单 → 主管审批 → 财务审核 → 打款，周期约7个工作日。"},
    {"id": 3, "title": "VPN使用说明", "category": "IT", "content": "下载客户端，使用企业账号登录，密钥找IT部门申请。"},
]


# 3. 定义一个"请求体模型"——告诉 FastAPI 提交的数据长什么样
#    继承 BaseModel，里面的字段就是期望接收的数据
class AskRequest(BaseModel):
    question: str           # 用户的问题
    doc_id: int | None = None  # 可选：指定问哪篇文档，不传就搜全部


# ---- 接口 ----

@router.get("/list")
def list_docs(keyword: str = "", category: str = ""):
    """查询文档列表（和制度查询逻辑一样，复习一下）"""
    result = FAKE_DOCS
    if keyword:
        result = [d for d in result if keyword in d["title"] or keyword in d["content"]]
    if category:
        result = [d for d in result if d["category"] == category]
    return {"total": len(result), "data": result}


@router.get("/{doc_id}")
def get_doc(doc_id: int):
    """查看一篇文档的详情"""
    for d in FAKE_DOCS:
        if d["id"] == doc_id:
            return {"data": d}
    return {"data": None, "message": "文档不存在"}


@router.post("/ask")
def ask_document(req: AskRequest):
    """
    【新概念】POST 请求 + 请求体
    - 调用方用 POST 方式访问 /api/v1/document/ask
    - 请求体里放 JSON：{"question": "怎么报销？", "doc_id": 2}
    - FastAPI 自动把 JSON 转成 AskRequest 对象，赋值给 req
    """
    # 如果指定了文档ID，就只查那篇
    docs_to_search = FAKE_DOCS
    if req.doc_id:
        docs_to_search = [d for d in FAKE_DOCS if d["id"] == req.doc_id]

    # 这里暂时用最简单的关键字匹配，模拟"从文档中找答案"
    # 后续接入 LLM 后，会变成真正的智能问答
    # 逐一匹配，使用问题的每个字符去问题库的content里去匹配
    # 匹配到，那么把问题库的答案收集起来，并返回
    matched = []
    for d in docs_to_search:
        for word in req.question:
            if word in d["content"]:
                matched.append(d)
                break

    if matched:
        answer = f"根据文档「{matched[0]['title']}」：{matched[0]['content']}"
    else:
        answer = "未找到相关内容，请换个问题试试。"

    return {
        "question": req.question,
        "answer": answer,
        "sources": matched,
    }
