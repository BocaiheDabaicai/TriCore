import request from './request'

// 第2层：kb-agent 管理接口 —— 全部经调度器代理（/v1/admin/kb/... → 8001 → kb-agent）
// 前端不直连 kb-agent，与问答链路同一模式（代理模式）

// 知识列表（keyword 关键字 / category 分类 / kind 类型，均可选）
export function listKnowledge(params) {
  return request.get('/v1/admin/kb/knowledge', { params })
}

// 删除知识（向量索引由 kb-agent 一并清理）
export function deleteKnowledge(id) {
  return request.delete(`/v1/admin/kb/knowledge/${id}`)
}

// 上传文件（multipart）：axios 检测到 FormData 会自动设置 Content-Type 和边界
export function uploadKnowledge(file, { kind, category } = {}) {
  const form = new FormData()
  form.append('file', file)
  if (kind) form.append('kind', kind)
  if (category) form.append('category', category)
  return request.post('/v1/admin/kb/upload', form)
}

// 未命中问题清单（按被问次数排序）
export function listMissed(limit = 100) {
  return request.get('/v1/admin/kb/missed', { params: { limit } })
}

// 删除一条未命中记录（对应知识已补充后）
export function deleteMissed(id) {
  return request.delete(`/v1/admin/kb/missed/${id}`)
}

// 清空全部未命中记录（批量补充完知识后一次性清理）
export function clearMissed() {
  return request.delete('/v1/admin/kb/missed')
}
