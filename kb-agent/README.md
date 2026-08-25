# 企业知识库Agent

基于 Python + FastAPI 的企业知识库系统：统一上传（解析 + AI 识别分类）→ 统一知识库 → 智能问答，具备 RAG（检索增强生成）能力。

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

- 首次使用：调用一次 `POST /api/v1/knowledge/reindex`
- 之后新增/修改/删除知识都会**自动同步向量索引**，无需手动操作
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
│   ├── knowledge.py           # 统一知识表（kind 区分 制度/文档/流程）
│   ├── message.py             # 对话消息表（多轮记忆）
│   └── vector.py              # 知识向量表（语义检索，按块存储）
├── api/                       # 接口层
│   ├── knowledge.py           # 统一知识库（上传 + CRUD + 重建索引）
│   └── agent.py               # 智能问答（统一问答入口）
├── services/                  # 业务服务层
│   ├── llm_service.py         # 大模型调用（RAG 生成 + 上传内容识别分类）
│   ├── embedding_service.py   # 向量嵌入（分块 + 建索引 + 语义检索 + 同步）
│   └── file_parser.py         # 文件解析（txt/md/pdf/docx，含 docx 表格提取）
├── seed_data.py               # 测试数据初始化脚本
├── requirements.txt
└── .env.example               # 配置模板
```

## 接口列表

### 智能问答（推荐使用）
- `POST /api/v1/agent/chat` — 统一问答入口，全局检索所有知识，支持多轮对话
  - 请求体：`{"question": "我想请假三天怎么办？", "session_id": "可选，延续会话"}`
- `POST /api/v1/agent/chat/stream` — 流式版问答（SSE），回答逐段返回，前端可做打字机效果
  - 事件：`meta`（来源/会话信息）→ `delta`（回答增量，多次）→ `done`（结束）

### 统一知识库
- `POST /api/v1/knowledge/upload` — **统一上传**：文件（txt/md/pdf/docx）→ 解析 → LLM 识别类型（制度/文档/流程）→ 入库 → 自动分块向量化
  - 可选表单参数：`kind`（手动指定类型，覆盖 LLM 判断）、`category`（业务分类，不传则由 LLM 根据内容自动拟定）
- `GET /api/v1/knowledge/list` — 知识列表（支持 keyword、category、kind 过滤）
- `GET /api/v1/knowledge/{id}` — 知识详情
- `POST /api/v1/knowledge/create` — 手工创建知识
- `PUT /api/v1/knowledge/{id}` — 更新知识（只传要改的字段）
- `DELETE /api/v1/knowledge/{id}` — 删除知识
- `POST /api/v1/knowledge/reindex` — 全量重建向量索引（兜底用，知识变更已自动同步）

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
- 增删改知识（含上传、修改流程步骤）时，自动同步对应的向量，无需手动重建
- `sync_vector`（分块、新增/覆盖）、`delete_vector`（删除）

### 文档分块（Chunking）
- 长内容自动切块（默认 400 字/块，块间重叠 50 字），每块一个独立向量
- 短内容（≤400 字）不分块；优先按段落边界切，不截断段落
- 检索命中"块"而非整篇：答案更精准、喂给 LLM 的上下文更省 token

### 文件解析
- 支持 txt / md / pdf / docx 上传，解析成纯文本入库
- docx 按文档顺序提取段落和表格：表格每行一条、`|` 分隔、合并单元格重复文字去重——制度文件里的收费标准表、申请单表不会丢失
- 已知限制：Word 自动编号（"第X条"的 X）解析不到；表格与正文挤在同一分块时检索排序可能偏低

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
| 文件解析 | pypdf（PDF）、python-docx（Word） |

## 架构演进

### v0.1：三表分型（2026-08-11 ~ 08-20）

知识按类型分三张表存储：`policies`（制度）、`documents`（文档）、`workflow_templates` + `workflow_steps`（流程模板和步骤）。对应三组接口，各管各的增删改查和问答。

### v0.2：统一知识表（2026-08-20）

**转变**：三表合一为 `knowledge` 表，用 `kind` 字段（policy/document/workflow）区分类型；流程步骤从独立子表退化为 `steps_json` JSON 字段；接口合并为一组 `/api/v1/knowledge`，新增统一上传入口。

**原因**：

1. 用户不该为分类操心——上传一个文件，还要先判断"它属于制度、文档还是流程"再选对应接口，这违背了统一问答入口"用户不知道也不关心信息在哪个模块"的设计思想
2. 三组接口 90% 的代码是重复的 CRUD 模板
3. 每次新增知识类型（通知、模板文件……）都要建表 + 写一组接口

**收益**：

1. 一个上传接口走天下：文件 → 解析 → LLM 识别分类 → 入库 → 立即可问答
2. 接口从三组（16 个）缩为一组（7 个），维护成本大降
3. 新类型只加 kind 枚举值，不改表结构

**代价**：流程步骤从关系型数据（可独立增删改、级联删除）退化为 JSON 字段——损失了按步骤查询的能力，换来模型统一。当前业务里步骤只用于展示和拼进向量，这个代价可接受。

**数据建模心得**：单表多型（一张表 + type 字段）适合"各类型结构大同小异、未来还会加类型"的场景；多表分型适合"各类型结构差异大、需要各自独立演进"的场景。本项目在两种方式都实践过之后，选择了前者。

## 开发记录

见仓库根目录 `README.md` 的「更新日志」章节。
