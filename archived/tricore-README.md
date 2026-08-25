# TriCore（三核）

> Sales + OA + Inventory + Master Data + Regulations + AI — 企业核心业务一体化智能解决方案

## 命名由来

| 维度 | 说明 |
|------|------|
| **Tri** | 三大核心系统：**Sales**（销售管理）+ **OA**（办公协同）+ **Inventory**（库存管理） + 辅助模块（Master Data / Regulations / AI） |
| **Core** | 聚焦核心业务，直击本质，不做 bloated SaaS |
| **中文名** | **三核** — 简洁有力，好记好传 |
| **英文名** | `TriCore` — 短小精悍，适合包名、域名 |
| **Rust 后端** | `tricore-server` — 高性能、内存安全 |
| **React 前端** | `tricore-web` — Vite + React + TypeScript |
| **Vue 3 前端** | `tricore-web-rust` — Rsbuild/Rspack + Vue 3 + TypeScript |

---

## 技术栈

### 前端 — `tricore-web`（React）

| 技术 | 用途 |
|------|------|
| Vite | 构建工具，极速 HMR |
| React 19 | UI 框架 |
| TypeScript | 类型安全 |
| React Router | 客户端路由 |
| Ant Design 6 | 企业级 UI 组件库 |
| Tailwind CSS 4 | 原子化 CSS 样式管理 |
| Redux Toolkit | 全局状态管理 |
| Axios | HTTP 请求 |

### 前端 — `tricore-web-rust`（Vue 3 + Rust 工具链）

| 技术 | 用途 |
|------|------|
| Rsbuild / Rspack | Rust 编写的极速构建工具 |
| Vue 3 | 渐进式 UI 框架 |
| TypeScript | 类型安全 |
| Vue Router | 客户端路由 |
| Ant Design Vue 4 | 企业级 UI 组件库 |
| Tailwind CSS 4 | 原子化 CSS 样式管理 |
| Pinia | Vue 3 官方状态管理 |
| Axios | HTTP 请求 |
| ECharts | 数据可视化图表（饼图/柱状图等） |
| marked | Markdown 解析渲染 |

### 后端 — `tricore-server`

| 技术 | 用途 |
|------|------|
| Actix-web | 高性能 HTTP 框架 |
| SQLx | 异步 PostgreSQL 驱动 |
| Serde | 序列化 / 反序列化 |
| Tokio | 异步运行时 |
| dotenvy | 环境变量加载 |
| bcrypt | 密码哈希 |
| jsonwebtoken | JWT 认证（HS256，24h 有效期） |
| reqwest | HTTP 客户端，调用外部 AI API |
| actix-multipart | 文件上传支持 |
| futures-util | 异步流处理（multipart 字段读取） |

### AI 助手

| 技术 | 用途 |
|------|------|
| Anthropic Messages API | Claude 系列模型（Sonnet/Opus/Haiku） |
| OpenAI Chat Completions API | DeepSeek（V3/V4 Pro/V4 Flash/R1）/ GPT-4o 等 |
| Function Calling / Tool Use | 5 个通用工具（数据查询 + API 调用），支持自主数据分析与任务执行 |
| 双格式自动适配 | 自动检测 API 类型并转换请求/响应格式 |
| Markdown 渲染 | AI 回复自动解析为富文本（列表/代码块/表格等） |
| 浮动面板 UI | 右下角弹出式聊天窗口，可一键放大，不遮挡操作 |
| 可配置系统提示词 | 自定义 AI 助手行为和知识范围 |

---

## 项目结构

