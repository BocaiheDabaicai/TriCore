// 接口视图数据 —— 按「调用方 → 被调方」分组的接口清单
// 总体视图回答"谁连谁"；这份清单回答"每个接口是干什么的"（点开看完整作用与链路）
// 内容与代码对齐：ai-assistant/api/admin.py、manager/main.py、study-agent/api/readings.py 等

export const INTERFACE_GROUPS = [
  {
    fromKey: 'frontend', toKey: 'ai-assistant', note: '问答链路',
    items: [
      {
        method: 'POST', path: '/api/v1/chat',
        desc: '统一问答入口（一次性返回完整回答）',
        detail: '调度器收到问题后先做意图识别（LLM 输出 JSON），knowledge 且知识库在线则转发，否则降级为通用对话并在响应里标 degraded。每次调用写入 calls 表（意图 / 实际来源 / 耗时）。',
      },
      {
        method: 'POST', path: '/api/v1/chat/stream',
        desc: '流式问答（SSE 打字机效果）',
        detail: '按 meta → delta → done 三段事件推送；知识库的流式回答字节级原样透传（透传层的铁律：不顺手改格式，换行协议动一处就全断）。前端边收边渲染，用户中途关掉也会落库。',
      },
    ],
  },
  {
    fromKey: 'admin-frontend', toKey: 'ai-assistant', note: '管理数据面（统计 + 知识管理代理）',
    items: [
      {
        method: 'GET', path: '/api/v1/admin/overview',
        desc: '总览：Agent 在线状态 + 调用统计',
        detail: 'Agent 状态由调度器实时探测；调用统计（总次数 / 知识问答成功率 / 降级次数 / 平均耗时）来自它自己的 calls 表——全链路数据只有调度器有这个视角。',
      },
      {
        method: 'GET', path: '/api/v1/admin/calls',
        desc: '最近调用记录',
        detail: '逐条列出每次问答：意图、实际回答来源、是否降级、耗时，最新在前。',
      },
      {
        method: 'GET', path: '/api/v1/admin/kb/knowledge',
        desc: '知识列表（代理转发）',
        detail: '支持关键字 / 分类 / 类型筛选。调度器不处理数据，原样转发到知识库的 /api/v1/knowledge/list；知识库不可用时统一返回 502，前端收到即提示。',
      },
      {
        method: 'POST', path: '/api/v1/admin/kb/upload',
        desc: '上传知识文件（代理转发）',
        detail: 'multipart 原样透传（txt / md / pdf / docx）。知识库收到后：解析 → LLM 识别分类 → 入库 → 自动分块向量化，立刻可问答。这条链就是"管理端发起 → 调度器中转 → 知识库处理"。',
      },
      {
        method: 'DELETE', path: '/api/v1/admin/kb/knowledge/{id}',
        desc: '删除一条知识（代理转发）',
        detail: '转发到知识库；知识库删除时顺带清理对应的向量索引。',
      },
      {
        method: 'GET', path: '/api/v1/admin/kb/missed',
        desc: '未命中问题清单（代理转发）',
        detail: '知识库答不上的问题自动入库、按被问次数排序——用户问什么没答上，就是要补什么知识。补完知识后从这里删掉。',
      },
      {
        method: 'DELETE', path: '/api/v1/admin/kb/missed/{id} · /api/v1/admin/kb/missed',
        desc: '删除 / 清空未命中记录（代理转发）',
        detail: '单个删除对应"这条知识已补充完毕"；清空用于批量补充后一次性处理。',
      },
    ],
  },
  {
    fromKey: 'admin-frontend', toKey: 'manager', note: '运维面（/ops 直连，不经调度器）',
    items: [
      {
        method: 'GET', path: '/ops/api/v1/services',
        desc: '全部服务状态',
        detail: '名称 / 端口 / 状态 / PID / 运行时长 / 重启次数，另含展示用的中文名与进入链接（来自 services.json）。管理端每 5 秒轮询它驱动状态灯。',
      },
      {
        method: 'POST', path: '/ops/api/v1/services/{name}/start · stop · restart',
        desc: '单个服务 启动 / 停止 / 重启',
        detail: '直连 manager（8002）：进程控制不能经调度器转发——ai-assistant 挂了也得能靠它重启。手动 stop 的服务不会被监控自动拉起；restart = stop + start。',
      },
      {
        method: 'POST', path: '/ops/api/v1/services/start-all · stop-all',
        desc: '全部 启动 / 停止（auto_start 项）',
        detail: '日常只需手动启动 manager 一个进程，它按配置把其余服务全部拉起并持续守护。',
      },
      {
        method: 'GET', path: '/ops/api/v1/services/{name}/logs',
        desc: '服务运行日志（尾部 N 行）',
        detail: '各服务日志由 manager 统一落盘到 logs/{name}.log；读取时清理 ANSI 颜色码，日志弹窗里不出现乱码。',
      },
    ],
  },
  {
    fromKey: 'ai-assistant', toKey: 'kb-agent', note: '问答链路的下游',
    items: [
      {
        method: 'POST', path: '/api/v1/agent/chat/stream',
        desc: '问答转发（唯一对接接口，SSE 透传）',
        detail: '调度器路由到知识库后调用的唯一问答接口；知识库内部再做 宽度/深度 分流检索与生成。曾因透传层丢换行导致流式界面永远"思考中"，修复后此处是字节级转发。',
      },
      {
        method: 'GET·POST·DELETE', path: '/api/v1/knowledge/* · /api/v1/missed*',
        desc: '知识管理接口（承接管理端代理流量）',
        detail: '上面"管理端 → 调度器"那组 kb 接口的下一跳——调度器只转发不处理，知识数据的一切增删查都落在这里。',
      },
    ],
  },
  {
    fromKey: 'study-frontend', toKey: 'study-agent', note: '独立体系（不与集群互通）',
    items: [
      {
        method: 'GET', path: '/api/readings',
        desc: '研读记录列表（更新时间倒序）',
        detail: '回顾页数据来源；每条含标题 / 精读泛读 / 分类标签 / 笔记摘要与时间戳。',
      },
      {
        method: 'GET', path: '/api/readings/{id}',
        desc: '单条记录详情',
        detail: '详情页与编辑模式回填用；记录不存在时返回 200 + data=null（与前端约定一致）。',
      },
      {
        method: 'POST', path: '/api/readings',
        desc: '新建记录（首次保存即创建）',
        detail: '自动保存的"首次保存"走它：拿到 id 后地址栏切换为 /edit/:id，之后一律走更新。',
      },
      {
        method: 'PUT', path: '/api/readings/{id}',
        desc: '更新记录（自动保存走它）',
        detail: '停笔 1.2 秒自动保存一次；内容无变化时前端不发请求（版本号比对），避免无谓写入。',
      },
      {
        method: 'POST', path: '/api/readings/{id}/attachment',
        desc: '上传论文附件（PDF / 图片）',
        detail: '存为 uploads/{id}_{文件名}；替换附件时先删旧文件。选文件不立即上传，保存时搭车传，失败保留自动重试。',
      },
      {
        method: 'GET', path: '/api/readings/{id}/attachment',
        desc: '打开附件（浏览器内联预览）',
        detail: 'PDF 调浏览器内置阅读器、图片直接显示——不在左论文区内嵌，左区预览走同一个地址。',
      },
      {
        method: 'DELETE', path: '/api/readings/{id}',
        desc: '删除记录（连带附件文件）',
        detail: '删除前有确认弹窗；记录与 uploads 里的附件文件一起清理，不留孤儿文件。',
      },
      {
        method: 'GET', path: '/api/sources',
        desc: '寻文站点列表',
        detail: '寻文页数据来源；站点按类型（工程管理 / AI·计算机 / Web3·区块链）分组展示。',
      },
    ],
  },
  {
    planned: true, fromKey: 'ai-assistant', toLabel: '文档审查 / 数据分析 / 通知助手（规划中）',
    note: '统一协议对接，换 Agent / 加 Agent 不改调度器',
    items: [
      {
        method: '协议',
        path: '{question, context} → {answer, references, confidence}',
        desc: '统一 Agent 协议（规划中）',
        detail: '每个 Agent 只暴露一个标准接口，调度器只认这套协议。文档审查、数据分析、通知助手接入时按此约定实现即可，调度器零改动。',
      },
    ],
  },
]
