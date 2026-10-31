import request from './request'

// 研读记录数据层 —— 调用后端接口（study-agent 8003，经 Vite 代理 /api 转发）
// 返回结构与页面约定一致：{ message, data }（列表多一个 total），页面零改动
// 字段：id / title / mode / tag / rating / domains / author / published / journal / note / attachment / created_at / updated_at

export async function listReadings() {
  return request.get('/readings')
}

export async function getReading(id) {
  return request.get(`/readings/${id}`)
}

export async function createReading(payload) {
  return request.post('/readings', payload)
}

export async function updateReading(id, payload) {
  return request.put(`/readings/${id}`, payload)
}

export async function deleteReading(id) {
  return request.delete(`/readings/${id}`)
}

// 上传论文附件（FormData 走 multipart，axios 会自动带对 Content-Type）
export async function uploadReadingAttachment(id, file) {
  const form = new FormData()
  form.append('file', file)
  return request.post(`/readings/${id}/attachment`, form)
}

// AI 识别文献信息：传新选的文件，或指定已有记录的附件（后端解析 + 大模型抽取，可能要几十秒）
// 返回 { message, data: {lang,title,author,published,journal,tag} | null }
export async function extractReadingFields({ file, readingId } = {}) {
  const form = new FormData()
  if (file) form.append('file', file)
  if (readingId) form.append('reading_id', readingId)
  return request.post('/readings/extract', form, { timeout: 180000 })
}

// AI 全文速读总结：传新选的文件，或指定已有记录的附件（全文调用通常 20~60 秒）
// 返回 { message, data: {summary, chars} | null }——扫描件 / 图片 / 失败时 data 为 null
export async function summarizeReading({ file, readingId } = {}) {
  const form = new FormData()
  if (file) form.append('file', file)
  if (readingId) form.append('reading_id', readingId)
  return request.post('/readings/summarize', form, { timeout: 300000 })
}
