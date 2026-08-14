# 企业知识库Agent

基于 Python + FastAPI 的企业知识库系统，支持制度查询、文档问答、流程助手，具备 RAG（检索增强生成）能力。

## 环境要求

- Python 3.10+
- pip

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，填写配置：

```bash
cp .env.example .env
```

| 配置项 | 说明 |
|---|---|
| LLM_* | 大模型配置（DeepSeek / 千问 / OpenAI 等，OpenAI 兼容接口） |
| EMBEDDING_* | 向量嵌入配置（硅基流动 bge-m3 免费 / 千问 / 其他） |

**注意：API Key 只放在 `.env` 里，不要写入 `.env.example`（会提交到 git）。**

## 初始化数据

```bash
python seed_data.py
```

然后**重建向量索引**（让检索生效）：

- 方式一：启动服务后调用 `POST /api/v1/document/reindex`
- 方式二：之后新增/修改了制度、文档、流程模板，都要重新调一次

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
├── main.py                    # 应用入口（路由注册 + 自动建表）
├── core/
│   ├── database.py            # 数据库引擎 + Base 基类
│   └── config.py              # 读取 .env 配置
├── models/                    # ORM 模型（数据库表）
│   ├── policy.py              # 制度表
│   ├── document.py            # 文档表
│   ├── workflow.py            # 流程模板表 + 步骤表
│   ├── message.py             # 对话消息表（多轮记忆）
│   └── vector.py              # 知识向量表（语义检索）
├── api/                       # 接口层
│   ├── policy.py              # 制度查询（CRUD + 问答）
│   ├── document.py            # 文档问答（CRUD + 问答 + 重建索引）
│   ├── workflow.py            # 流程助手（模板/步骤 CRUD + 引导）
│   └── agent.py               # 智能问答（统一问答入口）
├── services/                  # 业务服务层
│   ├── llm_service.py         # 大模型调用（RAG 生成）
│   └── embedding_service.py   # 向量嵌入（建索引 + 语义检索）
├── seed_data.py               # 测试数据初始化脚本
├── requirements.txt
└── .env.example               # 配置模板
```

## 接口列表

### 智能问答（推荐使用）
- `POST /api/v1/agent/chat` — 统一问答入口，全局检索制度+文档+流程，支持多轮对话
  - 请求体：`{"question": "我想请假三天怎么办？", "session_id": "可选，延续会话"}`

### 制度查询
- `GET /api/v1/policy/list` — 查询制度列表（支持 keyword、category 过滤）
- `GET /api/v1/policy/{id}` — 查看制度详情
- `POST /api/v1/policy/create` — 创建制度
- `PUT /api/v1/policy/{id}` — 更新制度（只传要改的字段）
- `DELETE /api/v1/policy/{id}` — 删除制度
- `POST /api/v1/policy/ask` — 制度问答

### 文档问答
- `GET /api/v1/document/list` — 查询文档列表
- `GET /api/v1/document/{id}` — 查看文档详情
- `POST /api/v1/document/create` — 创建文档
- `PUT /api/v1/document/{id}` — 更新文档
- `DELETE /api/v1/document/{id}` — 删除文档
- `POST /api/v1/document/ask` — 文档问答（支持多轮）
- `POST /api/v1/document/reindex` — 重建向量索引（知识变更后调用）

### 流程助手
- `GET /api/v1/workflow/templates` — 流程模板列表
- `GET /api/v1/workflow/templates/{id}` — 模板详情（含步骤）
- `POST /api/v1/workflow/templates/create` — 创建模板
- `PUT /api/v1/workflow/templates/{id}` — 更新模板
- `DELETE /api/v1/workflow/templates/{id}` — 删除模板（级联删除步骤）
- `POST /api/v1/workflow/templates/{id}/steps` — 给模板添加步骤
- `POST /api/v1/workflow/guide` — 流程引导

## 核心机制

### RAG 检索增强生成
1. **检索**：问题转向量 → 与知识库所有向量算余弦相似度 → 取最相关前3条
2. **增强**：资料拼进提示词（标注制度/文档/流程类型）
3. **生成**：大模型基于资料回答，无资料时诚实说"暂无"

### 检索降级链
```
向量语义检索（embedding 已配置且索引非空）
  → 字符打分检索（兜底方案）
```

### 多轮对话
- 返回 `session_id`，下次提问带上即可延续上下文
- 历史消息存 `messages` 表，检索时自动拼接上一轮问题

## 技术栈

| 组件 | 选型 |
|---|---|
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.0 |
| 数据库 | SQLite（可平滑迁移 MySQL/PostgreSQL） |
| 大模型 | DeepSeek（OpenAI 兼容接口，可换任意家） |
| 向量嵌入 | 硅基流动 bge-m3（可换任意家） |
| 向量存储 | SQLite 表（后续可升级 Chroma/Milvus 向量库） |

## 开发记录

见仓库根目录 `note.md`。
