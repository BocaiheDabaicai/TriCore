import { useEffect, useState, useRef } from 'react'
import { Spin } from 'antd'
import {
  ShoppingCartOutlined,
  TeamOutlined,
  AppstoreOutlined,
  FileTextOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ArrowUpOutlined,
  AuditOutlined,
  DatabaseOutlined,
} from '@ant-design/icons'
import { salesAPI, oaAPI, inventoryAPI } from '../../services/api'

interface StatsCard {
  title: string
  value: number
  icon: React.ReactNode
  color: string
  bg: string
  subtitle: string
}

function AnimatedNumber({ target }: { target: number }) {
  const [current, setCurrent] = useState(0)
  const raf = useRef(0)

  useEffect(() => {
    const duration = 800
    const start = performance.now()
    const animate = (now: number) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCurrent(Math.round(eased * target))
      if (progress < 1) raf.current = requestAnimationFrame(animate)
    }
    raf.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(raf.current)
  }, [target])

  return <span className="tabular-nums">{current.toLocaleString()}</span>
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<StatsCard[]>([
    { title: '销售订单', value: 0, icon: <ShoppingCartOutlined />, color: '#6c5ce7', bg: 'rgba(108,92,231,0.1)', subtitle: '全部订单' },
    { title: '员工数量', value: 0, icon: <TeamOutlined />, color: '#00b894', bg: 'rgba(0,184,148,0.1)', subtitle: '在职员工' },
    { title: '商品种类', value: 0, icon: <AppstoreOutlined />, color: '#fdcb6e', bg: 'rgba(253,203,110,0.15)', subtitle: '活跃商品' },
    { title: '待处理流程', value: 0, icon: <FileTextOutlined />, color: '#e17055', bg: 'rgba(225,112,85,0.1)', subtitle: 'OA审批中' },
    { title: '库存预警', value: 0, icon: <AlertOutlined />, color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', subtitle: '低库存商品' },
    { title: '本月完成', value: 0, icon: <CheckCircleOutlined />, color: '#74b9ff', bg: 'rgba(116,185,255,0.1)', subtitle: '已交付订单' },
  ])

  useEffect(() => {
    async function load() {
      try {
        const [salesDash, oaDash, invDash]: any[] = await Promise.allSettled([
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

  const modules = [
    { icon: <ShoppingCartOutlined />, color: '#6c5ce7', bg: 'rgba(108,92,231,0.08)', label: '销售系统', desc: '订单管理 · 商品定价 · 捆绑销售 · 退单处理' },
    { icon: <AuditOutlined />, color: '#00b894', bg: 'rgba(0,184,148,0.08)', label: 'OA 系统', desc: '流程审批 · 员工管理 · 日程协同 · 公告通知' },
    { icon: <DatabaseOutlined />, color: '#fdcb6e', bg: 'rgba(253,203,110,0.12)', label: '库存系统', desc: '入库管理 · 出库追踪 · 库存盘点 · 预警通知' },
  ]

  return (
    <div>
      <div className="page-header">
        <h2 className="gradient-text">工作台</h2>
        <p>TriCore 三核管理系统 — 核心业务概览</p>
      </div>

      <Spin spinning={loading}>
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {stats.map((item) => (
            <div key={item.title} className="glass-card p-5 group">
              <div className="flex items-start gap-4">
                <div className="stat-icon-circle" style={{ background: item.bg, color: item.color }}>
                  {item.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>{item.title}</p>
                  <p className="text-2xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                    <AnimatedNumber target={item.value} />
                  </p>
                  <p className="text-xs mt-0.5 flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
                    <ArrowUpOutlined style={{ color: item.color, fontSize: 10 }} />
                    {item.subtitle}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Spin>

      {/* Welcome & Module Overview */}
      <div className="glass-card p-6 mb-6">
        <h3 className="text-lg font-bold mb-1" style={{ color: 'var(--text-primary)' }}>欢迎使用 TriCore</h3>
        <p className="text-sm leading-relaxed mb-5" style={{ color: 'var(--text-secondary)' }}>
          集成 <span style={{ color: '#6c5ce7', fontWeight: 600 }}>销售管理</span>
          、<span style={{ color: '#00b894', fontWeight: 600 }}>办公协同</span>
          、<span style={{ color: '#fdcb6e', fontWeight: 600 }}>库存管理</span> 三大核心业务模块，
          基于 Rust 高性能后端，助力企业数字化运营。
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {modules.map((mod) => (
            <div
              key={mod.label}
              className="p-4 rounded-xl border transition-all duration-200 hover:translate-y-[-2px]"
              style={{ background: 'var(--input-bg)', borderColor: 'var(--border-subtle)' }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg" style={{ color: mod.color }}>{mod.icon}</span>
                <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{mod.label}</span>
              </div>
              <p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>{mod.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
