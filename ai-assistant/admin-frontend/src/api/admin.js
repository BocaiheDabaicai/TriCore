import request from './request'

// 第2层：管理端接口 —— 数据来自 ai-assistant（calls 表 + Agent 状态探测）

// 总览：Agent 在线状态 + 调用统计
export function getOverview() {
  return request.get('/v1/admin/overview')
}

// 最近调用记录（最新的在前）
export function getCalls(limit = 50) {
  return request.get('/v1/admin/calls', { params: { limit } })
}
