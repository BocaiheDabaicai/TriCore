// 架构图配置 —— 手工摆位的"画法"与"说明"
//
// 设计原则（三种关系、三种视觉语言，不混用）：
//   实线 = 调用（左右位置就是方向，所以不画箭头；每条线独立走，不与其他线共线段）
//   大框 = 守护（manager 用一个虚线大框罩住全部被管进程，manager 卡片挂在框外下边缘）
//   虚线 = 还没发生（虚线卡片 = 未做的服务；虚线连线 = 规划中的分流）
//   小圆圈 = 汇流点（多条线先汇到圆圈，再从圆圈另一边出一条线接上级节点）
//
// 节点的事实数据（状态/端口/进入链接）不在这里——由页面实时合并 manager 的 /services 接口；
// 这里只放：位置坐标 + services.json 没有的说明（作用/技术栈/数据库/外部依赖）。
// 布局微调 = 改这里的数字（每条线的 points 就是折线拐点，自己可调）。
//
// 同步约定：加/删服务时四处对一下——
//   services.json（清单）→ 这里 NODES（上卡片）→ interfaces.js（接口清单）→ datastores.js（有数据库时）
//   页面顶部有"漂移检测"：services.json 与这里的名单对不上会自动提示

export const CANVAS = { w: 1180, h: 530 }

export const CARD_W = 150
export const CARD_H = 56

// 大虚线框：manager 守护的全部进程（manager 卡片挂在框外下边缘——它是框的主人，不在框内）
export const GUARD_FRAME = { x: 20, y: 20, w: 1140, h: 420, label: 'manager 守护的全部进程（起停 / 探活 / 自动重启）' }

// 业务分区：浅色底 + 左上角标签
export const ZONES = [
  { x: 48, y: 76, w: 700, h: 340, label: '企业AI助手集群' },
  { x: 776, y: 76, w: 364, h: 154, label: '研读库（独立体系）' },
]

// 服务节点：key 与 services.json 的 name 对应（实时状态按它合并）
export const NODES = [
  // 入口层
  {
    key: 'frontend', x: 80, y: 130,
    detail: {
      role: '员工统一问答入口：对话、流式展示、回答来源标注',
      stack: 'Vue 3 + Vite + pinia + axios',
      db: '无（不落库）',
      deps: '经 /api 代理到调度器（8001），不直连任何 Agent',
    },
  },
  {
    key: 'admin-frontend', x: 80, y: 220,
    detail: {
      role: '管理员界面：调用统计、知识管理（上传/列表/未命中）、服务管理、架构图',
      stack: 'Vue 3 + Vite + daisyUI + pinia',
      db: '无',
      deps: '/api → 调度器（8001）代理各 Agent；/ops → manager（8002）直连',
    },
  },
  // 中枢层
  {
    key: 'ai-assistant', x: 330, y: 130,
    detail: {
      role: '统一 AI 助手：意图识别 → 路由分发 → 结果汇总；问答统一入口',
      stack: 'FastAPI + SQLite + httpx',
      db: 'assistant.db（calls 表：每次问答记一笔）',
      deps: 'DeepSeek（意图识别 + 兜底对话）；下游调知识库',
    },
  },
  // 能力层
  {
    key: 'kb-agent', x: 580, y: 130,
    detail: {
      role: '企业知识问答：制度查询、文档问答、流程助手（RAG）',
      stack: 'FastAPI + SQLite + NumPy（向量检索）',
      db: 'kb_agent.db（knowledge 表 + 向量 BLOB）',
      deps: 'DeepSeek（分类/问答）、硅基流动 bge-m3（Embedding）',
    },
  },
  // 规划中的服务：虚线占位
  {
    key: 'doc-review-agent', x: 580, y: 210, planned: true, cnName: '文档审查',
    detail: { role: '审查合同/方案/报告，指出问题与风险（规划中，尚未实现）' },
  },
  {
    key: 'data-analysis-agent', x: 580, y: 272, planned: true, cnName: '数据分析',
    detail: { role: '基于业务数据查询、统计、分析与归纳（规划中，尚未实现）' },
  },
  {
    key: 'notice-agent', x: 580, y: 334, planned: true, cnName: '通知助手',
    detail: { role: '通知起草、优化、发布与送达管理（规划中，尚未实现）' },
  },
  // 研读区（独立体系）
  {
    key: 'study-frontend', x: 800, y: 140,
    detail: {
      role: '研读库前端：论文精读/泛读笔记、回顾筛选、寻文导航',
      stack: 'Vue 3 + Vite + CodeMirror 6 + pinia',
      db: '无',
      deps: '经 /api 代理到研读后端（8003）',
    },
  },
  {
    key: 'study-agent', x: 970, y: 140,
    detail: {
      role: '研读库后端：研读记录、附件上传（PDF/图片）、寻文站点接口',
      stack: 'FastAPI + SQLite',
      db: 'study_agent.db + uploads/（论文附件）',
      deps: '暂未接 LLM（辅助整理是下一步）',
    },
  },
  // manager：框的主人，挂在框外下边缘（不受自己管理，状态恒为运行中——能打开这个页面就说明它活着）
  {
    key: 'manager', x: 330, y: 452, unmanaged: true, cnName: 'manager', sub: '守护根进程 · 8002',
    detail: {
      role: '唯一手动启动的根进程：按 services.json 拉起全部服务、探活、自动重启、统一日志',
      stack: 'FastAPI + subprocess + psutil + httpx',
      db: '无（配置即 services.json）',
      deps: '不依赖任何被管服务；它挂了要手动拉起（后续交系统服务兜底）',
    },
  },
]

// 汇流点（小圆圈）：多条线先汇到这里，再从另一边出一条线接上级节点
export const JUNCTIONS = [
  { x: 300, y: 158 },   // 调度器左：聊天端 + 管理端 汇流 → 调度器
  { x: 505, y: 158 },   // 调度器右：出口汇流 → 知识库 + 三个规划 Agent
]

// 连线：points = 折线拐点（每条线独立走，不与其他线共线段）
// 守护关系不用线画——看大虚线框；说明：研读库不与调度器连线，它保持独立、只被 manager 守护
export const EDGES = [
  // 入口 → 调度器（经左汇流点；两条线各自独立，不共线）
  { from: 'frontend', to: 'ai-assistant', points: [[230, 158], [296, 158]] },
  { from: 'admin-frontend', to: 'ai-assistant', points: [[230, 238], [300, 238], [300, 162]] },
  // 汇流点 → 调度器（一条线）
  { points: [[304, 158], [330, 158]] },
  // 管理端 → manager（/ops 直连，独立走线，绕开调度器列）
  { from: 'admin-frontend', to: 'manager', points: [[230, 258], [285, 258], [285, 480], [330, 480]] },
  // 调度器 → 右汇流点（一条线），再由圆圈分给知识库和三个规划 Agent
  { points: [[480, 158], [501, 158]] },
  { from: 'ai-assistant', to: 'kb-agent', points: [[509, 158], [580, 158]] },
  { from: 'ai-assistant', to: 'doc-review-agent', dashed: true, points: [[509, 158], [580, 238]] },
  { from: 'ai-assistant', to: 'data-analysis-agent', dashed: true, points: [[509, 158], [580, 300]] },
  { from: 'ai-assistant', to: 'notice-agent', dashed: true, points: [[509, 158], [580, 362]] },
  // 研读区内部
  { from: 'study-frontend', to: 'study-agent', points: [[950, 168], [970, 168]] },
]
