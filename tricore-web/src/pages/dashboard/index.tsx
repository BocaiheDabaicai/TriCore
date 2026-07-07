import { Card, Col, Row, Statistic } from 'antd'
import {
  ShoppingCartOutlined,
  TeamOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'

const stats = [
  { title: '销售订单', value: 0, icon: <ShoppingCartOutlined />, color: '#1677ff' },
  { title: '员工数量', value: 0, icon: <TeamOutlined />, color: '#52c41a' },
  { title: '商品种类', value: 0, icon: <DatabaseOutlined />, color: '#fa8c16' },
  { title: '本月完成', value: 0, icon: <CheckCircleOutlined />, color: '#722ed1' },
]

export default function Dashboard() {
  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>工作台</h2>
      <Row gutter={[16, 16]}>
        {stats.map((item) => (
          <Col xs={24} sm={12} lg={6} key={item.title}>
            <Card>
              <Statistic
                title={item.title}
                value={item.value}
                prefix={item.icon}
                valueStyle={{ color: item.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>
      <Card style={{ marginTop: 24 }}>
        <h3>欢迎使用 TriCore 三核管理系统</h3>
        <p>集成 <strong>销售管理</strong>、<strong>办公协同</strong>、<strong>库存管理</strong> 三大核心业务模块，助力企业高效运营。</p>
      </Card>
    </div>
  )
}
