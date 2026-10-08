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
// 超时单独放宽到 120s（与调度器代理一致）：默认 30s 会在解析+分类+向量化没跑完时就断掉大文件
// onProgress 回传传输进度（0~1），传输结束不代表上传完成——服务端还要解析、分类、向量化
export function uploadKnowledge(file, { kind, category, onProgress } = {}) {
  const form = new FormData()
  form.append('file', file)
  if (kind) form.append('kind', kind)
  if (category) form.append('category', category)
  return request.post('/v1/admin/kb/upload', form, {
    timeout: 120000,
    onUploadProgress: onProgress
      ? (e) => onProgress(e.total ? e.loaded / e.total : 0)
      : undefined,
  })
}

// 未命中问题清单（按被问次数排序）
export function listMissed(limit = 100) {
  return request.get('/v1/admin/kb/missed', { params: { limit } })
}

// AI 起草补充资料骨架（LLM 生成，超时放宽到 60 秒）
export function draftSupplement(id) {
  return request.post(`/v1/admin/kb/missed/${id}/draft`, null, { timeout: 60000 })
}

// 手工创建知识（补充资料编辑完写入知识库，向量由 kb-agent 自动同步）
export function createKnowledge(payload) {
  return request.post('/v1/admin/kb/knowledge/create', payload, { timeout: 60000 })
}

// 删除一条未命中记录（对应知识已补充后）
export function deleteMissed(id) {
  return request.delete(`/v1/admin/kb/missed/${id}`)
}

// 清空全部未命中记录（批量补充完知识后一次性清理）
export function clearMissed() {
  return request.delete('/v1/admin/kb/missed')
}
