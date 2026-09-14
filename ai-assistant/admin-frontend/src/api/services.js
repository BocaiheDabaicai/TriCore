import { createClient } from './client'

// 服务管理接口 —— 走 /ops 代理直连 manager（8002）
// 进程控制不能经 ai-assistant 转发：ai-assistant 挂了还得能重启它
// 60 秒超时：启动/停止要拉起进程，比普通请求慢
const request = createClient('/ops/api/v1', 60000)

export function getServices() {
  return request.get('/services')
}

export function startService(name) {
  return request.post(`/services/${name}/start`)
}

export function stopService(name) {
  return request.post(`/services/${name}/stop`)
}

export function restartService(name) {
  return request.post(`/services/${name}/restart`)
}

export function startAll() {
  return request.post('/services/start-all')
}

export function stopAll() {
  return request.post('/services/stop-all')
}

export function getLogs(name, lines = 200) {
  return request.get(`/services/${name}/logs`, { params: { lines } })
}
