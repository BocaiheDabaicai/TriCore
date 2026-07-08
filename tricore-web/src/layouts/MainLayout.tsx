import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'

const { Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <span>📊</span>, label: '工作台' },
  { key: '/sales',    icon: <span>🛒</span>, label: '销售管理' },
  { key: '/oa',       icon: <span>📋</span>, label: '办公协同' },
  { key: '/inventory',icon: <span>📦</span>, label: '库存管理' },
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
    <button className="theme-toggle" onClick={() => setDark(!dark)} title={dark ? '亮色模式' : '暗色模式'}>
      {dark ? '☀️' : '🌙'}
    </button>
  )
}

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Layout hasSider style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
      <Sider
        trigger={null} collapsible collapsed={collapsed} width={220}
        style={{ background: 'var(--sidebar-bg)' }}
        className="border-r border-[var(--border-subtle)]"
      >
        <div
          className="h-16 flex items-center justify-center cursor-pointer select-none"
          onClick={() => setCollapsed(!collapsed)}
        >
          <span className="text-2xl font-bold gradient-text tracking-wider">
            {collapsed ? '三核' : 'TriCore'}
          </span>
          {!collapsed && <span className="text-sm ml-1 mt-1" style={{ color: 'var(--text-muted)' }}>三核</span>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ background: 'transparent', borderInlineEnd: 'none' }}
          className="px-3 [&_.ant-menu-item]:rounded-xl [&_.ant-menu-item]:my-1"
        />
      </Sider>
      <Layout style={{ background: 'transparent' }}>
        <div className="h-16 flex items-center justify-between px-6 border-b" style={{ borderColor: 'var(--border-subtle)' }}>
          <span className="text-sm font-medium tracking-wide" style={{ color: 'var(--text-secondary)' }}>
            {menuItems.find((m) => m.key === location.pathname)?.label || 'TriCore'}
          </span>
          <ThemeToggle />
        </div>
        <Content className="p-6 overflow-auto" style={{ background: 'transparent' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
