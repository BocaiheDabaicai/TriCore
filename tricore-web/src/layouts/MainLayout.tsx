import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  ShoppingCartOutlined,
  TeamOutlined,
  DatabaseOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { Layout, Menu, Button, theme } from 'antd'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
  { key: '/sales', icon: <ShoppingCartOutlined />, label: '销售管理' },
  { key: '/oa', icon: <TeamOutlined />, label: '办公协同' },
  { key: '/inventory', icon: <DatabaseOutlined />, label: '库存管理' },
]

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: token.colorWhite,
          fontSize: collapsed ? 18 : 22,
          fontWeight: 700,
          letterSpacing: 2,
        }}>
          {collapsed ? '三核' : 'TriCore 三核'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{
          padding: '0 24px',
          background: token.colorBgContainer,
          display: 'flex',
          alignItems: 'center',
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <span style={{ marginLeft: 16, fontSize: 16, fontWeight: 500 }}>
            TriCore 三核管理系统
          </span>
        </Header>
        <Content style={{
          margin: 24,
          padding: 24,
          background: token.colorBgContainer,
          borderRadius: token.borderRadiusLG,
          overflow: 'auto',
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
