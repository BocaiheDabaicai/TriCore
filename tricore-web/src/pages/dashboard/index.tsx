import { useEffect, useState } from 'react'
import { Spin } from 'antd'
import { ShoppingCartOutlined, TeamOutlined, DatabaseOutlined, CheckCircleOutlined, FileTextOutlined, AlertOutlined } from '@ant-design/icons'
import { salesAPI, oaAPI, inventoryAPI } from '../../services/api'

interface StatsCard {
  title: string; value: number; icon: React.ReactNode; color: string; subtitle: string
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<StatsCard[]>([
    { title: '销售订单', value: 0, icon: <ShoppingCartOutlined />, color: '#6366f1', subtitle: '全部订单' },
    { title: '员工数量', value: 0, icon: <TeamOutlined />, color: '#22c55e', subtitle: '在职员工' },
    { title: '商品种类', value: 0, icon: <DatabaseOutlined />, color: '#f59e0b', subtitle: '活跃商品' },
    { title: '待处理流程', value: 0, icon: <FileTextOutlined />, color: '#ef4444', subtitle: 'OA审批中' },
    { title: '库存预警', value: 0, icon: <AlertOutlined />, color: '#8b5cf6', subtitle: '低库存商品' },
    { title: '本月完成', value: 0, icon: <CheckCircleOutlined />, color: '#06b6d4', subtitle: '已交付订单' },
  ])

  useEffect(() => {
    async function load() {
      try {
        const [salesDash, oaDash, invDash]: [any, any, any] = await Promise.allSettled([
          salesAPI.getDashboard(), oaAPI.getDashboard(), inventoryAPI.getDashboard(),
        ])
        setStats((prev) => {
          const next = [...prev]
          if (salesDash.status === 'fulfilled' && salesDash.value?.success !== false) {
            const { data } = salesDash.value
            next[0].value = data?.total_orders ?? 0
            const delivered = data?.orders_by_status?.find((s: any) => s.status === 'delivered')
            next[5].value = delivered?.count ?? 0
          }
          if (oaDash.status === 'fulfilled' && oaDash.value?.success !== false) {
            const { data } = oaDash.value
            next[1].value = data?.total_employees ?? 0
            next[3].value = data?.pending_workflows ?? 0
          }
          if (invDash.status === 'fulfilled' && invDash.value?.success !== false) {
            const { data } = invDash.value
            next[2].value = data?.total_products ?? 0
            next[4].value = data?.low_stock_count ?? 0
          }
          return next
        })
      } catch { /* use defaults */ }
      finally { setLoading(false) }
    }
    load()
  }, [])

  const s = { color: 'var(--text-secondary)' }
  const sm = { color: 'var(--text-muted)' }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 gradient-text">工作台</h2>
      <p className="text-sm mb-6" style={sm}>TriCore 三核管理系统 — 核心业务概览</p>

      <Spin spinning={loading}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {stats.map((item) => (
            <div key={item.title} className="glass-card p-5 group cursor-default">
              <div className="flex items-center justify-between mb-3">
                <span className="text-3xl opacity-80" style={{ color: item.color }}>{item.icon}</span>
                <span className="text-2xl font-bold tabular-nums" style={{ color: 'var(--text-primary)' }}>{item.value}</span>
              </div>
              <p className="text-sm font-medium" style={s}>{item.title}</p>
              <p className="text-xs mt-0.5" style={sm}>{item.subtitle}</p>
            </div>
          ))}
        </div>
      </Spin>

      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>欢迎使用 TriCore 三核管理系统</h3>
        <p className="text-sm leading-relaxed" style={s}>
          集成 <span className="text-indigo-500 font-medium">销售管理</span>、
          <span className="text-emerald-500 font-medium">办公协同</span>、
          <span className="text-amber-500 font-medium">库存管理</span> 三大核心业务模块，
          基于 Rust 高性能后端，助力企业数字化运营。
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
          {[
            { label: '🛒 销售系统', desc: '订单 · 商品 · 退单 · 捆绑销售' },
            { label: '📋 OA系统', desc: '流程审批 · 员工管理 · 归档' },
            { label: '📦 库存系统', desc: '入库 · 出库 · 盘点 · 问题追踪' },
          ].map((sys) => (
            <div key={sys.label} className="p-3 rounded-xl border text-sm"
              style={{ background: 'var(--input-bg)', borderColor: 'var(--border-subtle)' }}>
              <p style={s}>{sys.label}</p>
              <p className="text-xs mt-1" style={sm}>{sys.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
