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
        detail: '按 meta → delta → done 三段事件推送；知识库的流式回答字节级原样透传（透传层的铁律：不顺手改格式，换行协议动一处就全断）。前端边收边渲染，用户中途关掉也会落库。请求可带 selected_ids（指定文档模式），调度器原样透传给知识库。',
      },
      {
        method: 'GET', path: '/api/v1/catalog',
        desc: '知识目录（代理转发）',
        detail: '左侧「指定文档」面板的清单：每条只有标题 / 分类 / 类型 / 关键词，不含正文。面板收起时前端不发这个请求。',
      },
      {
        method: 'POST', path: '/api/v1/preselect',
        desc: 'AI 预选文档（代理转发）',
        detail: '把目录整体交给 LLM，按当前问题挑出最相关的 ≤5 篇作为默认勾选；目录超过 60 条时先向量粗排取 20 条候选再挑。用户可增删，预选失败就返回空、由用户自己勾。',
      },
      {
        method: 'GET', path: '/api/v1/conversations',
        desc: '对话记录列表（左侧栏）',
        detail: '本机全部会话按最近更新倒序，含标题（首问截断 50 字）与消息数。对话记录存在调度器：全链路视角只有它有。空会话不落库，发过问、答成功才出现在列表里。',
      },
      {
        method: 'GET', path: '/api/v1/conversations/{session_id}',
        desc: '单个会话 + 全部消息（点开回放）',
        detail: '切换会话时拉全量消息回放，assistant 行带 meta（实际回答来源 / 来源列表 / 检索方式）——降级轮存的也是实际来源而不是意图名。不存在返回 data:null，前端当"已在别处被删"处理。',
      },
      {
        method: 'DELETE', path: '/api/v1/conversations/{session_id}',
        desc: '删除会话（行内二次确认）',
        detail: '删本地两表 + best-effort 通知知识库清掉它那份多轮上下文（失败不影响本地删除）；幂等，重复删也返回成功。',
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
        desc: '上传知识文件（代理转发，支持批量）',
        detail: 'multipart 原样透传（txt / md / pdf / docx / 图片 png、jpg、jpeg、webp）。知识库收到后：解析 → LLM 识别分类 → 入库 → 自动分块向量化，立刻可问答；同时生成关键词与摘要（摘要供广度·汇总类问题使用）。解析分两路：有文字层的 PDF 页用 pypdf 直接取字（免费零误差），没有文字层的页（扫描件）与图片文件用 PyMuPDF 渲染后交大模型视觉转写（按页计费，扫描件耗时上分钟级）。批量上传由前端并发池实现（后端仍是单文件接口），逐文件显示进度与状态。这条链就是"管理端发起 → 调度器中转 → 知识库处理"。注意上传路由是**同步 def**：解析 / 分类 / 向量化都是阻塞调用，同步路由会被丢进线程池，多个文件真并行且不冻住事件循环（否则上传期间问答会被卡、探活超时还会把服务重启）。',
      },
      {
        method: 'POST', path: '/api/v1/admin/kb/missed/{id}/draft',
        desc: 'AI 起草补充资料骨架（代理转发）',
        detail: '未命中闭环的第一步：按未命中问题起草标题 / 分类 / 关键词 / 正文骨架。AI 只搭框架、绝不编造具体规定，正文里用【待补充】占位，由人工填实再入库。',
      },
      {
        method: 'POST', path: '/api/v1/admin/kb/knowledge/create',
        desc: '手工创建知识（代理转发）',
        detail: '未命中闭环的第二步：人工编辑完草稿后入库，摘要未传则由 LLM 生成；入库即完成分块向量化，随后自动删掉对应的未命中记录。',
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
        detail: '调度器路由到知识库后调用的唯一问答接口；知识库内部做四路分流——深度·自由问答（向量检索）/ 深度·指定文档（勾选文档全文）/ 广度·枚举（查表列清单）/ 广度·汇总（全部摘要综合）。曾因透传层丢换行导致流式界面永远"思考中"，修复后此处是字节级转发。',
      },
      {
        method: 'GET·POST', path: '/api/v1/agent/catalog · /api/v1/agent/preselect',
        desc: '目录与 AI 预选（承接聊天端流量）',
        detail: '「指定文档」面板的数据来源：catalog 给全量目录（不含正文），preselect 让 LLM 按问题挑 ≤5 篇做默认勾选。',
      },
      {
        method: 'GET·POST·DELETE', path: '/api/v1/knowledge/* · /api/v1/missed*',
        desc: '知识管理接口（承接管理端代理流量）',
        detail: '上面"管理端 → 调度器"那组 kb 接口的下一跳——调度器只转发不处理，知识数据的一切增删查都落在这里。',
      },
      {
        method: 'DELETE', path: '/api/v1/messages/{session_id}',
        desc: '清某个会话的多轮上下文',
        detail: '聊天端删除对话记录时由调度器 best-effort 调用：知识库的 messages 表按 session_id 存着它自己那份多轮上下文，一并清掉。幂等，失败不影响调度器侧删除。',
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
        method: 'POST', path: '/api/readings/extract',
        desc: 'AI 识别文献信息（自动回填表单）',
        detail: '选完文件自动调用（或传 reading_id 读已存附件）：PDF 首页文字层直取、扫描件与图片走视觉；'
          + '返回 语言/标题/作者/出版时间/期刊/标签，前端只补空字段；失败返回 data=null，不阻断手动填写。',
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
    fromKey: 'rpa-frontend', toKey: 'rpa-agent', note: '独立体系（不与集群互通，自带操作台）',
    items: [
      {
        method: 'GET', path: '/api/v1/browser',
        desc: '浏览器状态：开没开、忙不忙、心跳、用户目录、目标系统网址',
        detail: '操作台每 5 秒拉一次。心跳是执行器"还活着"的信号——长步骤里每走一步刷新一次，界面据此判断它是卡住了还是在正常干活。',
      },
      {
        method: 'POST', path: '/api/v1/browser/open',
        desc: '打开浏览器（懒启动，可顺带打开某个网址）',
        detail: '服务启动时不拉浏览器，第一次点这里才拉：headful 浏览器冷启动 1~3 秒，放在启动路径会拖超 manager 的 30 秒启动窗口。登录（账号 + 验证码）在打开的窗口里人工完成，登录态落盘到 data/browser_profile，之后不用反复登。',
      },
      {
        method: 'POST', path: '/api/v1/browser/close',
        desc: '关闭浏览器（登录态保留）',
        detail: '干净地走 Playwright 的 context.close + driver.stop；只把引用置空会让驱动进程挂着，下次在同一线程再起一个驱动会出怪问题。',
      },
      {
        method: 'POST', path: '/api/v1/browser/kill-orphans',
        desc: '强制结束残留浏览器进程（运维救急）',
        detail: '服务被重启/崩溃后浏览器子进程可能还占着用户目录，导致下次启动失败。它先干净关闭自己的连接，再按命令行里带本服务 profile 目录的条件结束进程（匹配在 Python 里做：路径反斜杠/正斜杠两种写法都要认）。',
      },
      {
        method: 'GET', path: '/api/v1/units',
        desc: '单元清单：声明（输入字段 / 步骤 / 环境） + 人工验证状态 + 最近一次运行',
        detail: '单元 = 一条业务数据 × 一个操作环节，靠 units/*.py 里的 UNIT 声明 + run(ctx) 自动注册，加单元不用改框架。人工验证是"双判定"的一半：系统只能判定脚本没报错，结果对不对要人核对过才算跑通。',
      },
      {
        method: 'POST', path: '/api/v1/units/{key}/run',
        desc: '投一次运行（入队返回 run_id，进度靠轮询）',
        detail: '先按声明的必填字段校验输入，再建运行记录、把任务投进浏览器队列，立刻返回——不等执行完。执行器正忙则返回 409 且不排队（RPA 操作有前后依赖，悄悄排队会让人以为没点上）。',
      },
      {
        method: 'GET', path: '/api/v1/runs/{id}',
        desc: '运行详情：状态 + 每步状态与耗时 + 截图 + 最近日志',
        detail: '进度用"步骤列表 + 当前第几步"表达，不用百分比（各步耗时差异太大，百分比会撒谎）。结束状态：success / failed / canceled / interrupted（服务重启打断）。',
      },
      {
        method: 'POST', path: '/api/v1/runs/{id}/cancel',
        desc: '取消运行（协作式：停在当前步骤边界）',
        detail: '只置一个取消开关，由单元在步骤之间检查退出——不硬杀，避免留下半填的表单。',
      },
      {
        method: 'POST', path: '/api/v1/units/{key}/verify',
        desc: '人工标记"这个单元真跑通了"',
        detail: '写 unit_meta 表（不改单元源码）。真实单元光看"页面提示保存成功"不算数，必须人打开目标系统核对过结果。',
      },
      {
        method: 'POST', path: '/api/v1/shots',
        desc: '上传页面截图（截图资料库）',
        detail: '写单元的选择器之前必须看清目标页面长什么样：截图传到这里，AI 读磁盘上的图来认清字段与按钮。将来元素定位失败时，这些图也是视觉兜底的素材。',
      },
      {
        method: 'GET', path: '/api/v1/stats',
        desc: '统计：运行次数 / 已验证单元数 / 截图数',
        detail: '给管理端「数据」视角报数用；admin-frontend 经 /rpa 代理直连它（只读查看，与 /study、/ops 同理）。',
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
