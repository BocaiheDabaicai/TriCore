// 状态 / 方法 / 类型 的显示映射 —— 各视图共用一套（文案 + 徽章 / 状态灯配色）

// 服务进程状态（manager 输出的四种 + 图上占位两种）：状态灯 dot / 徽章 badge / 文案 text
export const STATUS_META = {
  running: { dot: 'bg-success', text: '运行中', badge: 'badge-success' },
  starting: { dot: 'bg-warning', text: '启动中', badge: 'badge-warning' },
  stopped: { dot: 'bg-base-content/30', text: '已停止', badge: 'badge-ghost' },
  error: { dot: 'bg-error', text: '异常', badge: 'badge-error' },
  unknown: { dot: 'bg-base-content/20', text: '未知', badge: 'badge-ghost' },
  planned: { dot: 'bg-base-content/20', text: '规划中', badge: 'badge-ghost' },
}

// 接口方法徽章配色（组合方法 / 协议取不到时由调用处兜底 badge-ghost）
export const METHOD_META = {
  GET: 'badge-info',
  POST: 'badge-success',
  PUT: 'badge-warning',
  DELETE: 'badge-error',
}

// 知识类型中文名（知识列表徽章 / 上传页类型下拉共用）
export const KIND_LABELS = { policy: '制度', document: '文档', workflow: '流程' }
