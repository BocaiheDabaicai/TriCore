import { Card, Table, Tag } from 'antd'

const columns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '部门', dataIndex: 'department', key: 'department' },
  { title: '职位', dataIndex: 'position', key: 'position' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => (
      <Tag color={status === '在职' ? 'green' : 'red'}>{status}</Tag>
    ),
  },
]

export default function OADashboard() {
  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>办公协同</h2>
      <Card title="员工列表">
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
