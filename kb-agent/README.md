# 企业知识库Agent

基于 Python + FastAPI 的企业知识库系统，支持制度查询、文档问答、流程助手。

## 环境要求

- Python 3.10+
- pip

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
uvicorn main:app --reload
```

## 访问

| 地址 | 说明 |
|---|---|
| http://127.0.0.1:8000 | 服务首页 |
| http://127.0.0.1:8000/docs | Swagger 接口文档（可在线调试） |
| http://127.0.0.1:8000/redoc | ReDoc 只读文档 |

## 项目结构

```
kb-agent/
├── main.py              # 应用入口
├── api/                  # 接口模块
│   ├── policy.py          # 制度查询
│   └── document.py       # 文档问答
├── requirements.txt     # 依赖清单
└── .env.example         # 配置模板
```

## 接口列表

### 制度查询
- `GET /api/v1/policy/list` — 查询制度列表（支持 keyword、category 过滤）
- `GET /api/v1/policy/{id}` — 查看制度详情

### 文档问答
- `GET /api/v1/document/list` — 查询文档列表
- `GET /api/v1/document/{id}` — 查看文档详情
- `POST /api/v1/document/ask` — 提交问题，获取答案