```
TriCore/
├── README.md
├── tricore-web/                       # React 前端
│   ├── src/
│   │   ├── layouts/MainLayout.tsx     # 侧边栏 + 顶栏布局
│   │   ├── pages/
│   │   │   ├── dashboard/             # 工作台
│   │   │   ├── sales/                 # 销售管理
│   │   │   ├── oa/                    # 办公协同
│   │   │   └── inventory/            # 库存管理
│   │   ├── store/                     # Redux 状态
│   │   ├── services/api.ts           # API 层
│   │   └── styles/global.css         # 全局样式
│   └── vite.config.ts
├── tricore-web-rust/                  # Vue 3 前端（主力开发）
│   ├── src/
│   │   ├── layouts/MainLayout.vue     # 侧边栏菜单 + 顶栏用户信息
│   │   ├── pages/
│   │   │   ├── login/                 # 登录页（JWT 认证）
│   │   │   ├── dashboard/             # 工作台（统计卡片 + 图表 + 快捷入口）
│   │   │   ├── sales/                 # 销售管理（订单 + 商品 + 分类）
│   │   │   ├── oa/                    # 办公协同（审批 + 员工）
│   │   │   ├── inventory/            # 库存管理（库存调整 + 出入库 + 问题追踪）
│   │   │   ├── regulations/          # 规章制度（文件上传 + 分类管理）
│   │   │   ├── ai/                   # AI 管理（配置 + MCP + 对话）
│   │   │   ├── master-data/          # 基础数据（客户 + 部门 + 职位 + 车辆 + 用户 + 仓库）
│   │   │   └── data-snapshots/       # 数据快照（自动备份 + 恢复）
│   │   ├── stores/                    # Pinia 状态管理
│   │   │   ├── auth.ts / inventory.ts / oa.ts / sales.ts
│   │   ├── components/                # 公共组件
│   │   │   └── AiFloatingChat.vue     # AI 浮动对话面板（SSE 实时推理）
│   │   ├── services/                  # API 层（按模块拆分）
│   │   │   ├── http.ts               # Axios 实例 + JWT 拦截器
│   │   │   ├── auth.ts / sales.ts / oa.ts / inventory.ts
│   │   │   ├── regulations.ts / master-data.ts / ai.ts
│   │   │   └── data-snapshots.ts
│   │   ├── router/index.ts           # 路由配置 + beforeEach 认证守卫
│   │   └── styles/global.css         # 全局样式 + Ant Design 主题覆盖
│   ├── rsbuild.config.ts
│   └── postcss.config.mjs
└── tricore-server/                    # Rust 后端
    ├── src/
    │   ├── modules/                    # 业务模块（按领域组织）
    │   │   ├── ai/                     #   models.rs + handlers.rs + routes.rs
    │   │   ├── auth/                   #   认证模块
    │   │   ├── sales/ / oa/ / inventory/
    │   │   ├── master_data/ / regulation/
    │   │   ├── data_snapshot/          #   数据快照
    │   │   └── mcp/                    #   MCP 客户端
    │   ├── auth.rs                    # JWT 创建/验证 + 全局认证中间件
    │   ├── db.rs                      # 连接池 + 全量表自动创建 + 增量升级 + 种子数据
    │   ├── dto.rs                     # 共享 DTO（ApiResponse / PaginationParams）
    │   ├── error.rs                   # 统一错误处理（含 401）
    │   ├── config.rs                  # 环境变量 + 快照间隔配置
    │   └── main.rs                    # 入口 + 后台任务（快照 / MCP 刷新）
    ├── .env
    └── Cargo.toml
```

---

## 数据库

### 核心表

| 表名 | 模块 | 说明 |
|------|------|------|
| `users` | Sales | 用户（客户/销售/商户角色） |
| `products` | Sales / Inventory | 商品（共享） |
| `categories` | Sales | 商品分类 |
| `orders` + `order_items` | Sales | 订单 + 明细 |
| `bundle_sales` + `bundle_items` | Sales | 捆绑销售 |
| `return_orders` + `return_items` | Sales | 退单 |
| `employees` | OA | 员工（含 role 字段，用于系统登录） |
| `workflow_forms` + `workflow_steps` | OA | 审批流程 + 步骤 |
| `workflow_archives` | OA | 流程归档 |
| `warehouses` | Inventory | 仓库 |
| `warehouse_inventory` | Inventory | 仓库库存（商品-仓库多对多） |
| `stock_in_records` + `stock_in_items` | Inventory | 入库单 |
| `stock_out_records` + `stock_out_items` | Inventory | 出库单 |
| `issues` | Inventory | 问题追踪 |
| `customers` | Master Data | 客户主数据 |
| `departments` | Master Data | 部门 |
| `positions` | Master Data | 职位 |
| `vehicles` | Master Data | 车辆 |
| `regulation_categories` | Regulations | 文件分类 |
| `regulation_files` | Regulations | 规章制度文件 |
| `workflow_templates` | OA | 流程架构模板（steps JSONB） |
| `ai_configs` | AI | AI 配置（单行，CHECK id=1） |
| `mcp_servers` | AI | MCP 外部服务连接配置 |
| `data_snapshots` | 系统 | 数据库快照（定时备份，JSONB 存储，最多 12 条） |

> 注：`orders` 表通过 `ALTER TABLE ADD COLUMN IF NOT EXISTS` 增量新增了 `discounts JSONB` 列（折扣明细持久化）；`order_items` 表新增了 `warehouse_allocations JSONB` 列（仓库分配数据）。

### 种子数据

首次启动时自动创建（如果数据为空）：
- 管理员账号：`admin` / `admin123`
- 默认仓库：「默认仓库」
- AI 配置默认行（API Key 为空，需手动配置）
- 默认仓库：「默认仓库」

### Schema 管理

后端 `db.rs` 在每次启动时执行幂等 SQL（`CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN IF NOT EXISTS`），确保 schema 始终是最新状态。新增表/列直接在 `db.rs` 中追加即可。

---

## API 路由

