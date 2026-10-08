import { createClient } from './client'

// 操作台只对接一个后端：rpa-agent（Vite 把 /api 代理到 8004）
const api = createClient('/api', 30000)

// ---- 浏览器（人工登录在这里做） ----
export const getBrowser = () => api.get('/v1/browser')
export const openBrowser = (url = '') => api.post('/v1/browser/open', { url }, { timeout: 120000 })
export const closeBrowser = () => api.post('/v1/browser/close', {}, { timeout: 120000 })
export const killOrphans = () => api.post('/v1/browser/kill-orphans', {}, { timeout: 60000 })

// ---- 单元 ----
export const getUnits = () => api.get('/v1/units')
export const runUnit = (key, inputs) => api.post(`/v1/units/${key}/run`, { inputs }, { timeout: 60000 })
export const verifyUnit = (key, verified = true, note = null) =>
  api.post(`/v1/units/${key}/verify`, { verified, note })

// ---- 运行记录 ----
export const getRun = (id) => api.get(`/v1/runs/${id}`)
export const getRecentRuns = (limit = 5) => api.get('/v1/runs', { params: { limit } })
export const cancelRun = (id) => api.post(`/v1/runs/${id}/cancel`, {})
export const shotUrl = (runId, filename) => `/api/v1/runs/${runId}/shots/${filename}`

// ---- 截图资料库 ----
export const getShots = () => api.get('/v1/shots')
export const deleteShot = (name) => api.delete(`/v1/shots/file/${encodeURIComponent(name)}`)
export function uploadShot(file) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/v1/shots', form, { timeout: 60000 })
}
