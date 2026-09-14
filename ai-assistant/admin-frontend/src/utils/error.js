// 从 axios 错误里取后端返回的 detail（没有就退回 fallback，再退回原始 message）
export function errText(e, fallback = '') {
  return e.response?.data?.detail || fallback || e.message
}
