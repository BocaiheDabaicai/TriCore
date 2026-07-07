# TriCore（三核）

> 🎯 **Sales + OA + Inventory** — 三大核心业务系统，一体化解决方案

## 命名由来

| 维度 | 说明 |
|------|------|
| 🎯 **Tri** | 三大系统：**Sales**（销售管理）+ **OA**（办公协同）+ **Inventory**（库存管理） |
| ⚡ **Core** | 聚焦核心业务，直击本质，不做 bloated SaaS |
| 🇨🇳 **中文名** | **三核** — 简洁有力，好记好传 |
| 🔤 **英文名** | `TriCore` — 短小精悍，适合包名、域名 |
| 🦀 **Rust 后端** | `tricore-server` — 高性能、内存安全 |
| ⚛️ **React 前端** | `tricore-web` — Vite + React + TypeScript |
| 🦀⚡ **Rust 前端** | `tricore-web-rust` — Rsbuild/Rspack + Vue 3 + TypeScript |
| 📦 **管理端** | `tricore-admin` — 统一管理后台 |

---

## 技术栈

### 前端 — `tricore-web`（React 技术栈）

| 技术 | 用途 |
|------|------|
| [Vite](https://vitejs.dev/) | 构建工具，极速 HMR |
| [React 19](https://react.dev/) | UI 框架 |
| [TypeScript](https://www.typescriptlang.org/) | 类型安全 |
| [React Router](https://reactrouter.com/) | 客户端路由 |
| [Ant Design](https://ant.design/) | 企业级 UI 组件库 |
| [Tailwind CSS](https://tailwindcss.com/) | 原子化 CSS 样式管理 |
| [Redux Toolkit](https://redux-toolkit.js.org/) | 全局状态管理 |
| [Axios](https://axios-http.com/) | HTTP 请求 |

### 前端 — `tricore-web-rust`（Vue 3 + Rust 工具链）

| 技术 | 用途 |
|------|------|
| [Rsbuild](https://rsbuild.dev/) | 基于 Rspack 的构建工具 |
| [Rspack](https://rspack.dev/) | Rust 编写的极速 bundler |
| [Vue 3](https://vuejs.org/) | 渐进式 UI 框架 |
| [TypeScript](https://www.typescriptlang.org/) | 类型安全 |
| [Vue Router](https://router.vuejs.org/) | 客户端路由 |
| [Ant Design Vue](https://antdv.com/) | 企业级 UI 组件库 |
| [Tailwind CSS](https://tailwindcss.com/) | 原子化 CSS 样式管理 |
| [Pinia](https://pinia.vuejs.org/) | Vue 3 官方状态管理 |
| [Axios](https://axios-http.com/) | HTTP 请求 |

### 后端 — `tricore-server`

| 技术 | 用途 |
|------|------|
| [Actix-web](https://actix.rs/) | 高性能 HTTP 框架 |
| [SQLx](https://github.com/launchbadge/sqlx) | 异步 PostgreSQL 驱动 |
| [Serde](https://serde.rs/) | 序列化 / 反序列化 |
| [Tokio](https://tokio.rs/) | 异步运行时 |
| [dotenvy](https://crates.io/crates/dotenvy) | 环境变量加载 |

---

## 项目结构

```
TriCore/
├── README.md                    # 本文档
├── tricore-web/                 # React 前端 (Vite + React + TS)
│   ├── src/
│   │   ├── layouts/             # 布局组件
│   │   ├── pages/               # 页面
│   │   │   ├── sales/           # 销售管理模块
│   │   │   ├── oa/              # 办公协同模块
│   │   │   └── inventory/       # 库存管理模块
│   │   ├── store/               # Redux 状态管理
│   │   ├── services/            # API 服务层
│   │   ├── components/          # 公共组件
│   │   └── styles/              # 全局样式 (Tailwind CSS)
│   └── vite.config.ts
├── tricore-web-rust/            # Vue 3 前端 (Rsbuild/Rspack + Vue 3 + TS)
│   ├── src/
│   │   ├── layouts/             # 布局组件
│   │   ├── pages/               # 页面
│   │   │   ├── sales/           # 销售管理模块
│   │   │   ├── oa/              # 办公协同模块
│   │   │   └── inventory/       # 库存管理模块
│   │   ├── router/              # Vue Router 路由配置
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── services/            # API 服务层
│   │   └── styles/              # 全局样式 (Tailwind CSS)
│   ├── rsbuild.config.ts
│   └── postcss.config.mjs
└── tricore-server/              # Rust 后端 (Actix-web + SQLx)
    ├── src/
    │   ├── routes/              # 路由定义
    │   ├── handlers/            # 请求处理器
    │   ├── models/              # 数据模型
    │   └── db.rs                # 数据库连接池
    ├── .env                     # 环境变量
    └── Cargo.toml
```

---

## 数据库连接

> 在 `tricore-server/.env` 中配置以下环境变量：

| 配置项 | 说明 |
|--------|------|
| **DATABASE_HOST** | 数据库主机地址 |
| **DATABASE_PORT** | 数据库端口（默认 5432） |
| **DATABASE_USER** | 数据库用户名 |
| **DATABASE_PASS** | 数据库密码 |
| **DATABASE_NAME** | 数据库名称 |
| **DATABASE_URL** | 完整连接串 `postgres://<user>:<pass>@<host>:<port>/<db>` |

---

## 快速开始

### 1. 启动后端

```bash
cd tricore-server
cargo run
# 服务启动在 http://localhost:8080
```

### 2. 启动前端（React）

```bash
cd tricore-web
npm install
npm run dev
# 开发服务器启动在 http://localhost:5173
```

### 3. 启动前端（Vue 3 / Rsbuild）

```bash
cd tricore-web-rust
npm install
npm run dev
# 开发服务器启动在 http://localhost:5174
```

---

## 三大核心模块

### 🛒 Sales — 销售管理
- 客户管理 / CRM
- 订单管理
- 销售报表
- 合同管理

### 📋 OA — 办公协同
- 员工管理
- 审批流程
- 日程管理
- 公告通知

### 📦 Inventory — 库存管理
- 商品管理
- 入库 / 出库
- 库存盘点
- 库存预警

---

## License

MIT
