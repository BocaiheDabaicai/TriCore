import { useEffect, useState } from 'react'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs } from 'antd'
import { PlusOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { inventoryAPI } from '../../services/api'
import type { TabsProps } from 'antd'

export default function InventoryDashboard() {
  const [products, setProducts] = useState<any[]>([])
  const [stockIn, setStockIn] = useState<any[]>([])
  const [stockOut, setStockOut] = useState<any[]>([])
  const [issues, setIssues] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [issueModal, setIssueModal] = useState(false)
  const [issueForm, setIssueForm] = useState({ description: '', severity: 'medium', related_type: 'product', related_id: '', reported_by: '' })
  const [activeTab, setActiveTab] = useState('stock')

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
      title: '解决问题',
      content: <Input.TextArea id="resolution" rows={3} placeholder="解决方案..." />,
      okText: '确认解决',
      cancelText: '取消',
      onOk: async () => {
        const el = document.getElementById('resolution') as HTMLTextAreaElement
        try { await inventoryAPI.resolveIssue(id, { resolution: el?.value || '已解决' }); message.success('已解决'); loadData() } catch { message.error('操作失败') }
      },
    })
  }

  const severityColor: Record<string, string> = { critical: 'magenta', high: 'red', medium: 'orange', low: 'green' }
  const severityLabel: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }

  const productCols = [
    { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 100,
      render: (v: string) => <span style={{ color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: 12, fontWeight: 500 }}>{v}</span> },
    { title: '商品名称', dataIndex: 'name', key: 'name',
      render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span> },
    { title: '库存', dataIndex: 'quantity', key: 'qty', width: 100,
      render: (v: number) => {
        const color = v < 50 ? 'var(--danger)' : v < 200 ? 'var(--warning)' : 'var(--success)'
        return <span style={{ color, fontWeight: 600, fontFamily: 'ui-monospace, monospace' }}>{v} {v < 50 && <WarningOutlined style={{ fontSize: 11 }} />}</span>
      }},
    { title: '单价', dataIndex: 'original_price', key: 'price', width: 100,
      render: (v: number) => <span style={{ color: '#f59e0b', fontFamily: 'ui-monospace, monospace', fontSize: 13 }}>¥{Number(v).toFixed(2)}</span> },
    { title: '分类', dataIndex: 'category', key: 'cat', width: 90,
      render: (v: string) => v ? <Tag>{v}</Tag> : <span style={{ color: 'var(--text-muted)' }}>—</span> },
  ]

  const issueCols = [
    { title: '问题描述', dataIndex: 'description', key: 'desc', ellipsis: true,
      render: (v: string) => <span style={{ color: 'var(--text-primary)' }}>{v}</span> },
    { title: '类型', dataIndex: 'related_type', key: 'type', width: 80,
      render: (v: string) => <Tag>{v}</Tag> },
    { title: '严重程度', dataIndex: 'severity', key: 'sev', width: 90,
      render: (v: string) => <Tag color={severityColor[v] || 'default'}>{severityLabel[v] || v}</Tag> },
    { title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (v: string) => {
        const color = v === 'open' ? 'red' : v === 'in_progress' ? 'blue' : 'green'
        return <Tag color={color}>{v}</Tag>
      }},
    { title: '操作', key: 'action', width: 80,
      render: (_: any, r: any) =>
        (r.status !== 'resolved' && r.status !== 'closed')
          ? <Button type="link" size="small" icon={<CheckCircleOutlined />} onClick={() => handleResolve(r.id)}>解决</Button>
          : <span style={{ color: 'var(--success)', fontSize: 12 }}>已解决</span>
      },
  ]

  const siCols = [
    { title: '入库单号', dataIndex: 'stock_in_no', key: 'no', width: 140,
      render: (v: string) => <span style={{ color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: 12 }}>{v}</span> },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (v: string) => <Tag color={v === 'completed' ? 'green' : 'default'}>{v}</Tag> },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true,
      render: (v: string) => v || <span style={{ color: 'var(--text-muted)' }}>—</span> },
    { title: '时间', dataIndex: 'created_at', key: 'time', width: 110,
      render: (v: string) => <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{new Date(v).toLocaleDateString('zh-CN')}</span> },
  ]

  const soCols = [
    { title: '出库单号', dataIndex: 'stock_out_no', key: 'no', width: 140,
      render: (v: string) => <span style={{ color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: 12 }}>{v}</span> },
    { title: '车辆信息', dataIndex: 'vehicle_info', key: 'vehicle', width: 140,
      render: (v: string) => v || <span style={{ color: 'var(--text-muted)' }}>—</span> },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (v: string) => <Tag color={v === 'delivered' ? 'green' : v === 'shipped' ? 'blue' : 'default'}>{v}</Tag> },
    { title: '时间', dataIndex: 'created_at', key: 'time', width: 110,
      render: (v: string) => <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{new Date(v).toLocaleDateString('zh-CN')}</span> },
  ]

  const tabItems: TabsProps['items'] = [
    { key: 'stock', label: `库存 (${products.length})`,
      children: <Table columns={productCols} dataSource={products} rowKey="id" size="small" locale={{ emptyText: '暂无数据' }} pagination={{ pageSize: 10, showSizeChanger: false }} /> },
    { key: 'stock-in', label: `入库 (${stockIn.length})`,
      children: <Table columns={siCols} dataSource={stockIn} rowKey="id" size="small" locale={{ emptyText: '暂无数据' }} pagination={{ pageSize: 10, showSizeChanger: false }} /> },
    { key: 'stock-out', label: `出库 (${stockOut.length})`,
      children: <Table columns={soCols} dataSource={stockOut} rowKey="id" size="small" locale={{ emptyText: '暂无数据' }} pagination={{ pageSize: 10, showSizeChanger: false }} /> },
    { key: 'issues', label: `问题 (${issues.length})`,
      children: <>
        <div className="mb-3"><Button type="primary" icon={<PlusOutlined />} onClick={() => { setIssueForm({ description: '', severity: 'medium', related_type: 'product', related_id: products[0]?.id || '', reported_by: '' }); setIssueModal(true) }}>登记问题</Button></div>
        <Table columns={issueCols} dataSource={issues} rowKey="id" size="small" locale={{ emptyText: '暂无数据' }} pagination={{ pageSize: 10, showSizeChanger: false }} />
      </> },
  ]

  return (
    <div>
      <div className="page-header">
        <h2 className="gradient-text">库存管理</h2>
        <p>入库 · 出库 · 盘点 · 问题追踪</p>
      </div>
      <Spin spinning={loading}>
        <div className="glass-card p-5">
          <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
        </div>
      </Spin>

      <Modal title="登记问题" open={issueModal} onCancel={() => setIssueModal(false)} onOk={handleCreateIssue} okText="提交" cancelText="取消" width={480}>
        <div className="space-y-3 py-2">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs mb-1.5 block font-medium" style={{ color: 'var(--text-secondary)' }}>关联类型</label><Select className="w-full" value={issueForm.related_type} onChange={(v) => setIssueForm({ ...issueForm, related_type: v })} options={[{ value: 'product', label: '商品' }, { value: 'stock_in', label: '入库单' }, { value: 'stock_out', label: '出库单' }, { value: 'order', label: '订单' }]} /></div>
            <div><label className="text-xs mb-1.5 block font-medium" style={{ color: 'var(--text-secondary)' }}>严重程度</label><Select className="w-full" value={issueForm.severity} onChange={(v) => setIssueForm({ ...issueForm, severity: v })} options={[{ value: 'low', label: '低' }, { value: 'medium', label: '中' }, { value: 'high', label: '高' }, { value: 'critical', label: '严重' }]} /></div>
          </div>
          <div><label className="text-xs mb-1.5 block font-medium" style={{ color: 'var(--text-secondary)' }}>关联商品</label><Select className="w-full" value={issueForm.related_id || undefined} onChange={(v) => setIssueForm({ ...issueForm, related_id: v })} showSearch placeholder="选择商品" options={products.map((p: any) => ({ value: p.id, label: `${p.name} (${p.sku})` }))} /></div>
          <div><label className="text-xs mb-1.5 block font-medium" style={{ color: 'var(--text-secondary)' }}>问题描述</label><Input.TextArea value={issueForm.description} onChange={(e) => setIssueForm({ ...issueForm, description: e.target.value })} rows={3} placeholder="描述问题..." /></div>
        </div>
      </Modal>
    </div>
  )
}
