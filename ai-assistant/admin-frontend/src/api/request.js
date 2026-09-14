import { createClient } from './client'

// 第1层：axios 实例 —— 与聊天端同款三层架构（request → 模块接口 → 组件/pinia）
// 统一前缀走 Vite 代理转发到 ai-assistant（8001），再由其转发各 Agent；30 秒超时
export default createClient('/api', 30000)
