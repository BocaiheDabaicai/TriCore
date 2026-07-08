import { useEffect, useState } from 'react'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs, Space } from 'antd'
import { PlusOutlined, EyeOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { oaAPI } from '../../services/api'

const statusColors: Record<string, string> = { pending: 'default', in_progress: 'blue', approved: 'green', rejected: 'red', archived: 'purple' }
const s = { color: 'var(--text-secondary)' }
const sm = { color: 'var(--text-muted)' }
const tp = { color: 'var(--text-primary)' }

export default function OADashboard() {
  const [employees, setEmployees] = useState<any[]>([])
  const [workflows, setWorkflows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [wfModal, setWfModal] = useState(false)
  const [detailModal, setDetailModal] = useState(false)
  const [reviewModal, setReviewModal] = useState(false)
  const [selectedWf, setSelectedWf] = useState<any>(null)
  const [reviewForm, setReviewForm] = useState({ action: 'approve', comment: '' })
  const [wfForm, setWfForm] = useState({ title: '', description: '', reviewer_id: '' })

  const loadData = async () => {
    setLoading(true)
    try {
      const [empRes, wfRes]: any[] = await Promise.all([oaAPI.listEmployees({ per_page: 100 }), oaAPI.listWorkflows({ per_page: 50 })])
      setEmployees(empRes?.data?.data || empRes?.data || [])
      setWorkflows(wfRes?.data?.data || wfRes?.data || [])
    } catch { message.error('加载数据失败') } finally { setLoading(false) }
  }
  useEffect(() => { loadData() }, [])

  const handleCreateWf = async () => {
    if (!wfForm.title || !wfForm.reviewer_id) { message.warning('请填写标题和审核人'); return }
    try {
      await oaAPI.createWorkflow({ title: wfForm.title, description: wfForm.description, steps: [{ step_number: 1, reviewer_id: wfForm.reviewer_id }] })
      message.success('流程已创建'); setWfModal(false); setWfForm({ title: '', description: '', reviewer_id: '' }); loadData()
    } catch { message.error('创建失败') }
  }

  const openDetail = async (id: string) => {
    try { const res: any = await oaAPI.getWorkflow(id); setSelectedWf(res?.data || res); setDetailModal(true) } catch { message.error('加载失败') }
  }

  const handleReview = async () => {
    const step = selectedWf?.steps?.find((s: any) => s.status === 'pending')
    if (!step) { message.warning('没有待审核的步骤'); return }
    try { await oaAPI.reviewStep(selectedWf.id, step.id, reviewForm); message.success(reviewForm.action === 'approve' ? '已通过' : '已退回'); setReviewModal(false); loadData() } catch { message.error('操作失败') }
  }

  const wfColumns = [
    { title: '流程标题', dataIndex: 'title', key: 'title', render: (v: string) => <span className="font-medium" style={tp}>{v}</span> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={statusColors[v] || 'default'}>{v === 'in_progress' ? '审批中' : v === 'pending' ? '待提交' : v === 'approved' ? '已通过' : v === 'rejected' ? '已退回' : v}</Tag> },
    { title: '当前步骤', key: 'step', render: (_: any, r: any) => <span style={s}>{r.current_step}/{r.total_steps}</span> },
    { title: '时间', dataIndex: 'created_at', key: 'time', render: (v: string) => <span className="text-xs" style={sm}>{new Date(v).toLocaleDateString('zh-CN')}</span> },
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <Space>
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => openDetail(r.id)}>详情</Button>
        {r.status === 'in_progress' && <Button type="link" size="small" icon={<CheckCircleOutlined />} onClick={async () => { await openDetail(r.id); setReviewModal(true) }}>审核</Button>}
      </Space>
    )},
  ]

  const empColumns = [
    { title: '工号', dataIndex: 'employee_no', key: 'no', render: (v: string) => <span className="text-indigo-500 font-mono text-xs">{v}</span> },
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '部门', dataIndex: 'department', key: 'dept', render: (v: string) => <Tag>{v}</Tag> },
    { title: '职位', dataIndex: 'position', key: 'pos' },
    { title: '邮箱', dataIndex: 'email', key: 'email', render: (v: string) => <span className="text-xs" style={sm}>{v}</span> },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 gradient-text">办公协同</h2>
      <p className="text-sm mb-6" style={sm}>流程审批 · 员工管理 · 归档查阅</p>
      <Spin spinning={loading}>
        <div className="glass-card p-4">
          <Tabs items={[
            { key: 'workflows', label: <span>🔄 审批流程 <span className="text-xs ml-1" style={sm}>({workflows.length})</span></span>,
              children: <><div className="mb-3"><Button type="primary" icon={<PlusOutlined />} onClick={() => setWfModal(true)}>新建流程</Button></div>
              <Table columns={wfColumns} dataSource={workflows} rowKey="id" size="middle" locale={{ emptyText: <span style={sm}>暂无数据</span> }} pagination={{ pageSize: 10 }} /></> },
            { key: 'employees', label: <span>👥 员工列表 <span className="text-xs ml-1" style={sm}>({employees.length})</span></span>,
              children: <Table columns={empColumns} dataSource={employees} rowKey="id" size="middle" locale={{ emptyText: <span style={sm}>暂无数据</span> }} pagination={{ pageSize: 10 }} /> },
          ]} />
        </div>
      </Spin>

      <Modal title="新建审批流程" open={wfModal} onCancel={() => setWfModal(false)} onOk={handleCreateWf} okText="创建" cancelText="取消">
        <div className="space-y-3 py-2">
          <div><label className="text-sm mb-1 block" style={s}>流程标题</label><Input value={wfForm.title} onChange={(e) => setWfForm({ ...wfForm, title: e.target.value })} placeholder="例如：采购申请" /></div>
          <div><label className="text-sm mb-1 block" style={s}>描述</label><Input.TextArea value={wfForm.description} onChange={(e) => setWfForm({ ...wfForm, description: e.target.value })} rows={2} placeholder="流程说明" /></div>
          <div><label className="text-sm mb-1 block" style={s}>第一审核人</label><Select className="w-full" value={wfForm.reviewer_id || undefined} onChange={(v) => setWfForm({ ...wfForm, reviewer_id: v })} placeholder="选择员工" options={employees.map((e: any) => ({ value: e.id, label: `${e.name} (${e.department})` }))} /></div>
        </div>
      </Modal>

      <Modal title={`流程详情 — ${selectedWf?.title || ''}`} open={detailModal} onCancel={() => { setDetailModal(false); setSelectedWf(null) }} footer={null} width={640}>
        {selectedWf && (
          <div className="space-y-4 py-2">
            <div className="text-sm"><span style={sm}>状态：</span><Tag color={statusColors[selectedWf.status]}>{selectedWf.status}</Tag></div>
            <p style={s}>{selectedWf.description || '无描述'}</p>
            {selectedWf.steps?.map((step: any, i: number) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b text-sm" style={{ borderColor: 'var(--border-subtle)' }}>
                <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs" style={{ background: 'var(--input-bg)' }}>{step.step_number}</span>
                <span className="flex-1" style={s}>{step.reviewer_id?.slice(0, 8)}...</span>
                <Tag color={step.status === 'approved' ? 'green' : step.status === 'rejected' ? 'red' : 'default'}>{step.status}</Tag>
                {step.comment && <span className="text-xs" style={sm}>"{step.comment}"</span>}
              </div>
            ))}
          </div>
        )}
      </Modal>

      <Modal title="审批操作" open={reviewModal} onCancel={() => setReviewModal(false)} onOk={handleReview} okText="提交" cancelText="取消">
        <div className="space-y-3 py-2">
          <div><label className="text-sm mb-1 block" style={s}>操作</label><Select className="w-full" value={reviewForm.action} onChange={(v) => setReviewForm({ ...reviewForm, action: v })} options={[{ value: 'approve', label: '✅ 通过' }, { value: 'reject', label: '❌ 退回' }]} /></div>
          <div><label className="text-sm mb-1 block" style={s}>备注</label><Input.TextArea value={reviewForm.comment} onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })} rows={3} placeholder="审核意见..." /></div>
        </div>
      </Modal>
    </div>
  )
}
