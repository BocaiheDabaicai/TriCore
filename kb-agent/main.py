from fastapi import FastAPI

# 导入制度查询模块的路由器
from api.policy import router as policy_router
from api.myapi import router as myapi_router
from api.document import router as document_router

# 1. 创建 FastAPI 应用实例
app = FastAPI(title="企业知识库Agent", version="0.1.0")

# 2. 把 policy_router 挂载到主应用上
#    app.include_router() = "把这个路由器注册进来"
#    现在 /api/v1/policy/list 等接口就生效了
app.include_router(policy_router)
app.include_router(myapi_router)
app.include_router(document_router)


@app.get("/")
def root():
    return {"message": "企业知识库Agent 启动成功！"}


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"你好 {name}，欢迎使用企业知识库！"}
