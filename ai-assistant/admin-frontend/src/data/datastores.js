// 数据视图 —— 各服务的数据库与数据量说明
// 静态部分 = 结构描述（谁有什么库、每张表干嘛）；live 字段 = 绑定页面上拉的实时计数
// 内容与代码对齐：kb-agent/models、ai-assistant/models、study-agent/models

export const DATASTORES = [
  {
    name: 'kb_agent.db',
    ownerKey: 'kb-agent',
    type: 'SQLite 单文件',
    tables: [
      {
        name: 'knowledge',
        desc: '统一知识表：kind 区分制度 / 文档 / 流程，keywords 关键词（宽度查询的目录），content 全文；每条知识入库时自动分块向量化',
        live: 'knowledge',
      },
      {
        name: 'knowledge_vectors',
        desc: '知识分块的向量索引：float32 归一化 BLOB，检索时直接点积（即余弦相似度），全量矩阵运算',
      },
      {
        name: 'missed_questions',
        desc: '知识库答不上的问题：重复提问累计次数；补完对应知识后从这里删除',
        live: 'missed',
      },
      {
        name: 'messages',
        desc: '多轮对话记忆：同一 session_id 下的用户问题与 AI 回答',
      },
    ],
  },
  {
    name: 'assistant.db',
    ownerKey: 'ai-assistant',
    type: 'SQLite 单文件',
    tables: [
      {
        name: 'calls',
        desc: '每次问答调用记一笔：问题 / 意图 / 实际回答来源 / 是否降级 / 耗时——全链路视角只有调度器有',
        live: 'calls',
      },
    ],
  },
  {
    name: 'study_agent.db',
    ownerKey: 'study-agent',
    type: 'SQLite 单文件',
    tables: [
      {
        name: 'readings',
        desc: '研读记录：标题 / 精读泛读 / 分类标签 / Markdown 笔记 / 附件名 / 时间戳',
        live: 'readings',
      },
      {
        name: 'sources',
        desc: '寻文站点：类型分组 / 名称 / 链接 / 备注（首次启动自动灌入种子）',
        live: 'sources',
      },
    ],
    extra: {
      text: '附件目录 uploads/：论文 PDF 与截图原文件（命名 {记录id}_{文件名}，按数据策略计划不进 git）',
      live: 'attachments',
    },
  },
  {
    name: 'manager（无数据库）',
    ownerKey: 'manager',
    type: '配置即数据',
    tables: [
      {
        name: 'services.json',
        desc: '服务清单：端口 / 启动命令 / 探活路径 + 展示用中文名与进入链接——架构图的卡片与"进入"按钮都来自它',
      },
      {
        name: 'logs/{name}.log',
        desc: '各服务的运行日志统一落盘：Python 子进程强制 UTF-8 编码，读取时清理 ANSI 颜色码',
      },
    ],
  },
]
