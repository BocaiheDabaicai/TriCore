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
        detail: '枚举 / 汇总 / 深度三维判断、RAG 回答生成（深度·指定文档·汇总三种提示词）、答不上来时的诚实兜底话术',
      },
      {
        task: '上传理解',
        model: 'DeepSeek（V4 Flash）',
        detail: 'classify_upload：识别 kind（制度 / 文档 / 流程）、拟定分类、生成关键词与摘要',
      },
      {
        task: '摘要生成',
        model: 'DeepSeek（V4 Flash）',
        detail: '入库时随分类一起生成（含关键数字）；存量数据用 backfill_summary.py 补录——供「广度·汇总」类问题整篇喂给模型做跨文档综合',
      },
      {
        task: 'AI 预选 / 起草',
        model: 'DeepSeek（V4 Flash）',
        detail: '聊天端指定文档的默认勾选（preselect_documents）、管理端未命中问题的补充资料骨架（draft_supplement，只搭框架不编造）',
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
    config: '配置位置：study-agent/.env —— LLM 三项（LLM_API_KEY / LLM_BASE_URL / LLM_MODEL）',
    items: [
      {
        task: '文献信息识别',
        model: 'DeepSeek（V4 Flash）',
        detail: '选完文件自动抽取 语言 / 标题（英文给中文译名）/ 作者 / 出版时间 / 期刊 / 分类标签 并回填表单（只补空字段）；'
          + 'PDF 首页文字层直取，扫描件与图片走首页视觉理解；标签优先从已有候选里挑，保持体系不膨胀',
      },
    ],
  },
  {
    ownerKey: 'rpa-agent',
    config: '暂无 AI 配置（执行层刻意不用模型，先不引入 .env 里的 LLM 项）',
    items: [
      {
        task: '无 AI 依赖',
        model: '—',
        detail: '执行层是确定性脚本：模型临场决定"点哪个按钮、填什么值"一旦出错就是往生产系统写脏数据。'
          + 'AI 将来只放在两头——前面把 OA 里的非结构化内容读成结构化字段、后面在元素定位失败时做视觉兜底；'
          + '中间的操作动作始终由固定选择器完成。',
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
