import axios from 'axios'

// 研读库数据（只读统计）—— 走 /study 代理直连研读后端（8003）
// 独立体系、不经调度器；与 /ops 同理，属于管理端的"查看"能力
const request = axios.create({
  baseURL: '/study',
  timeout: 10000,
})

request.interceptors.response.use(
  (resp) => resp.data,
  (err) => Promise.reject(err),
)

export function listReadings() {
  return request.get('/readings')
}

export function listSources() {
  return request.get('/sources')
}
