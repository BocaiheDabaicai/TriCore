import axios from 'axios'

// 统一创建 axios 实例的工厂（三个前端项目同一套写法）
// 响应拦截器直接返回 resp.data，调用方拿到的就是后端的 {message, data}，不用每次 .data
export function createClient(baseURL, timeout) {
  const client = axios.create({ baseURL, timeout })
  client.interceptors.response.use(
    (resp) => resp.data,
    (e) => Promise.reject(e),
  )
  return client
}
