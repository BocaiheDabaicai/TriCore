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

// 批量导出：每条记录一个 Markdown，后端打包成 ZIP
// responseType=blob → 请求层拦截器返回的 resp.data 就是 Blob（不是 JSON）
export async function exportReadings(ids) {
  return request.get('/readings/export', {
    params: { ids: ids.join(',') },
    responseType: 'blob',
  })
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