所有路由（除 `/api/auth/login`）需携带 `Authorization: Bearer <token>` 认证头。

### Auth — `/api/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/login` | 员工登录，返回 JWT + 用户信息 |
| GET | `/me` | 获取当前登录用户信息 |

### Sales — `/api/sales`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/products` | 商品列表 |
| POST/PUT | `/products`, `/products/{id}` | 新增/编辑商品 |
| GET | `/orders` | 订单列表 |
| POST | `/orders` | 创建订单（校验库存并扣减） |
| PUT | `/orders/{id}` | 编辑订单（支持修改全部信息，含库存回滚/重扣） |
| PATCH | `/orders/{id}/status` | 变更状态（取消→恢复库存，发货→生成出库单） |
| GET/POST | `/bundles`, `/returns` | 捆绑销售 / 退单 |
| GET/POST/PUT/DELETE | `/categories` | 商品分类 CRUD |
| GET | `/dashboard` | 销售仪表盘 |

### OA — `/api/oa`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/employees`, `/employees/{id}` | 员工 CRUD |
| PUT/DELETE | `/employees/{id}` | 编辑/删除员工 |
| GET/POST | `/workflows`, `/workflows/{id}` | 流程 CRUD |
| PUT/DELETE | `/workflows/{id}` | 编辑/删除流程 |
| POST | `/workflows/{id}/submit` | 提交/重新提交流程 |
| POST | `/workflows/{id}/steps/{step}/review` | 审核步骤（支持 `reject_mode`: full/node） |
| GET/POST | `/templates` | 流程架构模板列表/创建 |
| PUT/DELETE | `/templates/{id}` | 编辑/删除架构模板 |
| GET | `/dashboard` | OA 仪表盘 |

### Inventory — `/api/inventory`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/products` | 库存商品列表 |
| GET/POST | `/stock-in` | 入库单列表/创建 |
| PUT | `/stock-in/{id}/verify`, `/complete` | 盘点/完成入库 |
| GET/POST | `/stock-out` | 出库单列表/创建 |
| PUT | `/stock-out/{id}/ship`, `/deliver` | 发货/送达 |
| GET/POST/PUT | `/issues` | 问题追踪 CRUD |
| PUT | `/issues/{id}/resolve` | 解决问题 |
| GET/POST/PUT/DELETE | `/warehouses` | 仓库 CRUD |
| GET | `/warehouse-inventory/{product_id}` | 查询商品在各仓库的库存分布 |
| POST | `/adjust` | 批量仓库库存调整（自动生成出入库单） |

### Master Data — `/api/master-data`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/customers` | 客户列表/新增 |
| PUT/DELETE | `/customers/{id}` | 编辑/删除客户 |
| GET/POST | `/departments` | 部门列表/新增 |
| PUT/DELETE | `/departments/{id}` | 编辑/删除部门 |
| GET/POST | `/positions` | 职位列表/新增 |
| PUT/DELETE | `/positions/{id}` | 编辑/删除职位 |
| GET/POST | `/vehicles` | 车辆列表/新增 |
| PUT/DELETE | `/vehicles/{id}` | 编辑/删除车辆 |

### Regulations — `/api/regulations`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/categories` | 文件分类列表/新增 |
| DELETE | `/categories/{id}` | 删除分类 |
| GET | `/files` | 文件列表（支持 `?title=` + `?category_id=` 筛选） |
| POST | `/files` | 上传文件（multipart，50MB 限制） |
| PUT | `/files/{id}` | 更新文件元数据 |
| DELETE | `/files/{id}` | 删除文件（DB + 磁盘） |
| GET | `/files/{id}/download` | 下载/预览文件 |

### AI — `/api/ai`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/config` | 获取 AI 配置（API Key、模型、地址） |
| PUT | `/config` | 更新 AI 配置 |
| POST | `/chat` | AI 对话（5 个内置工具 + MCP 外部工具，支持流式 SSE 响应：`{"stream":true}`，多轮自主分析与任务执行） |

### MCP — `/api/mcp`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/servers` | MCP 服务列表 |
| POST | `/servers` | 添加 MCP 服务（stdio/SSE） |
| PUT | `/servers/{id}` | 编辑 MCP 服务 |
| DELETE | `/servers/{id}` | 删除 MCP 服务 |
| GET | `/tools` | 查看已发现的 MCP 工具 |
| POST | `/refresh` | 刷新 MCP 工具列表 |

### Data Snapshots — `/api/data-snapshots`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/data-snapshots` | 快照列表（元数据） |
| POST | `/data-snapshots` | 手动创建快照 |
| POST | `/data-snapshots/{id}/restore` | 恢复快照（需 `{confirm:true}`） |
| DELETE | `/data-snapshots/{id}` | 删除快照 |

---

## 快速开始

### 1. 启动后端

