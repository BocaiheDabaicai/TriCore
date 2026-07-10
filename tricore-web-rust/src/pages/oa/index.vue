<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs, Space } from 'ant-design-vue'
import {
  PlusOutlined, EyeOutlined, CheckCircleOutlined, SendOutlined,
  AuditOutlined, EditOutlined, ReloadOutlined, DeleteOutlined,
  UpOutlined, DownOutlined, CloseOutlined,
} from '@ant-design/icons-vue'
import { oaAPI } from '@/services/api'

const loading = ref(true)
const employees = ref<any[]>([])
const workflows = ref<any[]>([])
const wfModal = ref(false)
const detailModal = ref(false)
const reviewModal = ref(false)
const editModal = ref(false)
const selectedWf = ref<any>(null)
const reviewForm = ref({ action: 'approve', comment: '' })
const wfForm = ref({ title: '', description: '', steps: [{ reviewer_id: '' }] as { reviewer_id: string }[] })
const editForm = ref({ title: '', description: '' })
const activeTab = ref('workflows')
const submitting = ref(false)
const saving = ref(false)

// ── Employee CRUD ──
const empModal = ref(false)
const editingEmp = ref<any>(null)
const empForm = ref({ employee_no: '', name: '', department: '', position: '', email: '', phone: '', password: '' })
const empSaving = ref(false)

const departments = computed(() => {
  const set = new Set(employees.value.map((e: any) => e.department).filter(Boolean))
  return Array.from(set).map((d) => ({ value: d, label: d }))
})

const positions = computed(() => {
  const set = new Set(employees.value.map((e: any) => e.position).filter(Boolean))
  return Array.from(set).map((p) => ({ value: p, label: p }))
})

const generateEmpNo = () => {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const seq = String(employees.value.length + 1).padStart(3, '0')
  return `EMP-${date}-${seq}`
}

const openEmpCreate = () => {
  editingEmp.value = null
  empForm.value = { employee_no: generateEmpNo(), name: '', department: '', position: '', email: '', phone: '', password: '' }
  empModal.value = true
}

const openEmpEdit = (record: any) => {
  editingEmp.value = record
  empForm.value = {
    employee_no: record.employee_no, name: record.name, department: record.department,
    position: record.position, email: record.email, phone: record.phone || '',
    password: '',
  }
  empModal.value = true
}

const handleEmpSave = async () => {
  const f = empForm.value
  if (!f.employee_no || !f.name || !f.department || !f.position || !f.email) { message.warning('请填写必填字段'); return }
  if (!editingEmp.value && !f.password) { message.warning('请输入密码'); return }
  empSaving.value = true
  try {
    if (editingEmp.value) {
      await oaAPI.updateEmployee(editingEmp.value.id, { name: f.name, department: f.department, position: f.position, email: f.email, phone: f.phone || undefined })
      message.success('员工信息已更新')
    } else {
      await oaAPI.createEmployee({ employee_no: f.employee_no, name: f.name, department: f.department, position: f.position, email: f.email, phone: f.phone || undefined, password: f.password })
      message.success('员工已创建')
    }
    empModal.value = false
    load()
  } catch (err: any) { message.error(err?.response?.data?.message || '操作失败') } finally { empSaving.value = false }
}

const handleEmpDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除员工「${record.name} (${record.employee_no})」吗？`,
    okText: '确认删除', okType: 'danger', cancelText: '取消',
    onOk: async () => { try { await oaAPI.deleteEmployee(record.id); message.success('已删除'); load() } catch { message.error('删除失败') } },
  })
}

const statusColors: Record<string, string> = { pending: 'default', in_progress: 'blue', approved: 'green', rejected: 'red', archived: 'purple' }
const statusLabels: Record<string, string> = { pending: '待提交', in_progress: '审批中', approved: '已通过', rejected: '已退回', archived: '已归档' }
const stepStatusLabels: Record<string, string> = { pending: '待审核', approved: '已通过', rejected: '已退回' }
const stepStatusColors: Record<string, string> = { pending: 'default', approved: 'green', rejected: 'red' }

const employeeMap = computed(() => {
  const m = new Map<string, any>()
  for (const e of employees.value) m.set(e.id, e)
  return m
})
const getEmployee = (id: string) => employeeMap.value.get(id)

const employeeOptions = computed(() =>
  employees.value.map((e: any) => ({ value: e.id, label: `${e.name} (${e.department})` }))
)

const load = async () => {
  loading.value = true
  try {
    const [e, w]: any[] = await Promise.all([oaAPI.listEmployees({ per_page: 100 }), oaAPI.listWorkflows({ per_page: 50 })])
    employees.value = e?.data?.data || e?.data || []; workflows.value = w?.data?.data || w?.data || []
  } catch { message.error('加载失败') } finally { loading.value = false }
}
onMounted(load)

// ── Multi-step creation ──
const addStep = () => wfForm.value.steps.push({ reviewer_id: '' })
const removeStep = (i: number) => {
  if (wfForm.value.steps.length <= 1) { message.warning('至少需要一个审核人'); return }
  wfForm.value.steps.splice(i, 1)
}
const moveUp = (i: number) => {
  if (i === 0) return
  const arr = wfForm.value.steps
  ;[arr[i - 1], arr[i]] = [arr[i], arr[i - 1]]
}
const moveDown = (i: number) => {
  const arr = wfForm.value.steps
  if (i >= arr.length - 1) return
  ;[arr[i + 1], arr[i]] = [arr[i], arr[i + 1]]
}

const handleCreate = async () => {
  if (!wfForm.value.title) { message.warning('请填写流程标题'); return }
  if (wfForm.value.steps.some((s) => !s.reviewer_id)) { message.warning('请为每个步骤选择审核人'); return }
  const steps = wfForm.value.steps.map((s, i) => ({ step_number: i + 1, reviewer_id: s.reviewer_id }))
  try {
    await oaAPI.createWorkflow({ title: wfForm.value.title, description: wfForm.value.description, steps })
    message.success('流程已创建')
    wfModal.value = false
    wfForm.value = { title: '', description: '', steps: [{ reviewer_id: '' }] }
    load()
  } catch (err: any) {
    message.error(err?.response?.data?.message || '创建失败')
  }
}

// ── Detail / Edit / Delete ──
const openDetail = async (id: string) => {
  try { const res: any = await oaAPI.getWorkflow(id); selectedWf.value = res?.data || res; detailModal.value = true } catch { message.error('加载失败') }
}
const openReview = async (id: string) => {
  try { const res: any = await oaAPI.getWorkflow(id); selectedWf.value = res?.data || res; reviewModal.value = true } catch { message.error('加载失败') }
}
const openEdit = async (id: string) => {
  try {
    const res: any = await oaAPI.getWorkflow(id)
    const wf = res?.data || res
    selectedWf.value = wf
    editForm.value = { title: wf.title || '', description: wf.description || '' }
    editModal.value = true
  } catch { message.error('加载失败') }
}

const submitWorkflow = async (id: string) => {
  submitting.value = true
  try { await oaAPI.submitWorkflow(id); message.success('流程已提交'); load() } catch { message.error('提交失败') } finally { submitting.value = false }
}

const handleSubmit = async () => {
  if (!selectedWf.value) return
  submitting.value = true
  try { await oaAPI.submitWorkflow(selectedWf.value.id); message.success('流程已提交'); detailModal.value = false; load() } catch { message.error('提交失败') } finally { submitting.value = false }
}

const handleUpdate = async () => {
  if (!selectedWf.value || !editForm.value.title) { message.warning('请填写标题'); return }
  saving.value = true
  try {
    await oaAPI.updateWorkflow(selectedWf.value.id, { title: editForm.value.title, description: editForm.value.description })
    message.success('已保存'); editModal.value = false; detailModal.value = false; load()
  } catch (err: any) { message.error(err?.response?.data?.message || '保存失败') } finally { saving.value = false }
}

const handleDelete = async (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除流程「${record.title}」吗？此操作不可恢复。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try { await oaAPI.deleteWorkflow(record.id); message.success('流程已删除'); load() } catch { message.error('删除失败') }
    },
  })
}

const handleReview = async () => {
  const step = selectedWf.value?.steps?.find((s: any) => s.status === 'pending')
  if (!step) { message.warning('没有待审核步骤'); return }
  try { await oaAPI.reviewStep(selectedWf.value.id, step.id, reviewForm.value); message.success(reviewForm.value.action === 'approve' ? '已通过' : '已退回'); reviewModal.value = false; load() } catch { message.error('操作失败') }
}

// ── Table columns ──
const wfCols = [
  { title: '流程标题', dataIndex: 'title', key: 'title',
    customRender: ({ text }: any) => h('span', { style: { fontWeight: 600, color: 'var(--text-primary)' } }, text) },
  { title: '状态', dataIndex: 'status', key: 'status', width: 90,
    customRender: ({ text }: any) => h(Tag, { color: statusColors[text] || 'default' }, () => statusLabels[text] || text) },
  { title: '进度', key: 'step', width: 70,
    customRender: ({ record }: any) => h('span', { style: { color: 'var(--text-secondary)', fontSize: '12px' } }, `${record.current_step}/${record.total_steps}`) },
  { title: '创建时间', dataIndex: 'created_at', key: 'time', width: 110,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleDateString('zh-CN')) },
  { title: '操作', key: 'action', width: 220,
    customRender: ({ record }: any) => {
      const btns = [h(Button, { type: 'link', size: 'small', onClick: () => openDetail(record.id) }, () => [h(EyeOutlined), ' 详情'])]
      if (record.status === 'pending') {
        btns.push(h(Button, { type: 'link', size: 'small', onClick: () => openEdit(record.id) }, () => [h(EditOutlined), ' 修改']))
        btns.push(h(Button, { type: 'link', size: 'small', onClick: () => submitWorkflow(record.id) }, () => [h(SendOutlined), ' 提交']))
        btns.push(h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleDelete(record) }, () => [h(DeleteOutlined)]))
      }
      if (record.status === 'in_progress') {
        btns.push(h(Button, { type: 'link', size: 'small', onClick: () => openReview(record.id) }, () => [h(CheckCircleOutlined), ' 审核']))
      }
      if (record.status === 'rejected') {
        btns.push(h(Button, { type: 'link', size: 'small', onClick: () => openEdit(record.id) }, () => [h(EditOutlined), ' 修改']))
        btns.push(h(Button, { type: 'link', size: 'small', onClick: () => submitWorkflow(record.id) }, () => [h(ReloadOutlined), ' 重新提交']))
        btns.push(h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleDelete(record) }, () => [h(DeleteOutlined)]))
      }
      return h(Space, { size: 4 }, () => btns)
    }},
]

const empCols = [
  { title: '工号', dataIndex: 'employee_no', key: 'no', width: 150,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: 500 } }, text) },
  { title: '姓名', dataIndex: 'name', key: 'name',
    customRender: ({ text }: any) => h('span', { style: { fontWeight: 500 } }, text) },
  { title: '部门', dataIndex: 'department', key: 'dept', width: 100,
    customRender: ({ text }: any) => h(Tag, {}, () => text) },
  { title: '职位', dataIndex: 'position', key: 'pos' },
  { title: '邮箱', dataIndex: 'email', key: 'email',
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, text) },
  { title: '操作', key: 'action', width: 110,
    customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
      h(Button, { type: 'link', size: 'small', onClick: () => openEmpEdit(record) }, () => [h(EditOutlined), ' 编辑']),
      h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleEmpDelete(record) }, () => [h(DeleteOutlined)]),
    ])},
]
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">办公协同</h2>
      <p>流程审批 · 员工管理 · 归档查阅</p>
    </div>
    <Spin :spinning="loading">
      <div class="glass-card p-6">
        <Tabs v-model:activeKey="activeTab">
          <a-tab-pane key="workflows" :tab="`审批流程 (${workflows.length})`">
            <div class="mb-3"><Button type="primary" @click="wfModal = true"><PlusOutlined /> 新建流程</Button></div>
            <Table :columns="wfCols" :dataSource="workflows" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
          <a-tab-pane key="employees" :tab="`员工列表 (${employees.length})`">
            <div class="mb-3"><Button type="primary" @click="openEmpCreate"><PlusOutlined /> 添加员工</Button></div>
            <Table :columns="empCols" :dataSource="employees" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>

        </Tabs>
      </div>
    </Spin>

    <!-- ═══ Create workflow modal (multi-step) ═══ -->
    <Modal v-model:open="wfModal" title="新建审批流程" @ok="handleCreate" okText="创建" cancelText="取消" :width="560">
      <div class="space-y-3 py-2">
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">流程标题</label><Input v-model:value="wfForm.title" placeholder="例如：采购申请" /></div>
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">描述</label><Input v-model:value="wfForm.description" placeholder="流程说明" /></div>
        </div>

        <!-- Steps -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-medium" :style="{ color: 'var(--text-secondary)' }">审核步骤 ({{ wfForm.steps.length }})</label>
            <Button type="link" size="small" @click="addStep"><PlusOutlined /> 添加审核人</Button>
          </div>
          <div class="space-y-2">
            <div v-for="(step, i) in wfForm.steps" :key="i"
              class="flex items-center gap-2 p-2 rounded-lg border" :style="{ borderColor: 'var(--border-subtle)', background: 'var(--input-bg)' }"
            >
              <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 text-white"
                style="background: var(--accent)">{{ i + 1 }}</span>
              <Select
                v-model:value="step.reviewer_id"
                class="flex-1"
                placeholder="选择审核人"
                :options="employeeOptions"
                showSearch
                :filterOption="(input: string, option: any) => option.label.toLowerCase().includes(input.toLowerCase())"
              />
              <div class="flex items-center gap-0.5 flex-shrink-0">
                <Button type="text" size="small" :disabled="i === 0" @click="moveUp(i)"><UpOutlined /></Button>
                <Button type="text" size="small" :disabled="i >= wfForm.steps.length - 1" @click="moveDown(i)"><DownOutlined /></Button>
                <Button type="text" size="small" danger @click="removeStep(i)"><CloseOutlined /></Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Modal>

    <!-- ═══ Detail modal ═══ -->
    <Modal v-model:open="detailModal" :footer="null" :width="720">
      <template #title>
        <div class="flex items-center gap-2">
          <AuditOutlined :style="{ color: 'var(--accent)' }" />
          <span>{{ selectedWf?.title || '流程详情' }}</span>
        </div>
      </template>
      <div v-if="selectedWf" class="space-y-5 py-1">
        <div class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '56px' }">状态</span>
            <Tag :color="statusColors[selectedWf.status]">{{ statusLabels[selectedWf.status] || selectedWf.status }}</Tag>
          </div>
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '56px' }">进度</span>
            <span :style="{ color: 'var(--text-primary)', fontSize: '13px', fontWeight: 500 }">第 {{ selectedWf.current_step }}/{{ selectedWf.total_steps }} 步</span>
          </div>
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '56px' }">创建人</span>
            <span :style="{ color: 'var(--text-primary)', fontSize: '13px' }">
              <template v-if="getEmployee(selectedWf.creator_id)">
                {{ getEmployee(selectedWf.creator_id).name }}
                <span :style="{ color: 'var(--text-muted)', fontSize: '11px' }">({{ getEmployee(selectedWf.creator_id).department }})</span>
              </template>
              <template v-else>—</template>
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '56px' }">创建时间</span>
            <span :style="{ color: 'var(--text-primary)', fontSize: '13px' }">{{ new Date(selectedWf.created_at).toLocaleString('zh-CN') }}</span>
          </div>
        </div>

        <div v-if="selectedWf.description" class="p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <p class="text-xs mb-1 font-medium" :style="{ color: 'var(--text-muted)' }">流程说明</p>
          <p class="text-sm" :style="{ color: 'var(--text-secondary)' }">{{ selectedWf.description }}</p>
        </div>

        <div>
          <p class="text-xs font-semibold mb-3" :style="{ color: 'var(--text-secondary)' }">审批步骤</p>
          <div class="space-y-2">
            <div v-for="(step, i) in selectedWf.steps" :key="i">
              <div v-if="i > 0" class="flex justify-center" :style="{ height: '8px' }">
                <div :style="{ width: '2px', height: '100%', background: step.status !== 'pending' ? 'var(--accent)' : 'var(--border-subtle)' }" />
              </div>
              <div class="flex items-center gap-4 p-3 rounded-xl border transition-all"
                :style="{
                  borderColor: step.status === 'approved' ? 'var(--success)' : step.status === 'rejected' ? 'var(--danger)' : step.status === 'pending' && selectedWf.status === 'in_progress' ? 'var(--accent)' : 'var(--border-subtle)',
                  background: step.status === 'pending' && selectedWf.status === 'in_progress' ? 'var(--accent-soft)' : 'var(--bg-card)',
                }"
              >
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  :style="{ background: step.status === 'approved' ? 'var(--success)' : step.status === 'rejected' ? 'var(--danger)' : 'var(--accent)', color: '#fff' }">
                  {{ step.step_number }}
                </div>
                <div class="flex-1 min-w-0">
                  <template v-if="getEmployee(step.reviewer_id)">
                    <p class="text-sm font-semibold" :style="{ color: 'var(--text-primary)' }">{{ getEmployee(step.reviewer_id).name }}</p>
                    <p class="text-xs" :style="{ color: 'var(--text-muted)' }">{{ getEmployee(step.reviewer_id).department }} · {{ getEmployee(step.reviewer_id).position }}</p>
                  </template>
                  <template v-else><p class="text-sm" :style="{ color: 'var(--text-muted)' }">未知审核人</p></template>
                </div>
                <Tag :color="stepStatusColors[step.status] || 'default'">{{ stepStatusLabels[step.status] || step.status }}</Tag>
                <div v-if="step.comment" class="text-xs italic px-2" :style="{ color: 'var(--text-muted)', maxWidth: '160px' }" :title="step.comment">"{{ step.comment }}"</div>
                <Button v-if="step.status === 'pending' && selectedWf.status === 'in_progress'" type="primary" size="small"
                  @click="() => { reviewForm = { action: 'approve', comment: '' }; detailModal = false; reviewModal = true }"><CheckCircleOutlined /> 审核</Button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="selectedWf.status === 'pending'" class="flex justify-end gap-2 pt-2 border-t" :style="{ borderColor: 'var(--border-subtle)' }">
          <Button @click="() => { editForm = { title: selectedWf.title, description: selectedWf.description || '' }; detailModal = false; editModal = true }"><EditOutlined /> 修改</Button>
          <Button danger @click="() => { handleDelete(selectedWf); detailModal = false }"><DeleteOutlined /> 删除</Button>
          <Button type="primary" :loading="submitting" @click="handleSubmit"><SendOutlined /> 提交审批</Button>
        </div>

        <div v-if="selectedWf.status === 'rejected'" class="flex justify-end gap-2 pt-2 border-t" :style="{ borderColor: 'var(--border-subtle)' }">
          <Button @click="() => { editForm = { title: selectedWf.title, description: selectedWf.description || '' }; detailModal = false; editModal = true }"><EditOutlined /> 修改流程</Button>
          <Button type="primary" :loading="submitting" @click="handleSubmit"><ReloadOutlined /> 重新提交</Button>
        </div>
      </div>
    </Modal>

    <!-- ═══ Edit modal ═══ -->
    <Modal v-model:open="editModal" title="修改流程" @ok="handleUpdate" :confirmLoading="saving" okText="保存" cancelText="取消" :width="480">
      <div class="space-y-3 py-2">
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">流程标题</label><Input v-model:value="editForm.title" placeholder="流程标题" /></div>
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">描述</label><Input.TextArea v-model:value="editForm.description" :rows="3" placeholder="补充说明..." /></div>
        <div class="p-3 rounded-lg text-xs" :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">
          保存后可使用「提交审批」或「重新提交」将流程送审。
        </div>
      </div>
    </Modal>

    <!-- ═══ Employee modal (create / edit) ═══ -->
    <Modal v-model:open="empModal" :title="editingEmp ? '编辑员工' : '添加员工'" @ok="handleEmpSave" :confirmLoading="empSaving" okText="保存" cancelText="取消" :width="520">
      <div class="grid grid-cols-2 gap-3 py-2">
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">工号 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <div class="flex gap-1">
            <Input v-model:value="empForm.employee_no" placeholder="EMP-20260101-001" :disabled="!!editingEmp" class="flex-1" />
            <Button v-if="!editingEmp" size="small" @click="empForm.employee_no = generateEmpNo()" :style="{ color: 'var(--accent)' }">生成</Button>
          </div>
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">姓名 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <Input v-model:value="empForm.name" placeholder="姓名" />
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">部门 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <Select v-model:value="empForm.department" class="w-full" placeholder="选择部门" :options="departments" showSearch allowClear />
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">职位 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <Select v-model:value="empForm.position" class="w-full" placeholder="选择职位" :options="positions" showSearch allowClear />
        </div>
        <div class="col-span-2">
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">邮箱 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <Input v-model:value="empForm.email" placeholder="email@tricore.com" />
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">电话</label>
          <Input v-model:value="empForm.phone" placeholder="手机号" />
        </div>
        <div v-if="!editingEmp">
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">密码 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <Input.Password v-model:value="empForm.password" placeholder="登录密码" />
        </div>
      </div>
    </Modal>

    <!-- ═══ Review modal ═══ -->
    <Modal v-model:open="reviewModal" title="审批操作" @ok="handleReview" okText="提交" cancelText="取消" :width="420">
      <div class="space-y-3 py-2">
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">操作</label><Select v-model:value="reviewForm.action" class="w-full" :options="[{value:'approve',label:'通过'},{value:'reject',label:'退回'}]" /></div>
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label><Input.TextArea v-model:value="reviewForm.comment" :rows="3" placeholder="审核意见..." /></div>
      </div>
    </Modal>

  </div>
</template>
