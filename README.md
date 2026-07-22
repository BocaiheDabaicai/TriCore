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
| jsonwebtoken | JWT 认证（HS256，24h 有效期） |

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
│   │   │   ├── dashboard/             # 工作台（统计卡片 + 模块概览）
│   │   │   ├── sales/                 # 销售管理（订单 + 商品 + 分类）
│   │   │   ├── oa/                    # 办公协同（审批 + 员工）
│   │   │   ├── inventory/            # 库存管理（库存调整 + 出入库 + 问题追踪）
│   │   │   └── master-data/          # 基础数据（客户 + 部门 + 职位 + 车辆 + 用户 + 仓库）
│   │   ├── stores/                    # Pinia 状态管理
│   │   │   ├── auth.ts               # 认证 Store（登录/登出/Token）
│   │   │   ├── inventory.ts
│   │   │   ├── oa.ts
│   │   │   └── sales.ts
│   │   ├── router/index.ts           # 路由配置 + beforeEach 认证守卫
│   │   ├── services/api.ts           # API 层 + JWT 拦截器
│   │   └── styles/global.css         # 全局样式 + Ant Design 主题覆盖
│   ├── rsbuild.config.ts
│   └── postcss.config.mjs
└── tricore-server/                    # Rust 后端
    ├── src/
    │   ├── routes/
    │   │   ├── auth.rs                # 认证路由（登录/当前用户）
    │   │   ├── sales.rs               # 销售 + 商品分类
    │   │   ├── oa.rs
    │   │   ├── inventory.rs
    │   │   └── master_data.rs
    │   ├── handlers/                  # 请求处理器
    │   ├── models/                    # 数据模型 + DTO
    │   ├── auth.rs                    # JWT 创建/验证 + 全局认证中间件
    │   ├── db.rs                      # 连接池 + 全部 24 张表自动创建 + 种子数据
    │   ├── error.rs                   # 统一错误处理（含 401）
    │   ├── config.rs                  # 环境变量（含 JWT_SECRET）
    │   └── main.rs                    # 入口（挂载认证中间件）
    ├── migrations/                    # SQL 迁移文件（参考用）
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
| `stock_in_records` + `stock_in_items` | Inventory | 入库单 |
| `stock_out_records` + `stock_out_items` | Inventory | 出库单 |
| `issues` | Inventory | 问题追踪 |
| `customers` | Master Data | 客户主数据 |
| `departments` | Master Data | 部门 |
| `positions` | Master Data | 职位 |
| `vehicles` | Master Data | 车辆 |

### 种子数据

首次启动时自动创建（如果数据为空）：
- 管理员账号：`admin` / `admin123`
- 默认仓库：「默认仓库」

### Schema 管理

后端 `db.rs` 在每次启动时执行幂等 SQL（`CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN IF NOT EXISTS`），确保 schema 始终是最新状态，不依赖 `sqlx::migrate`。

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
| PUT | `/orders/{id}` | 编辑待处理订单 |
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
| PUT | `/issues/{id}/resolve` | 解决问题 |
| GET/POST/PUT/DELETE | `/warehouses` | 仓库 CRUD |

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

### 认证系统 (Auth)

- **登录页**：工号 + 密码登录，柔和渐变背景 + 浮动光晕动画，暗色/亮色双主题
- **JWT 认证**：HS256 签名，24h 有效期，全局路由守卫 + Axios 拦截器自动附 Token
- **权限控制**：后端全局中间件拦截未认证请求（除登录接口），401 自动跳转登录页
- 右上角用户信息 Popover（工号/部门/职位/邮箱/电话）+ 退出登录按钮

### 工作台 (Dashboard)

- 六张统计卡片（销售订单、员工数量、商品种类、待处理流程、库存预警、本月完成）
- 员工数量实时反映数据库在职员工数
- 三大核心模块概览

### 销售管理 (Sales)

- **订单管理**：创建订单（客户/配送车辆下拉关联基础数据 + 多商品行 + 单位只读 + 折扣叠加百分比/固定金额 + 优惠备注）、订单详情、状态流转（取消时恢复库存，发货时生成出库单）
- **商品管理**：SKU 自动生成、价格、库存、分类下拉（关联分类管理数据）
- **商品分类管理**：独立的增删改查 Tab
- 待处理订单可编辑车辆/备注

### 办公协同 (OA)

- **审批流程**：多步骤流程创建、提交、审核（通过/退回）、被退回流程修改后重新提交、删除
- **员工管理**：工号自动生成、部门/职位下拉选择、增删改查

### 库存管理 (Inventory)

- **库存调整**：选择仓库 + 入库/出库调整，自动生成出入库记录
- **入库/出库**：记录列表查看，列宽宽松
- **问题追踪**：登记（自动填入报告人）、Modal 文本域解决、严重程度分类

### 基础数据 (Master Data)

侧边栏独立菜单，含六个子模块：

- **客户管理**：名称、联系人、电话、邮箱、地址
- **部门管理**：部门名称、描述
- **职位管理**：职位名称、关联部门
- **车辆管理**：车牌号、车型、载重、司机、状态（空闲/使用中/维护）
- **用户管理**：工号自动生成、部门/职位联动下拉（选部门后过滤职位）、密码、角色
- **仓库管理**：仓库名称、位置、启用状态

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