```bash
cd tricore-server
# 创建 uploads 目录（可选，后端会自动创建）
cargo run
# 服务启动在 http://localhost:8080
# 首次启动自动创建所有数据库表和种子数据
```

### 2. 启动前端（Vue 3 — 主力开发）

```bash
cd tricore-web-rust
npm install
npm run dev
# 开发服务器启动在 http://localhost:5174
```

### 3. 配置 AI 助手（可选）

访问「AI 管理 → AI 配置」，填入 API Key 和选择模型即可启用浮动 AI 对话助手。

### 4. 启动前端（React — 已弃用，不再维护）

```bash
cd tricore-web
npm install
npm run dev
# 开发服务器启动在 http://localhost:5173
```

---

## 功能模块

### 认证系统 (Auth)

- **登录页**：工号 + 密码登录，柔和渐变背景 + 浮动光晕动画，暗色/亮色双主题
- **JWT 认证**：HS256 签名，24h 有效期，全局路由守卫 + Axios 拦截器自动附 Token
- **权限控制**：后端全局中间件拦截未认证请求（除登录接口），401 自动跳转登录页
- 右上角用户信息 Popover（工号/部门/职位/邮箱/电话）+ 退出登录按钮

### 工作台 (Dashboard)

- 六张统计卡片（销售订单、在职员工、商品种类、待审流程、库存预警、规章制度文件数），图标 + 数值 + 趋势标签，hover 上浮动画
- **ECharts 数据图表**：订单状态环形饼图 + 商品库存横向柱状图（红黄绿三级预警着色）
- **暗色/亮色双主题自适应**：图表跟随系统主题自动切换配色，文字/网格线/柱色均适配
- 信息概览栏（本月入库/出库量、待解决问题数、系统运行状态）
- **6 模块快捷入口**：销售管理、办公协同、库存管理、基础数据、规章制度、AI 助手，点击跳转

### 销售管理 (Sales)

- **订单管理**：创建订单（客户/配送车辆下拉 + 按仓库分配商品数量 + 折扣叠加百分比/固定金额/备注）、订单详情（卡片式布局，含客户信息/金额算式/商品明细/各仓库当前库存）、订单编辑（完整还原创建时全部信息含仓库分配）、状态流转（取消→恢复双库存，发货→生成出库单）
- **商品管理**：SKU 自动生成、价格、库存、分类下拉（关联分类管理数据）
- **商品分类管理**：独立的增删改查 Tab
- 待处理订单可编辑车辆/备注

### 办公协同 (OA)

- **审批流程**：多步骤流程创建、提交、审核（通过/退回）、被退回流程修改后重新提交、删除
- **顺序审批**：后置步骤必须等前置全部通过才能审核，后端严格校验
- **双退回模式**：完全退回（重置全部步骤从头审批）和本结点退回（已通过步骤保留，仅退回当前节点）
- **流程架构配置**：保存常用审批模板（名称 + 描述 + 审核步骤），新建流程时一键套用
- **员工管理**：工号自动生成、部门/职位下拉选择、增删改查

### 库存管理 (Inventory)

- **库存调整**：展示各仓库当前库存 + 可调目标数量 + 下拉选择仓库，系统自动判断 delta 生成入库单/出库单，备注关联到单据
- **库存列表**：总库存 = 各仓库 inventory 数量之和
- **入库/出库**：记录列表（含仓库列 + 详情按钮），可查看完整单据信息（商品明细/仓库/备注/时间）
- **问题追踪**：登记（自动填入报告人）、Modal 文本域解决、严重程度分类

### 基础数据 (Master Data)

侧边栏独立菜单，含六个子模块：

- **客户管理**：名称、联系人、电话、邮箱、地址
- **部门管理**：部门名称、描述
- **职位管理**：职位名称、关联部门
- **车辆管理**：车牌号、车型、载重、司机、状态（空闲/使用中/维护）
- **用户管理**：工号自动生成、部门/职位联动下拉（选部门后过滤职位）、密码、角色
- **仓库管理**：仓库名称、位置、启用状态

### 规章制度 (Regulations)

- **文件上传**：Ant Design `<a-upload>` 组件，multipart 上传，50MB 限制
- **文件管理**：文件列表，按文件名关键字 / 分类下拉筛选查询
- **分类管理**：弹窗式分类增删，支持关键字筛选，上传表单内嵌分类管理按钮，分类删除时关联文件自动变为未分类
- **文件预览**：Axios blob 下载（携带 JWT Token）→ Blob URL → `window.open`，浏览器内直接查看 PDF、图片等
- **侧边栏入口**：独立菜单项（FileTextOutlined 图标）

### AI 智能化方案

基于当前系统架构和 AI 技术发展趋势，规划以下三个阶段的 AI 集成方案：

---

