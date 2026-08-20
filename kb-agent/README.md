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

- 首次使用：调用一次 `POST /api/v1/document/reindex`
- 之后新增/修改/删除制度、文档、流程模板都会**自动同步向量索引**，无需手动操作
- `reindex` 保留作为兜底：怀疑索引和数据不一致时全量重建

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

### 制度管理
- `GET /api/v1/policy/list` — 查询制度列表（支持 keyword、category 过滤）
- `GET /api/v1/policy/{id}` — 查看制度详情
- `POST /api/v1/policy/create` — 创建制度
- `PUT /api/v1/policy/{id}` — 更新制度（只传要改的字段）
- `DELETE /api/v1/policy/{id}` — 删除制度

### 文档问答
- `GET /api/v1/document/list` — 查询文档列表
- `GET /api/v1/document/{id}` — 查看文档详情
- `POST /api/v1/document/create` — 创建文档
- `PUT /api/v1/document/{id}` — 更新文档
- `DELETE /api/v1/document/{id}` — 删除文档
- `POST /api/v1/document/ask` — 文档问答（支持多轮）
- `POST /api/v1/document/reindex` — 全量重建向量索引（兜底用，知识变更已自动同步）

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

### 检索性能优化
- **向量归一化入库**：余弦相似度 = 点积 ÷ (模长 × 模长)。把"除以模长"在建索引时提前算好（存单位向量），查询时只剩一次点积
- **NumPy 矩阵运算**：所有向量叠成矩阵，一次矩阵乘法算完所有相似度，替代 Python 逐条循环（纯计算部分加速约 500 倍）
- **二进制存储**：向量以 float32 BLOB 存库（比 JSON 文本省 4 倍空间），读取用 `np.frombuffer` 零解析成本——JSON 解析曾是最大瓶颈（1 万条约 3 秒）

### 索引自动同步
- 增删改制度/文档/流程模板（含添加步骤）时，自动同步对应的向量，无需手动重建
- `sync_vector`（新增/覆盖）、`delete_vector`（删除）、`sync_template_vector`（模板，步骤拼进内容）

### 文档分块（Chunking）
- 长内容自动切块（默认 400 字/块，块间重叠 50 字），每块一个独立向量
- 短内容（≤400 字）不分块；优先按段落边界切，不截断段落
- 检索命中"块"而非整篇：答案更精准、喂给 LLM 的上下文更省 token

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
| 向量计算 | NumPy（矩阵化相似度计算） |
| 向量存储 | SQLite 表（后续可升级 Chroma/Milvus 向量库） |

## 开发记录

见仓库根目录 `note.md`。
