# ai-assistant（企业AI助手·统一调度服务）

> 独立服务：统一问答入口——意图识别 → 路由分发 → 汇总回答；前端界面（Vite）属于本服务

## 目标架构

```
前端界面（Vite，属于 ai-assistant 服务）
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
| 前端 | Vite（新版，框架待定） |
| 服务间调用 | httpx（支持 SSE 流式透传） |
| 大模型 | DeepSeek（OpenAI 兼容接口） |

## 后续规划

### Agent 管理界面（方案已确认，待实现，2026-08-31 记录）

- 位置：调度器前端（ai-assistant）——问答一个入口，管理也一个入口；侧边栏分「聊天 / Agent 管理」
- 调用情况：ai-assistant 新增第一张表 `calls`（SQLite，与 kb-agent 同款技术栈），每次路由记一笔（意图、目标 Agent、耗时、是否降级）——这个数据只有调度器有全貌，必须由它记录；管理页展示各 Agent 调用次数/成功率/平均耗时、最近调用记录
- 数据信息：代理模式——前端只调调度器的管理接口，由调度器转发到各 Agent 的管理接口（kb-agent 的 knowledge/missed 已现成），前端不直连各 Agent（与问答链路同一模式）；代价是多一跳网络，换来前端零耦合
- 页面结构：总览（各 Agent 在线状态 + 调用统计）/ kb-agent（上传、知识列表、未命中问题清单）
- 原则：先不抽象统一管理协议——先把 kb-agent 页面做实，第二个 Agent 接入时再提炼协议
- 第一步：`calls` 表 + 管理页骨架（前端加侧边栏）

### 会话总结（已设计，待实现，2026-08-26 记录）

- 需求：用户在某 session 内要求「总结一下刚才的对话」
- 方案（无需落库）：前端 `messages` 数组已持有本次会话全量消息 → 调度器意图识别加 `summarize` → `llm_service.summarize_history`（总结专用 prompt）→ 前端 history 从「最近 10 条」改为「全量发送」
- 待办：session_id 存 localStorage（刷新不丢会话）、长会话分段总结（map-reduce）、token 优化（仅总结类请求带全量历史）

## 更新日志

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

# 3. 前端（5173 端口，在 ai-assistant\frontend 目录）
npm run dev
```

浏览器打开 http://localhost:5173
