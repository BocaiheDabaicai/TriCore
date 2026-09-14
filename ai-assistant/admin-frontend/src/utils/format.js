// 时长 / 数字的显示格式化

// 运行时长（秒 → 人读文案）：小时优先，其次分钟、秒
export function fmtUptime(seconds) {
  if (seconds == null) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h) return `${h} 小时 ${m} 分`
  if (m) return `${m} 分 ${s} 秒`
  return `${s} 秒`
}

// 请求耗时（毫秒 → 秒 / 毫秒）
export function fmtDuration(ms) {
  return ms >= 1000 ? (ms / 1000).toFixed(1) + ' s' : ms + ' ms'
}
