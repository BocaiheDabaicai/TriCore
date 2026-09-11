// AI 视角 —— 集群里哪里用了 AI、用的什么模型、去哪里改
// 配置事实与代码对齐：各服务 core/config.py 从 .env 读取（OpenAI 兼容协议，换供应商只改 .env）
// 同步约定：新服务用了 AI → 这里加一组；换模型/换供应商时改本文件里对应的说明文字

export const AI_USAGES = [
  {
    ownerKey: 'kb-agent',
    config: '配置位置：kb-agent/.env —— LLM 一组（LLM_API_KEY / LLM_BASE_URL / LLM_MODEL）+ Embedding 一组（EMBEDDING_*）',
    items: [
      {
        task: '问答生成',
        model: 'DeepSeek（V4 Flash）',
        detail: '宽 / 深度问题判断、RAG 回答生成、答不上来时的诚实兜底话术',
      },
      {
        task: '上传理解',
        model: 'DeepSeek（V4 Flash）',
        detail: 'classify_upload：识别 kind（制度 / 文档 / 流程）、拟定分类、生成关键词',
      },
      {
        task: '向量化',
        model: '硅基流动 bge-m3',
        detail: '知识分块的语义向量（检索时点积即相似度）；未配置 Embedding 时自动降级为字符匹配',
      },
    ],
  },
  {
    ownerKey: 'ai-assistant',
    config: '配置位置：ai-assistant/.env —— LLM 三项 + KB_AGENT_URL（知识库服务地址）',
    items: [
      {
        task: '意图识别',
        model: 'DeepSeek（V4 Flash）',
        detail: '把问题分类为 knowledge / general 并输出路由 JSON；识别失败时降级 general',
      },
      {
        task: '兜底对话',
        model: 'DeepSeek（V4 Flash）',
        detail: '知识库不可用或非知识类问题时直接生成通用回答（响应里标 degraded）',
      },
    ],
  },
  {
    ownerKey: 'study-agent',
    planned: true,
    config: '将来同样放 study-agent/.env（照 kb-agent 的模式读取）',
    items: [
      {
        task: '暂无 AI',
        model: '—',
        detail: '下一步规划：LLM 辅助整理笔记 / 生成摘要——接入方式照 kb-agent/services/llm_service.py 的模式',
      },
    ],
  },
  {
    ownerKey: 'manager',
    config: '无',
    items: [
      {
        task: '无 AI 依赖',
        model: '—',
        detail: '运维守护不依赖模型：起停、探活、自动重启、日志都是纯进程管理',
      },
    ],
  },
]

// 更改 / 新增模型的操作指引
export const AI_GUIDE = [
  {
    title: '换模型',
    desc: '改对应服务 .env 的 LLM_MODEL（例如 Flash 换 Pro）——代码用 OpenAI 兼容协议，改完重启服务即生效',
  },
  {
    title: '换供应商',
    desc: '改 .env 的 LLM_BASE_URL + LLM_API_KEY 即可（.env.example 注释里有 DeepSeek / 通义千问 / OpenAI 的现成示例）',
  },
  {
    title: '换向量模型',
    desc: '改 kb-agent/.env 的 EMBEDDING_* 三项；换模型后必须重建向量索引（旧向量与新模型不通用）',
  },
  {
    title: '新 Agent 用 AI',
    desc: '照 kb-agent/services/llm_service.py 的模式新增服务层文件 + 自己的 .env 配置，不与其他服务耦合',
  },
  {
    title: '改完要重启',
    desc: '.env 在服务启动时读取——去「服务管理」页点对应服务的"重启"即可',
  },
]
