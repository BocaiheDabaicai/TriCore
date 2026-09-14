# ai-assistant（企业AI助手·统一调度服务）

> 独立服务：统一问答入口——意图识别 → 路由分发 → 汇总回答；前端界面（Vite）属于本服务

## 目标架构

```
前端（聊天端 frontend / 管理端 admin-frontend，均属于本服务）
    ↓ SSE 流式
ai-assistant（统一AI助手服务：意图识别 + 路由 + 汇总）
    ├→ kb-agent             企业知识问答（第一个接入）
    ├→ doc-review-agent     企业项目文档审查（规划中）
    ├→ data-analysis-agent  企业数据分析（规划中）
    └→ notice-agent         企业通知助手（规划中）
    └→ 无匹配时：ai-assistant 直接 LLM 通用对话（兜底）
```

## 分步构建计划

1. **服务骨架**：FastAPI 目录结构 + 配置（.env）+ Hello 接口
2. **LLM 服务层**：意图识别（JSON 输出）+ 通用对话兜底
3. **Agent 注册表**：统一协议定义 + kb-agent 适配器（HTTP 调用 + SSE 透传）
4. **统一问答接口**：`/api/v1/chat`、`/api/v1/chat/stream`
5. **前端（Vite）**：聊天界面 + SSE 流式渲染 + markdown 显示
6. **联调**：前端 ↔ ai-assistant ↔ kb-agent 全链路

## 技术栈

| 组件 | 选型 |
|---|---|
| 后端 | Python + FastAPI（与 kb-agent 一致） |
| 前端 | 聊天端：Vite + Vue3 + pinia；管理端：Vite + Vue3 + pinia + vue-router + Tailwind CSS 4 + daisyUI 5 |
| 服务间调用 | httpx（支持 SSE 流式透传） |
| 大模型 | DeepSeek（OpenAI 兼容接口） |

## 后续规划

### Agent 管理界面（v1 已实现，2026-09-01）

- **独立管理端前端** `admin-frontend/`（5174 端口）：与聊天端分离（受众、权限、部署范围不同）；侧边栏按板块分组（总览 / 运维：服务管理、架构图 / 知识库：上传知识、知识列表、未命中问题），Vite 8 + Vue3 + vue-router 5 + pinia 4 + Tailwind 4 + daisyUI 5
- **calls 表已建成**：每次问答调用记一笔（意图、实际回答来源、是否降级、耗时），流式接口用生成器 try/finally 保证断流也落库；总览页展示调用统计（总次数 / 知识问答成功率 / 降级次数 / 平均耗时）与最近调用记录
- **kb-agent 管理页已做实**：上传（类型/分类可选）、知识列表（筛选 / 删除）、未命中清单（删除 / 清空）
- **代理模式**：前端只调 `/api/v1/admin`（overview/calls 来自本服务，kb 数据转发 kb-agent 的 knowledge/missed 接口），前端不直连 Agent；kb-agent 不可用统一返回 502
- 原则：先不抽象统一管理协议——kb-agent 页面做实后，第二个 Agent 接入时再提炼协议
- 剩余：知识详情/编辑页、调用统计按天图表、Agent 清单目前硬编码在 admin.py（新 Agent 接入时接 registry）

### 会话总结（已设计，待实现，2026-08-26 记录）

- 需求：用户在某 session 内要求「总结一下刚才的对话」
- 方案（无需落库）：前端 `messages` 数组已持有本次会话全量消息 → 调度器意图识别加 `summarize` → `llm_service.summarize_history`（总结专用 prompt）→ 前端 history 从「最近 10 条」改为「全量发送」
- 待办：session_id 存 localStorage（刷新不丢会话）、长会话分段总结（map-reduce）、token 优化（仅总结类请求带全量历史）

## 更新日志

- 2026-09-14 管理端代码整理（零行为变化，CDP 逐页验证通过）：建 `utils/`（meta 状态与类型映射 / format / error 错误提取 / architecture 画图纯函数）+ `composables/usePolling`（三处轮询共用）+ `api/client.js`（createClient 工厂，/api、/ops、/study 三个 axios 实例合一）+ `components/PageHeader`；架构图页 509 行单文件拆为 `views/architecture/` 八文件——父组件只留视图切换（VIEWS 配置数组）、实时状态与抽屉外壳，四个视图面板与节点/接口两种抽屉内容各自独立，数据面板自带轮询；六个视图全部接入公共模块
- 2026-09-01 管理界面 v1：前端拆分为聊天端（frontend）+ 管理端（admin-frontend，5174，Vite 8 + vue-router 5 + Tailwind 4 + daisyUI 5）；本服务建库（SQLite assistant.db + calls 表，每次问答记一笔）；新增 `/api/v1/admin`（overview 统计 / calls 记录 / kb 代理转发：知识列表、删除、上传、未命中清单），kb-agent 不可用统一 502
- 2026-08-26 前端重构：axios 统一请求（`api/request.js` 实例 + 拦截器）、pinia 状态管理（Options 写法）、组件拆分（ChatHeader / MessageList / MessageBubble / ChatInput），App.vue 纯布局；组件直读 store 不传 props；`/status` 移至 `/api/status` 统一前缀
- 2026-08-26 修复 SSE 透传丢换行 bug：registry 透传时 `iter_lines()` 剥掉的换行未补回、空行被过滤，导致前端按 `\n\n` 切块失败、流式界面永远「思考中…」；修复为逐行补 `\n`、保留空行；前端 streamChat 增加流结束兜底解析

- 2026-08-26 完成第 1~4 步：服务骨架（8001 端口）、LLM 服务层（意图识别 JSON 输出 + 通用对话兜底）、统一问答接口 `/api/v1/chat` 与 `/api/v1/chat/stream`（SSE）、Agent 注册表 + kb-agent 适配器（httpx 调用 + SSE 原样透传）
  - 路由规则：knowledge 且 kb-agent 在线 → 转发；kb-agent 不可用 → 降级兜底（响应带 `degraded: true`）
  - 兜底对话不存历史，由调用方传 `history`；kb-agent 的多轮记忆仍走它的 `session_id`
- 2026-08-26 完成第 5 步：前端（Vite + Vue3 单页聊天，`frontend/` 目录）——SSE 流式渲染、markdown 显示、来源展示；Vite 代理 `/api` → 8001，无跨域问题
- 2026-08-26 完成第 6 步：联调通过三个场景（知识问题走 kb-agent / 闲聊走兜底 / kb-agent 关闭时降级）
- 2026-08-25 确认技术栈与分步构建计划，开始第一步（服务骨架）

## 启动方式

```powershell
# 1. kb-agent（8000 端口，在 kb-agent 目录）
.venv\Scripts\python.exe -m uvicorn main:app --port 8000

# 2. ai-assistant（8001 端口，在 ai-assistant 目录）
.venv\Scripts\python.exe -m uvicorn main:app --port 8001

# 3. 聊天端前端（5173 端口，在 ai-assistant\frontend 目录）
npm run dev

# 4. 管理端前端（5174 端口，在 ai-assistant\admin-frontend 目录）
npm run dev
```

浏览器打开：聊天端 http://localhost:5173、管理端 http://localhost:5174
