import { createClient } from './client'

// 办公自动化执行器的只读统计 —— 走 /rpa 代理直连 rpa-agent（8004）
// 它有自己的操作台（5176）负责实际操作；管理端只借它把数据量显示在「数据」视角里
const request = createClient('/rpa', 10000)

export function getRpaStats() {
  return request.get('/v1/stats')
}
