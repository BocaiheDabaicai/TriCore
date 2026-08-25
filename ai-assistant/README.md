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

## 更新日志

- 2026-08-25 确认技术栈与分步构建计划，开始第一步（服务骨架）