#### 方案一：AI 对话助手 ✅ 已实现

**概述**：系统内常驻 AI 对话面板，通过 **Tool Use / Function Calling** 直接对接数据库和后端 API，用户以自然语言与系统交互、执行业务操作。

**能力示例**：
- *「本月销售额最高的 5 个订单是哪些？」* → AI 执行 SQL 聚合查询并总结
- *「库存低于 50 的商品有哪些？」* → 自动查询并预警
- *「帮我创建一个客户，名称叫 XX 科技」* → AI 调用 POST /master-data/customers 执行
- *「给这个订单关联配送司机张三」* → AI 调用 PUT /sales/orders/{id} 更新配送信息
- *「系统整体情况怎么样？」* → 获取 Dashboard 概览统计

**技术实现**：
- 后端 `/api/ai/chat` 接口，对接 Claude / DeepSeek / GPT-4o 等 API
- 5 个通用 Tool 函数：`list_tables` / `describe_table` / `run_query`（数据库只读分析）+ `list_apis` / `call_api`（后端接口调用）
- 前端 AI 对话组件（聊天气泡 UI，Markdown 富文本渲染）
- 可配置的模型选择、API Key、系统提示词
- 完整的 Tool Use 循环（最多 10 轮），AI 自主组合工具完成任务
- SQL 安全校验（仅允许 SELECT/WITH/EXPLAIN，防注入，10s 超时，自动 LIMIT）
- 用户 JWT 透传，所有 API 调用权限与前端一致

**优势**：改动最小，不侵入现有模块，一个入口覆盖全系统。

---

#### 方案二：规章制度 RAG（文档智能问答）

**概述**：针对「规章制度」模块，让用户直接对已上传的文件内容进行提问。

**能力示例**：
- *「安全规范中对仓库管理有什么要求？」* → AI 从规范文件中检索相关内容回答
- *「对比一下 A 文件和 B 文件中关于考勤的规定」* → 跨文件检索对比

**技术实现**：
- 文件上传时自动提取文本内容（PDF/Word/txt）并向量化存储
- 新增 `/api/ai/ask-document` 接口，基于 RAG（检索增强生成）回答
- 前端文件列表新增「提问」按钮
- 依赖：Embedding 模型 + 向量数据库（可用 PostgreSQL `pgvector` 扩展）

**预估工期**：2-3 天

---

#### 方案三：模块内嵌 AI 分析

**概述**：在各业务模块页面中嵌入 AI 分析卡片，提供主动式智能洞察。

**能力示例**：
- 销售管理：*「本周销售趋势」「商品关联分析」「异常订单检测」*
- 库存管理：*「库存周转分析」「缺货风险预警」「补货建议」*
- 办公协同：*「审批效率分析」「流程瓶颈识别」*
- 规章制度：*「文件摘要」「关键条款提取」*

**技术实现**：
- 各模块新增 `AIAnalysisCard` 组件
- 后端为每个模块提供分析 API（调用 LLM + 数据查询）
- 前端渲染 Markdown 分析结果

**预估工期**：3-5 天

---

#### 实施建议

| 阶段 | 方案 | 状态 | 投入产出比 |
|------|------|------|-----------|
| 第一阶段 | AI 对话助手 | ✅ 已完成 | ⭐⭐⭐⭐⭐ 最高 |
| 第二阶段 | 规章制度 RAG | 📋 待实施 | ⭐⭐⭐⭐ 高 |
| 第三阶段 | 模块内嵌 AI 分析 | 📋 待实施 | ⭐⭐⭐ 中 |

> **设计原则**：所有 AI 功能均通过后端中转调用外部 API，前端不直接暴露 API Key。配置持久化在数据库，UI 中可随时修改，无需重启服务。

---

## UI 设计特性

- 暗色/亮色主题切换（默认暗色）
- 毛玻璃卡片效果 + hover 发光边框
- 渐变动画标题文字
- 点阵科技感背景
- Ant Design 组件全主题覆盖（Menu、Table、Modal、Button、Tag、Tabs 等）
- 统一的 `page-header` / `glass-card` / `gradient-text` / `stat-icon-circle` 组件类
- ECharts 数据可视化图表（饼图/柱状图），暗亮双主题自适应
- 浮动 AI 对话面板（右下角弹出，可放大，Markdown 富文本渲染）
- 统计卡片 hover 上浮动画 + 模块快捷入口边框高亮过渡

---

## 更新日志

### 2026-08-06

#### 项目架构重构 — 模块化

