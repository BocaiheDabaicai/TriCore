import request from './request'

// 寻文（文献站点）数据层 —— 调用后端接口（study-agent 8003，经 Vite 代理 /api 转发）
// 字段：id / type / name / url / note

export async function listSources() {
  return request.get('/sources')
}
