import { useEffect, useState } from 'react'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs, InputNumber } from 'antd'
import { PlusOutlined, EyeOutlined } from '@ant-design/icons'
import { salesAPI } from '../../services/api'
import type { TabsProps } from 'antd'

const statusColors: Record<string, string> = {
  pending: 'orange', confirmed: 'blue', processing: 'purple',
  shipped: 'cyan', delivered: 'green', cancelled: 'red',
}
const statusLabels: Record<string, string> = {
  pending: '待处理', confirmed: '已确认', processing: '处理中',
  shipped: '已发货', delivered: '已交付', cancelled: '已取消',
}
const categories = ['电子产品', '日用品', '食品', '服装', '办公用品', '医疗', '运动']

export default function SalesDashboard() {
  const [products, setProducts] = useState<any[]>([])
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [orderModal, setOrderModal] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<any>(null)
  const [editing, setEditing] = useState<any>(null)
  const [form, setForm] = useState({ sku: '', name: '', original_price: 0, category: '', description: '' })
  const [activeTab, setActiveTab] = useState('orders')

  const loadData = async () => {
    setLoading(true)
    try {
      const [prodRes, orderRes]: any[] = await Promise.all([
        salesAPI.listProducts({ per_page: 100 }),
        salesAPI.listOrders({ per_page: 50 }),
      ])
      setProducts(prodRes?.data?.data || prodRes?.data || [])
      setOrders(orderRes?.data?.data || orderRes?.data || [])
    } catch { message.error('加载数据失败') }
    finally { setLoading(false) }
  }
  useEffect(() => { loadData() }, [])

  const handleSave = async () => {
    if (!form.name || !form.sku) { message.warning('请填写名称和SKU'); return }
    try {
      if (editing) { await salesAPI.updateProduct(editing.id, form); message.success('已更新') }
      else { await salesAPI.createProduct(form); message.success('已创建') }
      setModalOpen(false); setEditing(null); setForm({ sku: '', name: '', original_price: 0, category: '', description: '' })
      loadData()
    } catch { message.error('操作失败') }
  }

  const productCols = [
    { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 110,
      render: (v: string) => <span style={{ color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: 12, fontWeight: 500 }}>{v}</span> },
    { title: '商品名称', dataIndex: 'name', key: 'name',
      render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span> },
    { title: '价格', dataIndex: 'original_price', key: 'price', width: 100,
      render: (v: number) => <span style={{ color: '#f59e0b', fontFamily: 'ui-monospace, monospace', fontSize: 13 }}>¥{Number(v).toFixed(2)}</span> },
    { title: '库存', dataIndex: 'quantity', key: 'qty', width: 80,
      render: (v: number) => {
        const color = v < 50 ? 'var(--danger)' : v < 200 ? 'var(--warning)' : 'var(--success)'
        return <span style={{ color, fontWeight: 600, fontFamily: 'ui-monospace, monospace' }}>{v}</span>
      }},
    { title: '分类', dataIndex: 'category', key: 'cat', width: 100,
      render: (v: string) => v ? <Tag>{v}</Tag> : <span style={{ color: 'var(--text-muted)' }}>—</span> },
    { title: '操作', key: 'action', width: 80,
      render: (_: any, r: any) => (
        <Button type="link" size="small" onClick={() => { setEditing(r); setForm({ sku: r.sku, name: r.name, original_price: Number(r.original_price), category: r.category || '', description: r.description || '' }); setModalOpen(true) }}>编辑</Button>
      )},
  ]

  const orderCols = [
    { title: '订单号', dataIndex: 'order_no', key: 'no', width: 160,
      render: (v: string) => <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 12, color: 'var(--text-secondary)' }}>{v}</span> },
    { title: '金额', dataIndex: 'final_amount', key: 'amt', width: 110,
      render: (v: number) => <span style={{ color: '#f59e0b', fontFamily: 'ui-monospace, monospace', fontWeight: 600 }}>¥{Number(v).toFixed(2)}</span> },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (v: string) => <Tag color={statusColors[v] || 'default'}>{statusLabels[v] || v}</Tag> },
    { title: '时间', dataIndex: 'created_at', key: 'time', width: 120,
      render: (v: string) => <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{new Date(v).toLocaleDateString('zh-CN')}</span> },
    { title: '操作', key: 'action', width: 80,
      render: (_: any, r: any) => (
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={async () => {
          try { const res: any = await salesAPI.getOrder(r.id); setSelectedOrder(res?.data || res); setOrderModal(true) }
          catch { message.error('加载失败') }
        }}>详情</Button>
      )},
  ]

  const tabItems: TabsProps['items'] = [
    { key: 'orders', label: `订单列表 (${orders.length})`,
      children: <Table columns={orderCols} dataSource={orders} rowKey="id" size="small" locale={{ emptyText: '暂无数据' }} pagination={{ pageSize: 10, showSizeChanger: false }} /> },
    { key: 'products', label: `商品管理 (${products.length})`,
      children: <>
        <div className="mb-3">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); setForm({ sku: '', name: '', original_price: 0, category: '', description: '' }); setModalOpen(true) }}>新增商品</Button>
        </div>
        <Table columns={productCols} dataSource={products} rowKey="id" size="small" locale={{ emptyText: '暂无数据' }} pagination={{ pageSize: 10, showSizeChanger: false }} />
      </> },
  ]

  return (
    <div>
      <div className="page-header">
        <h2 className="gradient-text">销售管理</h2>
        <p>商品定价 · 订单管理 · 捆绑销售 · 退单处理</p>
      </div>
      <Spin spinning={loading}>
        <div className="glass-card p-5">
          <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
        </div>
      </Spin>

      <Modal title={editing ? '编辑商品' : '新增商品'} open={modalOpen} onCancel={() => { setModalOpen(false); setEditing(null) }} onOk={handleSave} okText="保存" cancelText="取消" width={480}>
        <div className="space-y-3 py-2">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs mb-1.5 block font-medium" style={{ color: 'var(--text-secondary)' }}>SKU</label><Input value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} placeholder="PRO-001" /></div>
            <div><label className="text-xs mb-1.5 block font-medium" style={{ color: 'var(--text-secondary)' }}>价格</label><InputNumber className="w-full" value={form.original_price} onChange={(v) => setForm({ ...form, original_price: v || 0 })} min={0} step={0.01} /></div>
          </div>
          <div><label className="text-xs mb-1.5 block font-medium" style={{ color: 'var(--text-secondary)' }}>商品名称</label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="商品名称" /></div>
          <div><label className="text-xs mb-1.5 block font-medium" style={{ color: 'var(--text-secondary)' }}>分类</label><Select className="w-full" value={form.category || undefined} onChange={(v) => setForm({ ...form, category: v })} allowClear placeholder="选择分类" options={categories.map((c) => ({ value: c, label: c }))} /></div>
        </div>
      </Modal>

      <Modal title={`订单详情 — ${selectedOrder?.order_no || ''}`} open={orderModal} onCancel={() => { setOrderModal(false); setSelectedOrder(null) }} footer={null} width={560}>
        {selectedOrder && (
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span style={{ color: 'var(--text-muted)' }}>订单号</span><p className="font-mono text-xs mt-0.5" style={{ color: 'var(--text-primary)' }}>{selectedOrder.order_no}</p></div>
              <div><span style={{ color: 'var(--text-muted)' }}>状态</span><p className="mt-0.5"><Tag color={statusColors[selectedOrder.status]}>{statusLabels[selectedOrder.status] || selectedOrder.status}</Tag></p></div>
              <div><span style={{ color: 'var(--text-muted)' }}>原价</span><p className="mt-0.5" style={{ color: 'var(--text-primary)' }}>¥{Number(selectedOrder.total_amount).toFixed(2)}</p></div>
              <div><span style={{ color: 'var(--text-muted)' }}>实付</span><p className="font-bold mt-0.5" style={{ color: '#f59e0b' }}>¥{Number(selectedOrder.final_amount).toFixed(2)}</p></div>
            </div>
            {selectedOrder.items?.length > 0 && (
              <div>
                <p className="text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>订单明细</p>
                <div className="rounded-lg overflow-hidden border" style={{ borderColor: 'var(--border-subtle)' }}>
                  {selectedOrder.items.map((item: any, i: number) => (
                    <div key={i} className="flex justify-between items-center px-4 py-2.5 text-sm"
                      style={{ background: i % 2 === 0 ? 'transparent' : 'var(--input-bg)' }}>
                      <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>#{i + 1}</span>
                      <span style={{ color: 'var(--text-secondary)' }}>×{item.quantity} @ ¥{Number(item.unit_price).toFixed(2)}</span>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>¥{Number(item.subtotal).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
