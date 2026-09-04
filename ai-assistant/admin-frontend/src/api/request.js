import axios from 'axios'

// 第1层：axios 实例 —— 与聊天端同款三层架构（request → 模块接口 → 组件/pinia）
const request = axios.create({
  baseURL: '/api',      // 统一前缀，走 Vite 代理转发到 ai-assistant（8001），再由其转发各 Agent
  timeout: 30000,       // 30 秒超时
})

// 请求拦截器：发出去之前统一处理（以后加 token、公共 headers 就在这里）
request.interceptors.request.use((config) => config)

// 响应拦截器：统一剥掉 axios 的包装，调用方直接拿到 data；
// 出错统一从这里抛出，调用方 try/catch 即可
request.interceptors.response.use(
  (resp) => resp.data,
  (err) => Promise.reject(err),
)

export default request