- **后端重组**：旧 `models/` + `handlers/` + `routes/` 三层平铺结构 → `modules/{domain}/` 领域模块，每个模块内含 `models.rs` + `handlers.rs` + `routes.rs`，相关代码内聚，维护路径清晰
- **共享提取**：`dto.rs`（ApiResponse / PaginationParams）提取到 `src/` 根目录，跨模块引用统一为 `crate::dto::`
- **前端 API 分层**：旧单体 `services/api.ts`（190 行）拆分为 `http.ts`（Axios 实例 + 拦截器）+ 8 个领域文件（auth / sales / oa / inventory / regulations / master-data / ai / data-snapshots），按左侧菜单对应归类

#### 数据快照系统

- **自动定时备份**：后端 `data_snapshots` 表，每次备份完整保存 27 张业务表数据为 JSONB，含时间戳，后台 tokio 任务按 `SNAPSHOT_INTERVAL_SECS`（默认 3600s）自动执行
- **12 条上限**：超出时自动清除最旧记录，FIFO 策略
- **一键恢复**：前端快照管理页（`/data-snapshots`），支持查看、手动创建、恢复（事务内按 FK 依赖顺序删除+重插）、删除
- **安全机制**：`ai_configs`（含 API Key）排除不备份；恢复需 `confirm: true` 确认

#### AI 助手增强

- **推理过程实时展示**：后端 SSE 流式推送 → 前端 ReadableStream 逐条消费，工具调用（查数据库/调 API）在分析过程中逐个出现，分析过程默认展开并排在最终回复上方
- **推理内容返回**：非流式模式下 `ChatResponse` 新增 `reasoning` 字段，包含每步工具调用的名称、参数、结果
- **API 错误处理**：`call_anthropic` / `call_openai` 增加 HTTP 状态码检查，4xx/5xx 返回真实错误信息而非误导性「空响应」
- **表名纠错**：系统提示词强化实际表名说明 + `run_query` 错误信息引导调用 `list_tables` 修正，避免 AI 编造不存在的表名导致循环卡死
- **全屏独立对话页**：`/ai/chat` 为顶层独立路由（脱离 MainLayout），`position:fixed` 全视口布局，浮动面板通过「新窗口」按钮打开

#### MCP 集成框架

- **MCP Client**：新增 `modules/mcp/` 模块，支持 stdio（本地子进程 JSON-RPC）和 SSE（远程 HTTP）两种传输方式连接外部 MCP Server
- **AI 工具扩展**：`build_tools()` 动态追加 MCP 工具（`mcp:` 前缀），`execute_tool()` 自动路由到 `client::call_tool()`；服务启动时自动刷新
- **前端管理**：`/ai/mcp` 独立页面，服务列表（名称/传输/启停/编辑删除）+ 工具发现展示
- **数据库**：新增 `mcp_servers` 表

#### 前端优化

- AI 管理页拆分为「AI 配置」和「MCP 服务」两个独立子页面（侧边栏 AI 管理下子菜单）
- 全屏对话框滚动修复：移除 Spin 包裹导致的 flex 布局链断裂
- Tailwind 样式改为内联 style 避免与 Ant Design 组件冲突

### 2026-07-29

#### AI 助手重大升级 — 从"只读分析"到"任务执行"

- **工具系统重构**：从 7 个硬编码查询工具升级为 3 个数据库通用工具（`list_tables` / `describe_table` / `run_query`）+ 2 个 API 调用工具（`list_apis` / `call_api`），AI 可组合使用覆盖全部业务场景
- **run_query — 动态 SQL 分析**：AI 可执行任意 SELECT 查询（JOIN / GROUP BY / 聚合 / 子查询），结果以 Markdown 表格返回；内置 SQL 安全校验（仅允许 SELECT/WITH/EXPLAIN，防多语句注入，10s 超时，自动 LIMIT 100），动态适配 PostgreSQL 全部常见列类型
- **call_api — 后端接口调用**：AI 可调用任意后端 API 执行创建/更新/删除等写操作；通过提取用户 JWT 令牌 + 内部 HTTP 透传实现认证，权限与前端操作完全一致；禁止递归调用 `/ai/chat` 和绕过 `/auth/login`
- **list_apis — 完整 API 目录**：内置约 60 个后端接口的完整目录（方法/路径/必填字段），AI 可根据用户意图自行查找匹配的 API
- **任务式对话流程**：AI 收到任务后自动理解意图 → 查 API → 缺信息时主动向用户提问 → 补齐后执行 → 反馈结果，不再默默略过可选字段
- **Tool Use 轮次上限**: 5 → 10，适配多工具组合使用场景
- **max_tokens**: 2048 → 4096，适配更长的工具响应和对话上下文

#### Bug 修复

