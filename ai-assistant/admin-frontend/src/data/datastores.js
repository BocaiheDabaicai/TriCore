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
        desc: '统一知识表：kind 区分制度 / 文档 / 流程，keywords 关键词（枚举查询的目录），summary 摘要（汇总比较时整篇喂给模型），content 全文；每条知识入库时自动分块向量化',
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
      {
        name: 'conversations',
        desc: '对话记录·会话表：session_id 唯一（前端首轮发问时懒生成）、标题 = 首问截断 50 字、创建与最近更新时间',
      },
      {
        name: 'chat_messages',
        desc: '对话记录·消息：按 session_id 索引存 user / assistant 两行；assistant 行的 meta 存实际回答来源、来源列表、检索方式与是否降级',
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
    name: 'rpa_agent.db',
    ownerKey: 'rpa-agent',
    type: 'SQLite 单文件',
    tables: [
      {
        name: 'runs',
        desc: '每次单元运行一笔：哪个单元 / 输入 JSON / 状态（排队·执行·成功·失败·取消·被打断）/ 停在哪个失败步 / 产物目录；服务重启时会把遗留的"执行中"标成被打断',
        live: 'runs',
      },
      {
        name: 'run_steps',
        desc: '一次运行里每一步的状态、耗时、截图文件名与错误——操作台的步骤列表就是读它',
      },
      {
        name: 'unit_meta',
        desc: '单元的人工验证标记：系统断言通过只是"脚本没报错"，人工核对过金蝶结果才算真跑通（双判定）',
      },
    ],
    extra: {
      text: '浏览器 profile 与数据目录：data/browser_profile（登录态，绝不进 git）、data/runs/{id}/（每步截图）、data/shots/（操作台上传的页面截图）',
      live: 'shots',
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
