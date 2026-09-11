const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']

// 底部时钟文案：2026年9月11日 星期五 11:44:35
export function formatClock(d) {
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${WEEKDAYS[d.getDay()]} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}