- **编辑订单 — 数量和优惠不回显**：`get_order` 返回 `{order, items}` 嵌套结构，前端 `openOrderEdit` 误当扁平对象使用导致 `id`/`discounts`/`vehicle_info` 全部为 `undefined`；修复为解构后扁平化 `{...data.order, items: data.items}`
- **编辑订单 — final_amount 覆盖 bug**：`update_order` 存在两次 UPDATE 查询，第二步用 `existing.total_amount`（旧值）通过 COALESCE 覆盖了第一步 if-items 分支正确计算的新 final_amount；修复为合并为单次 UPDATE，if/else 两分支统一计算 total/discount/final 后一次写入
- **AI 创建订单不关联配送信息**：`list_apis` 和系统提示词均未引导 AI 询问用户配送车辆/司机；修复为 API 目录和提示词中明确标注应主动询问

### 2026-07-28

#### AI 助手

- **AI 对话助手**：浮动按钮触发（右下角），弹出式聊天面板（440×520，支持一键放大至 720×680），聊天气泡 UI + 滑入动画，面板完全与页面内容叠加不遮挡操作
- **自然语言数据查询**：基于 Function Calling 实现内置工具，AI 自动选择合适的工具调用后端查询数据库，基于最新数据生成分析回答
- **双 API 格式兼容**：自动检测 API 类型，Anthropic Messages API（Claude/Claude Opus/Claude Haiku）和 OpenAI Chat Completions API（DeepSeek V3/V4 Pro/V4 Flash/R1/OpenAI 兼容代理）均无缝支持，Tool Use / Tool Calls 双向转换透明处理
- **Markdown 富文本渲染**：AI 回复自动解析 Markdown 格式（粗体/列表/代码块/表格/引用/标题），用户消息保持纯文本
- **可配置模型**：DeepSeek V4 Pro (1m)、DeepSeek V4 Flash、DeepSeek V3、DeepSeek R1、Claude Sonnet/Opus/Haiku、GPT-4o 等
- **AI 配置页面**：API Key（可切换显示）、模型选择、API 地址、自定义系统提示词，居中卡片式 UI，配置持久化在数据库即时生效
- **AI 智能化方案文档**：README 补充完整的三阶段 AI 战略路线图（AI 对话助手 ✅ / 规章制度 RAG 📋 / 模块内嵌分析 📋）

#### 工作台

- **ECharts 图表集成**：订单状态环形饼图 + 商品库存横向柱状图（红黄绿三级预警着色），暗色/亮色双主题自适应，切换主题时图表自动销毁重建
- **6 模块快捷入口**：销售管理、办公协同、库存管理、基础数据、规章制度、AI 助手，hover 上浮 + 边框高亮动画，点击直接跳转
- **信息概览栏**：本月入库/出库量、待解决问题数、系统运行状态标签
- **统计卡片增强**：6 张卡片（销售订单、在职员工、商品种类、待审流程、库存预警、规章制度文件数），图标 + 数值 + 趋势标签

#### 规章制度

- **文件管理**：multipart 文件上传（50MB 限制）、文件列表、按文件名关键字 / 分类下拉筛选
- **分类管理**：弹窗式分类增删，支持关键字筛选，上传表单内嵌分类管理按钮
- **文件预览**：使用 `axios` blob 下载（携带 JWT token）创建 Blob URL 后浏览器内直接预览 PDF、图片等，避免直接拼接 URL 导致的 401 认证失败
- **UI 优化**：文件上传改为 Ant Design `<a-upload>` 组件，搜索输入框样式统一，分类 Modal 层级修复（zIndex 覆盖上传弹窗）

#### 审批流程增强

- **顺序审批**：后置步骤必须等前置步骤全部通过才能审核，后端严格校验
- **双退回模式**：完全退回（重置全部步骤，重新从头审批）和本结点退回（已通过步骤保留，仅退回当前节点，重新提交后直达退回节点）
- **流程架构配置**：保存常用审批模板（名称 + 描述 + 审核步骤 JSONB），新建流程时一键套用标题/描述/步骤，架构支持编辑和删除
- **创建流程优化**：描述字段改为 `TextArea` 文本域（3 行），新增「使用流程架构」按钮弹窗选择模板

#### 销售管理

- **订单编辑完善**：编辑时完整带出创建时的仓库分配数量（动态加载当前库存并合并保存的分配数据）、折扣明细（后端 `orders.discounts` JSONB 列持久化）、车辆司机信息（通过车牌号匹配下拉选项）
- **订单详情仓库分配**：详情页优先展示 `warehouse_allocations` 原始分配记录，回退显示各仓库当前库存
- **库存数据修正**：修复「水」商品总库存与仓库库存合计不一致的问题（`products.quantity` 与 `SUM(warehouse_inventory.quantity)` 对齐）

#### 后端基础设施

- **新增依赖**：`actix-multipart`、`futures-util`、`reqwest`
- **新增表**：`regulation_categories`、`regulation_files`、`workflow_templates`、`ai_configs`、`orders.discounts`（ALTER TABLE ADD COLUMN）
- **API 路由**：`/api/regulations/*`（7 个端点）、`/api/ai/*`（3 个端点）、`/api/oa/templates/*`（4 个端点）
- **DB Schema 管理**：`ai_configs` 单行配置表（CHECK id=1）+ 首次启动自动种子默认值

