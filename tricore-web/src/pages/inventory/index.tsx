import { Card, Table, Tag } from 'antd'

const columns = [
  { title: 'SKU', dataIndex: 'sku', key: 'sku' },
  { title: '商品名称', dataIndex: 'name', key: 'name' },
  { title: '库存数量', dataIndex: 'quantity', key: 'quantity' },
  { title: '单价', dataIndex: 'price', key: 'price' },
  {
    title: '状态',
    dataIndex: 'quantity',
    key: 'status',
    render: (_: unknown, record: { quantity: number }) => {
      const quantity = record.quantity;
      if (quantity === undefined) return null
      return quantity > 100 ? (
        <Tag color="green">充足</Tag>
      ) : quantity > 10 ? (
        <Tag color="orange">正常</Tag>
      ) : (
        <Tag color="red">紧缺</Tag>
      )
    },
  },
]

export default function InventoryDashboard() {
  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>库存管理</h2>
      <Card title="商品列表">
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
