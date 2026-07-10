# TriCore（三核）

> Sales + OA + Inventory + Master Data — 企业核心业务一体化解决方案

## 命名由来

| 维度 | 说明 |
|------|------|
| **Tri** | 三大系统：**Sales**（销售管理）+ **OA**（办公协同）+ **Inventory**（库存管理） |
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

### 后端 — `tricore-server`

| 技术 | 用途 |
|------|------|
| Actix-web | 高性能 HTTP 框架 |
| SQLx | 异步 PostgreSQL 驱动 |
| Serde | 序列化 / 反序列化 |
| Tokio | 异步运行时 |
| dotenvy | 环境变量加载 |
| bcrypt | 密码哈希 |

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
│   │   │   ├── dashboard/             # 工作台（统计卡片 + 模块概览）
│   │   │   ├── sales/                 # 销售管理（订单 + 商品）
│   │   │   ├── oa/                    # 办公协同（审批 + 员工）
│   │   │   ├── inventory/            # 库存管理（库存调整 + 出入库 + 问题追踪）
│   │   │   └── master-data/          # 基础数据（客户 + 部门 + 职位 + 车辆）
│   │   ├── router/index.ts           # 路由配置
│   │   ├── services/api.ts           # API 层
│   │   └── styles/global.css         # 全局样式 + Ant Design 主题覆盖
│   ├── rsbuild.config.ts
│   └── postcss.config.mjs
└── tricore-server/                    # Rust 后端
    ├── src/
    │   ├── routes/                    # 路由：sales / oa / inventory / master_data
    │   ├── handlers/                  # 请求处理器
    │   ├── models/                    # 数据模型 + DTO
    │   ├── db.rs                      # 连接池 + schema 自动修复
    │   ├── error.rs                   # 统一错误处理
    │   ├── config.rs                  # 环境变量配置
    │   └── main.rs                    # 入口
    ├── migrations/                    # SQL 迁移文件（参考用，不再由 sqlx::migrate 执行）
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
| `orders` + `order_items` | Sales | 订单 + 明细 |
| `bundle_sales` + `bundle_items` | Sales | 捆绑销售 |
| `return_orders` + `return_items` | Sales | 退单 |
| `employees` | OA | 员工 |
| `workflow_forms` + `workflow_steps` | OA | 审批流程 + 步骤 |
| `workflow_archives` | OA | 流程归档 |
| `warehouses` | Inventory | 仓库 |
| `stock_in_records` + `stock_in_items` | Inventory | 入库单 |
| `stock_out_records` + `stock_out_items` | Inventory | 出库单 |
| `issues` | Inventory | 问题追踪 |
| `customers` | Master Data | 客户主数据 |
| `departments` | Master Data | 部门 |
| `positions` | Master Data | 职位 |
| `vehicles` | Master Data | 车辆 |

### Schema 管理

后端 `db.rs` 在每次启动时执行幂等 SQL（`CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN IF NOT EXISTS`），确保 schema 始终是最新状态，不依赖 `sqlx::migrate`。

---

## API 路由

### Sales — `/api/sales`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/products` | 商品列表 |
| POST/PUT | `/products`, `/products/{id}` | 新增/编辑商品 |
| GET | `/orders` | 订单列表 |
| POST | `/orders` | 创建订单（校验库存并扣减） |
| PUT | `/orders/{id}` | 编辑待处理订单 |
| PATCH | `/orders/{id}/status` | 变更状态（发货时自动生成出库单） |
| GET/POST | `/bundles`, `/returns` | 捆绑销售 / 退单 |
| GET | `/dashboard` | 销售仪表盘 |

### OA — `/api/oa`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/employees`, `/employees/{id}` | 员工 CRUD |
| PUT/DELETE | `/employees/{id}` | 编辑/删除员工 |
| GET/POST | `/workflows`, `/workflows/{id}` | 流程 CRUD |
| PUT/DELETE | `/workflows/{id}` | 编辑/删除流程 |
| POST | `/workflows/{id}/submit` | 提交/重新提交流程 |
| POST | `/workflows/{id}/steps/{step}/review` | 审核步骤 |
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
| GET | `/warehouses` | 仓库列表 |

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

---

## 快速开始

### 1. 启动后端

```bash
cd tricore-server
cargo run
# 服务启动在 http://localhost:8080
```

### 2. 启动前端（Vue 3 — 主力开发）

```bash
cd tricore-web-rust
npm install
npm run dev
# 开发服务器启动在 http://localhost:5174
```

### 3. 启动前端（React）

```bash
cd tricore-web
npm install
npm run dev
# 开发服务器启动在 http://localhost:5173
```

---

## 功能模块

### 工作台 (Dashboard)

- 六张统计卡片（销售订单、员工数量、商品种类、待处理流程、库存预警、本月完成）
- 数字计数动画
- 三大核心模块概览

### 销售管理 (Sales)

- **订单管理**：创建订单（多商品行 + 配送车辆 + 库存校验扣减）、订单详情、状态流转（待处理 → 已确认 → 处理中 → 已发货 → 已交付）、发货时自动生成出库单
- **商品管理**：SKU、价格、库存、分类的增删改查
- 待处理订单可编辑车辆/备注，可删除

### 办公协同 (OA)

- **审批流程**：多步骤流程创建（支持拖动排序审核人）、提交、审核（通过/退回）、被退回流程修改后重新提交、删除
- **员工管理**：工号自动生成、部门/职位下拉选择、增删改查
- 顶部用户信息卡片（hover 展开详情）

### 库存管理 (Inventory)

- **库存调整**：每项商品一键调整数量，自动生成入库/出库记录
- **入库/出库**：记录列表查看
- **问题追踪**：登记、解决、严重程度分类

### 基础数据 (Master Data)

侧边栏独立菜单，含四个子模块：

- **客户管理**：名称、联系人、电话、邮箱、地址
- **部门管理**：部门名称、描述
- **职位管理**：职位名称、所属部门
- **车辆管理**：车牌号、车型、载重、司机、状态（空闲/使用中/维护）

---

## UI 设计特性

- 暗色/亮色主题切换（默认暗色）
- 毛玻璃卡片效果 + hover 发光边框
- 渐变动画标题文字
- 点阵科技感背景
- Ant Design 组件全主题覆盖（Menu、Table、Modal、Button、Tag、Tabs 等）
- 统一的 `page-header` / `glass-card` / `gradient-text` 组件类

---

## 更新日志

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