### 2026-07-23

- **仓库级库存系统**：新增 `warehouse_inventory` 表（商品-仓库多对多），`complete_stock_in` / `create_stock_out` / `create_order` / `update_order` / 取消订单均同步维护双库存
- **库存调整重新设计**：商品层 → 仓库层，展示各仓库当前库存 + 可调目标数量 + 下拉选择仓库，根据 delta 正负自动生成入库单/出库单，备注关联到单据
- **订单创建按仓库分配**：选择商品后自动加载各仓库可用库存，逐仓填写分配数量，后端精准从指定仓库扣减
- **订单编辑完整化**：编辑界面与创建完全一致（含仓库分配数据），数据通过 `warehouse_allocations` JSONB 列持久化，支持修改全部信息并回滚/重扣库存
- **订单详情 UI 重新设计**：卡片式布局，分基本信息/客户/配送/金额算式/商品明细（含各仓库当前库存）/备注六个区域
- **入库/出库详情 Modal**：列表新增「详情」按钮，展示单据信息、商品明细、仓库、备注、时间
- **优惠顺序计算修复**：多个优惠项从前向后依次应用于前一结果，而非全部基于原始总额
- **商品选择限制**：库存为 0 的商品不可选；数量输入框受库存上限约束
- **Schema 管理清理**：移除不安全的旧 SQL 迁移文件，由 `db.rs` 统一管理（`CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN IF NOT EXISTS`）
- **后端审计 + 修复**：全量 schema 与模型 100% 对齐验证，86 条路由全部 handler 覆盖，CORS 预检被认证中间件拦截 bug 修复
- **数据库清理**：清空旧种子测试数据，重建管理员账号 `admin/123456`

### 2026-07-22

- **认证系统**：新增 JWT 登录认证（后端 `jsonwebtoken` + 全局中间件拦截，前端 Pinia Store + 路由守卫 + Axios 拦截器），默认管理员 `admin/admin123` 自动种子
- **登录页面**：柔和渐变背景 + 浮动光晕动画，暗色/亮色双主题，毛玻璃卡片风格
- **用户管理**：基础数据新增「用户管理」Tab，工号自动生成、部门/职位联动下拉、角色设置
- **商品分类管理**：销售管理新增「商品分类」Tab，支持增删改；商品新增时 SKU 自动生成，分类下拉关联分类数据
- **仓库管理**：基础数据新增「仓库管理」Tab，支持增删改；库存调整模态框新增仓库选择器；首次启动自动种子默认仓库
- **销售订单增强**：客户下拉关联客户管理数据、配送车辆下拉关联车辆管理数据（自动填入车牌/司机）；优惠支持叠加（百分比 + 固定金额 + 备注）；模态框加宽至 880px
- **库存管理优化**：入库/出库/问题表格列宽大幅放宽（size "middle"）；入库/出库单号列宽增至 190px；问题解决改为 Modal 文本域输入；登记问题自动填入报告人
- **状态流转完善**：订单取消时自动恢复库存（`UPDATE products SET quantity = quantity + n`）；状态变更模态框精简（移除车辆信息字段）
- **数据库**：`db.rs` 升级至全部 24 张表自动创建（含 `categories`、`employees`、`users` 等），不再依赖手动执行 SQL 文件
- **后端接口**：新增 `/api/auth/login`、`/api/auth/me`、`/api/sales/categories` CRUD、`/api/inventory/warehouses` DELETE
- **环境配置**：新增 `JWT_SECRET` 环境变量，数据库连接切换至本地 `postgres://postgres:123456@localhost:5432/tricore`

### 2026-07-10

- **基础数据模块**：新增客户/部门/职位/车辆管理，独立侧边栏菜单
- **销售管理**：订单支持多商品行、配送车辆、库存校验与扣减、状态流转、发货自动生成出库单
- **办公协同**：审批支持多步骤（拖动排序）、提交/审核/退回/修改/重新提交/删除；员工 CRUD
- **库存管理**：一键库存调整自动生成出入库记录、登记/解决问题
- **UI**：整体设计升级——玻璃拟态、渐变动画、点阵背景、全组件主题覆盖、亮暗双主题
- **后端**：db.rs 启动时自动修复 schema，不再依赖 sqlx::migrate 校验和
- **修复**：Tailwind 与 Ant Design 的 CSS 层级冲突、图标大小显示、菜单亮色主题对齐

### 2026-07-07

- 项目初始化，三个子项目骨架搭建
- Sales / OA / Inventory 基础 CRUD
- 数据库迁移 + 种子数据

---

## License

MIT
