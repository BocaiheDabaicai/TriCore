import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  ShoppingCartOutlined,
  AuditOutlined,
  DatabaseOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'

const { Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
  { key: '/sales',     icon: <ShoppingCartOutlined />, label: '销售管理' },
  { key: '/oa',       icon: <AuditOutlined />, label: '办公协同' },
  { key: '/inventory', icon: <DatabaseOutlined />, label: '库存管理' },
]

function ThemeToggle() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('theme')
    return saved ? saved === 'dark' : true
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <button className="theme-toggle" onClick={() => setDark(!dark)} title={dark ? '切换亮色模式' : '切换暗色模式'}>
      {dark ? '☀️' : '🌙'}
    </button>
  )
}

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const currentLabel = menuItems.find((m) => m.key === location.pathname)?.label || 'TriCore'

  return (
    <Layout hasSider style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={230}
        collapsedWidth={60}
        style={{ background: 'var(--sidebar-bg)' }}
      >
        {/* Logo */}
        <div
          className="h-16 flex items-center justify-center gap-2 cursor-pointer select-none"
          onClick={() => navigate('/dashboard')}
          style={{ borderBottom: '1px solid var(--border-subtle)' }}
        >
          {collapsed ? (
            <span className="text-xl font-bold gradient-text">三</span>
          ) : (
            <>
              <span className="text-xl font-bold gradient-text tracking-tight">TriCore</span>
              <span className="text-xs font-medium px-1.5 py-0.5 rounded-md" style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }}>三核</span>
            </>
          )}
        </div>

        {/* Menu */}
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ background: 'transparent', borderInlineEnd: 'none' }}
          className="px-2 py-2"
        />

        {/* Collapse toggle at bottom */}
        <div
          className="absolute bottom-4 left-0 right-0 flex justify-center"
        >
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 hover:bg-[var(--accent-soft)]"
            style={{ color: 'var(--text-muted)', border: 'none', background: 'transparent', cursor: 'pointer' }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
        </div>
      </Sider>

      <Layout style={{ background: 'transparent' }}>
        {/* Header */}
        <div
          className="h-16 flex items-center justify-between px-6 sticky top-0 z-10"
          style={{
            background: 'var(--bg-card)',
            backdropFilter: 'blur(12px)',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold tracking-wide" style={{ color: 'var(--text-primary)' }}>
              {currentLabel}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }}>
              TriCore
            </span>
          </div>
          <ThemeToggle />
        </div>

        {/* Content */}
        <Content className="p-6 overflow-auto" style={{ background: 'transparent', maxWidth: 1280, margin: '0 auto', width: '100%' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
