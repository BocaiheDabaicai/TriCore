// 从 axios 错误里取后端返回的中文提示（detail），取不到就退回传入的兜底文案
export function errText(e, fallback = '') {
  return e.response?.data?.detail || fallback || e.message
}
