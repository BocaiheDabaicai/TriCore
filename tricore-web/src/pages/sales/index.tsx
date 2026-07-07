import { Card, Table, Tag } from 'antd'

const columns = [
  { title: '订单编号', dataIndex: 'orderNo', key: 'orderNo' },
  { title: '客户名称', dataIndex: 'customer', key: 'customer' },
  { title: '金额', dataIndex: 'amount', key: 'amount' },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => {
      const color = status === '已完成' ? 'green' : status === '进行中' ? 'blue' : 'orange'
      return <Tag color={color}>{status}</Tag>
    },
  },
]

export default function SalesDashboard() {
  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>销售管理</h2>
      <Card title="订单列表">
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="id"
          locale={{ emptyText: '暂无数据，请先连接数据库' }}
        />
      </Card>
    </div>
  )
}
