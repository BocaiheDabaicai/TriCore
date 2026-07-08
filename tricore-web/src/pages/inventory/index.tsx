import { useEffect, useState } from 'react'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs } from 'antd'
import { PlusOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { inventoryAPI } from '../../services/api'

const s = { color: 'var(--text-secondary)' }
const sm = { color: 'var(--text-muted)' }
const tp = { color: 'var(--text-primary)' }

export default function InventoryDashboard() {
  const [products, setProducts] = useState<any[]>([])
  const [stockIn, setStockIn] = useState<any[]>([])
  const [stockOut, setStockOut] = useState<any[]>([])
  const [issues, setIssues] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [issueModal, setIssueModal] = useState(false)
  const [issueForm, setIssueForm] = useState({ description: '', severity: 'medium', related_type: 'product', related_id: '', reported_by: '' })

  const loadData = async () => {
    setLoading(true)
    try {
      const [prodRes, siRes, soRes, issRes]: any[] = await Promise.all([
        inventoryAPI.listProducts(), inventoryAPI.listStockIn({ per_page: 50 }),
        inventoryAPI.listStockOut({ per_page: 50 }), inventoryAPI.listIssues({ per_page: 50 }),
      ])
      setProducts(prodRes?.data || [])
      setStockIn(siRes?.data?.data || siRes?.data || [])
      setStockOut(soRes?.data?.data || soRes?.data || [])
      setIssues(issRes?.data?.data || issRes?.data || [])
    } catch { message.error('加载数据失败') } finally { setLoading(false) }
  }
  useEffect(() => { loadData() }, [])

  const handleCreateIssue = async () => {
    if (!issueForm.description || !issueForm.related_id) { message.warning('请填写描述'); return }
    try { await inventoryAPI.createIssue(issueForm); message.success('已登记'); setIssueModal(false); loadData() } catch { message.error('操作失败') }
  }

  const handleResolve = async (id: string) => {
    Modal.confirm({
      title: '解决问题', content: <Input.TextArea id="resolution" rows={3} placeholder="解决方案..." />,
      onOk: async () => {
        const el = document.getElementById('resolution') as HTMLTextAreaElement
        try { await inventoryAPI.resolveIssue(id, { resolution: el?.value || '已解决' }); message.success('已解决'); loadData() } catch { message.error('操作失败') }
      },
    })
  }

  const productCols = [
    { title: 'SKU', dataIndex: 'sku', key: 'sku', render: (v: string) => <span className="text-indigo-500 font-mono text-xs">{v}</span> },
    { title: '商品', dataIndex: 'name', key: 'name' },
    { title: '库存', dataIndex: 'quantity', key: 'qty', render: (v: number) => <span className={`font-mono font-bold ${v < 50 ? 'text-red-500' : v < 200 ? 'text-amber-500' : 'text-emerald-500'}`}>{v} {v < 50 && <WarningOutlined className="ml-1" />}</span> },
    { title: '单价', dataIndex: 'original_price', key: 'price', render: (v: number) => <span className="text-amber-500">¥{Number(v).toFixed(2)}</span> },
    { title: '分类', dataIndex: 'category', key: 'cat', render: (v: string) => v ? <Tag>{v}</Tag> : null },
  ]

  const issueCols = [
    { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true, render: (v: string) => <span style={tp}>{v}</span> },
    { title: '类型', dataIndex: 'related_type', key: 'type', render: (v: string) => <Tag>{v}</Tag> },
    { title: '严重', dataIndex: 'severity', key: 'sev', render: (v: string) => <Tag color={v === 'critical' ? 'magenta' : v === 'high' ? 'red' : v === 'medium' ? 'orange' : 'green'}>{v}</Tag> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={v === 'open' ? 'red' : v === 'in_progress' ? 'blue' : 'green'}>{v}</Tag> },
    { title: '操作', key: 'action', render: (_: any, r: any) => (r.status !== 'resolved' && r.status !== 'closed') ? <Button type="link" size="small" icon={<CheckCircleOutlined />} onClick={() => handleResolve(r.id)}>解决</Button> : <span className="text-xs text-emerald-500">已解决</span> },
  ]

  const commonCols = (prefix: string) => [
    { title: '单号', dataIndex: `${prefix}_no`, key: 'no', render: (v: string) => <span className="text-indigo-500 font-mono text-xs">{v}</span> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={v === 'completed' || v === 'delivered' ? 'green' : v === 'shipped' ? 'blue' : 'default'}>{v}</Tag> },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
    { title: '时间', dataIndex: 'created_at', key: 'time', render: (v: string) => <span className="text-xs" style={sm}>{new Date(v).toLocaleDateString('zh-CN')}</span> },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 gradient-text">库存管理</h2>
      <p className="text-sm mb-6" style={sm}>入库 · 出库 · 盘点 · 问题追踪</p>
      <Spin spinning={loading}>
        <div className="glass-card p-4">
          <Tabs items={[
            { key: 'stock', label: <span>📦 库存 <span className="text-xs ml-1" style={sm}>({products.length})</span></span>,
              children: <Table columns={productCols} dataSource={products} rowKey="id" size="middle" locale={{ emptyText: <span style={sm}>暂无数据</span> }} pagination={{ pageSize: 10 }} /> },
            { key: 'stock-in', label: <span>📥 入库 <span className="text-xs ml-1" style={sm}>({stockIn.length})</span></span>,
              children: <Table columns={commonCols('stock_in')} dataSource={stockIn} rowKey="id" size="middle" locale={{ emptyText: <span style={sm}>暂无数据</span> }} pagination={{ pageSize: 10 }} /> },
            { key: 'stock-out', label: <span>📤 出库 <span className="text-xs ml-1" style={sm}>({stockOut.length})</span></span>,
              children: <Table columns={commonCols('stock_out')} dataSource={stockOut} rowKey="id" size="middle" locale={{ emptyText: <span style={sm}>暂无数据</span> }} pagination={{ pageSize: 10 }} /> },
            { key: 'issues', label: <span>⚠️ 问题 <span className="text-xs ml-1" style={sm}>({issues.length})</span></span>,
              children: <><div className="mb-3"><Button type="primary" icon={<PlusOutlined />} onClick={() => { setIssueForm({ description: '', severity: 'medium', related_type: 'product', related_id: products[0]?.id || '', reported_by: '' }); setIssueModal(true) }}>登记问题</Button></div>
              <Table columns={issueCols} dataSource={issues} rowKey="id" size="middle" locale={{ emptyText: <span style={sm}>暂无数据</span> }} pagination={{ pageSize: 10 }} /></> },
          ]} />
        </div>
      </Spin>

      <Modal title="登记问题" open={issueModal} onCancel={() => setIssueModal(false)} onOk={handleCreateIssue} okText="提交" cancelText="取消">
        <div className="space-y-3 py-2">
          <div><label className="text-sm mb-1 block" style={s}>关联类型</label><Select className="w-full" value={issueForm.related_type} onChange={(v) => setIssueForm({ ...issueForm, related_type: v })} options={[{ value: 'product', label: '商品' }, { value: 'stock_in', label: '入库单' }, { value: 'stock_out', label: '出库单' }, { value: 'order', label: '订单' }]} /></div>
          <div><label className="text-sm mb-1 block" style={s}>关联ID</label><Select className="w-full" value={issueForm.related_id || undefined} onChange={(v) => setIssueForm({ ...issueForm, related_id: v })} showSearch options={products.map((p: any) => ({ value: p.id, label: `${p.name} (${p.sku})` }))} /></div>
          <div><label className="text-sm mb-1 block" style={s}>严重程度</label><Select className="w-full" value={issueForm.severity} onChange={(v) => setIssueForm({ ...issueForm, severity: v })} options={[{ value: 'low', label: '低' }, { value: 'medium', label: '中' }, { value: 'high', label: '高' }, { value: 'critical', label: '严重' }]} /></div>
          <div><label className="text-sm mb-1 block" style={s}>问题描述</label><Input.TextArea value={issueForm.description} onChange={(e) => setIssueForm({ ...issueForm, description: e.target.value })} rows={3} placeholder="描述问题..." /></div>
        </div>
      </Modal>
    </div>
  )
}
