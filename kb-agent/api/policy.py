from fastapi import APIRouter

# 1. 创建"路由器"——相当于一个小型的 FastAPI
#    prefix="/api/v1/policy" 表示这个文件里所有接口路径都以它开头
router = APIRouter(prefix="/api/v1/policy", tags=["制度查询"])

# 2. 硬编码几条假数据（还没有数据库，暂时用 list 代替）
FAKE_POLICIES = [
    {"id": 1, "title": "考勤管理制度", "category": "人事", "content": "上班时间为9:00-18:00，迟到扣款50元/次。"},
    {"id": 2, "title": "报销审批制度", "category": "财务", "content": "报销金额超过500元需部门经理审批。"},
    {"id": 3, "title": "信息安全制度", "category": "IT",   "content": "严禁在外部设备上存储公司敏感数据。"},
    {"id": 4, "title": "出差管理制度", "category": "人事", "content": "出差需提前3天提交出差申请单。"},
    {"id": 5, "title": "采购流程制度", "category": "财务", "content": "单笔采购超过1000元需三家比价。"},
]


@router.get("/list")
def list_policies(keyword: str = "", category: str = ""):
    """
    查询制度列表
    - keyword: 按标题/内容模糊搜索，不传就是查全部
    - category: 按分类过滤，不传就是所有分类
    两个参数都可以不传，默认空字符串表示"不过滤"
    """
    result = FAKE_POLICIES

    # 关键字过滤：标题或内容包含关键字才算命中
    if keyword:
        result = [p for p in result if keyword in p["title"] or keyword in p["content"]]

    # 分类过滤
    if category:
        result = [p for p in result if p["category"] == category]

    return {"total": len(result), "data": result}


@router.get("/{policy_id}")
def get_policy(policy_id: int):
    """根据ID查一条制度的详情"""
    for p in FAKE_POLICIES:
        if p["id"] == policy_id:
            return {"data": p}
    return {"data": None, "message": "制度不存在"}
