import axios from 'axios'

// axios 实例工厂 —— 三个 baseURL（/api 调度器、/ops manager、/study 研读库）共用同一套拦截器
export function createClient(baseURL, timeout) {
  const client = axios.create({ baseURL, timeout })

  // 请求拦截器：发出去之前统一处理（以后加 token、公共 headers 就在这里）
  client.interceptors.request.use((config) => config)

  // 响应拦截器：统一剥掉 axios 的包装，调用方直接拿到 data；
  // 出错统一从这里抛出，调用方 try/catch 即可
  client.interceptors.response.use(
    (resp) => resp.data,
    (err) => Promise.reject(err),
  )

  return client
}
