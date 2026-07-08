import { useEffect, useState } from 'react'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs, InputNumber } from 'antd'
import { PlusOutlined, EyeOutlined } from '@ant-design/icons'
import { salesAPI } from '../../services/api'

const statusColors: Record<string, string> = {
  pending: 'orange', confirmed: 'blue', processing: 'purple',
  shipped: 'cyan', delivered: 'green', cancelled: 'red',
}
const categories = ['电子产品', '日用品', '食品', '服装', '办公用品', '医疗', '运动']

const s = { color: 'var(--text-secondary)' }
const sm = { color: 'var(--text-muted)' }

export default function SalesDashboard() {
  const [products, setProducts] = useState<any[]>([])
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [orderModal, setOrderModal] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<any>(null)
  const [editing, setEditing] = useState<any>(null)
  const [form, setForm] = useState({ sku: '', name: '', original_price: 0, category: '', description: '' })

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
    { title: 'SKU', dataIndex: 'sku', key: 'sku', render: (v: string) => <span className="text-indigo-500 font-mono text-xs">{v}</span> },
    { title: '商品名称', dataIndex: 'name', key: 'name' },
    { title: '价格', dataIndex: 'original_price', key: 'price', render: (v: number) => <span className="text-amber-500 font-mono text-sm">¥{Number(v).toFixed(2)}</span> },
    { title: '库存', dataIndex: 'quantity', key: 'qty', render: (v: number) => <span className={v < 50 ? 'text-red-500' : 'text-emerald-500'}>{v}</span> },
    { title: '分类', dataIndex: 'category', key: 'cat', render: (v: string) => v ? <Tag>{v}</Tag> : null },
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <Button type="link" size="small" onClick={() => { setEditing(r); setForm({ sku: r.sku, name: r.name, original_price: Number(r.original_price), category: r.category || '', description: r.description || '' }); setModalOpen(true) }}>编辑</Button>
    )},
  ]

  const orderCols = [
    { title: '订单号', dataIndex: 'order_no', key: 'no', render: (v: string) => <span className="font-mono text-xs" style={s}>{v}</span> },
    { title: '金额', dataIndex: 'final_amount', key: 'amt', render: (v: number) => <span className="text-amber-500 font-mono text-sm">¥{Number(v).toFixed(2)}</span> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={statusColors[v] || 'default'}>{v}</Tag> },
    { title: '时间', dataIndex: 'created_at', key: 'time', render: (v: string) => <span className="text-xs" style={sm}>{new Date(v).toLocaleDateString('zh-CN')}</span> },
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <Button type="link" size="small" icon={<EyeOutlined />} onClick={async () => {
        try { const res: any = await salesAPI.getOrder(r.id); setSelectedOrder(res?.data || res); setOrderModal(true) }
        catch { message.error('加载失败') }
      }}>详情</Button>
    )},
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 gradient-text">销售管理</h2>
      <p className="text-sm mb-6" style={sm}>商品定价 · 订单管理 · 捆绑销售 · 退单处理</p>
      <Spin spinning={loading}>
        <div className="glass-card p-4">
          <Tabs items={[
            { key: 'orders', label: <span>📋 订单列表 <span className="text-xs ml-1" style={sm}>({orders.length})</span></span>,
              children: <Table columns={orderCols} dataSource={orders} rowKey="id" size="middle" locale={{ emptyText: <span style={sm}>暂无数据</span> }} pagination={{ pageSize: 10 }} /> },
            { key: 'products', label: <span>📦 商品管理 <span className="text-xs ml-1" style={sm}>({products.length})</span></span>,
              children: <>
                <div className="mb-3"><Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); setForm({ sku: '', name: '', original_price: 0, category: '', description: '' }); setModalOpen(true) }}>新增商品</Button></div>
                <Table columns={productCols} dataSource={products} rowKey="id" size="middle" locale={{ emptyText: <span style={sm}>暂无数据</span> }} pagination={{ pageSize: 10 }} />
              </> },
          ]} />
        </div>
      </Spin>

      <Modal title={editing ? '编辑商品' : '新增商品'} open={modalOpen} onCancel={() => { setModalOpen(false); setEditing(null) }} onOk={handleSave} okText="保存" cancelText="取消">
        <div className="space-y-3 py-2">
          <div><label className="text-sm mb-1 block" style={s}>SKU</label><Input value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} placeholder="PRO-001" /></div>
          <div><label className="text-sm mb-1 block" style={s}>商品名称</label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="商品名称" /></div>
          <div><label className="text-sm mb-1 block" style={s}>价格</label><InputNumber className="w-full" value={form.original_price} onChange={(v) => setForm({ ...form, original_price: v || 0 })} min={0} step={0.01} /></div>
          <div><label className="text-sm mb-1 block" style={s}>分类</label><Select className="w-full" value={form.category || undefined} onChange={(v) => setForm({ ...form, category: v })} allowClear placeholder="选择分类" options={categories.map((c) => ({ value: c, label: c }))} /></div>
        </div>
      </Modal>

      <Modal title={`订单详情 — ${selectedOrder?.order_no || ''}`} open={orderModal} onCancel={() => { setOrderModal(false); setSelectedOrder(null) }} footer={null} width={640}>
        {selectedOrder && (
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span style={sm}>订单号：</span><span className="font-mono" style={{ color: 'var(--text-primary)' }}>{selectedOrder.order_no}</span></div>
              <div><span style={sm}>状态：</span><Tag color={statusColors[selectedOrder.status]}>{selectedOrder.status}</Tag></div>
              <div><span style={sm}>原价：</span><span style={{ color: 'var(--text-primary)' }}>¥{Number(selectedOrder.total_amount).toFixed(2)}</span></div>
              <div><span style={sm}>实付：</span><span className="font-bold" style={{ color: '#f59e0b' }}>¥{Number(selectedOrder.final_amount).toFixed(2)}</span></div>
            </div>
            {selectedOrder.items?.length > 0 && (
              <div>
                <p className="text-sm mb-2 font-medium" style={s}>明细</p>
                {selectedOrder.items.map((item: any, i: number) => (
                  <div key={i} className="flex justify-between py-2 border-b text-sm" style={{ borderColor: 'var(--border-subtle)' }}>
                    <span style={s}>#{i + 1}</span>
                    <span style={sm}>×{item.quantity} @ ¥{Number(item.unit_price).toFixed(2)}</span>
                    <span style={{ color: 'var(--text-primary)' }}>¥{Number(item.subtotal).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
