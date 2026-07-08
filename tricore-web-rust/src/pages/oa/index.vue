<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs } from 'ant-design-vue'
import { PlusOutlined, EyeOutlined, CheckCircleOutlined } from '@ant-design/icons-vue'
import { oaAPI } from '@/services/api'

const loading = ref(true)
const employees = ref<any[]>([])
const workflows = ref<any[]>([])
const wfModal = ref(false)
const detailModal = ref(false)
const reviewModal = ref(false)
const selectedWf = ref<any>(null)
const reviewForm = ref({ action: 'approve', comment: '' })
const wfForm = ref({ title: '', description: '', reviewer_id: '' })

const load = async () => {
  loading.value = true
  try {
    const [e, w]: any[] = await Promise.all([oaAPI.listEmployees({ per_page: 100 }), oaAPI.listWorkflows({ per_page: 50 })])
    employees.value = e?.data?.data || e?.data || []; workflows.value = w?.data?.data || w?.data || []
  } catch { message.error('加载失败') } finally { loading.value = false }
}
onMounted(load)

const handleCreate = async () => {
  if (!wfForm.value.title || !wfForm.value.reviewer_id) { message.warning('请填写标题和审核人'); return }
  try { await oaAPI.createWorkflow({ title: wfForm.value.title, description: wfForm.value.description, steps: [{ step_number: 1, reviewer_id: wfForm.value.reviewer_id }] }); message.success('已创建'); wfModal.value = false; load() } catch { message.error('创建失败') }
}

const openDetail = async (id: string) => { try { const res: any = await oaAPI.getWorkflow(id); selectedWf.value = res?.data || res; detailModal.value = true } catch { message.error('加载失败') } }

const handleReview = async () => {
  const step = selectedWf.value?.steps?.find((s: any) => s.status === 'pending')
  if (!step) { message.warning('没有待审核步骤'); return }
  try { await oaAPI.reviewStep(selectedWf.value.id, step.id, reviewForm.value); message.success(reviewForm.value.action === 'approve' ? '已通过' : '已退回'); reviewModal.value = false; load() } catch { message.error('操作失败') }
}

const wfCols = [
  { title: '流程标题', dataIndex: 'title', key: 'title' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '当前步骤', key: 'step', customRender: ({ record }: any) => `${record.current_step}/${record.total_steps}` },
  { title: '操作', key: 'action', customRender: ({ record }: any) => {
    const btns = [h(Button, { type: 'link', size: 'small', onClick: () => openDetail(record.id) }, () => [h(EyeOutlined), ' 详情'])]
    if (record.status === 'in_progress') btns.push(h(Button, { type: 'link', size: 'small', onClick: async () => { await openDetail(record.id); reviewModal.value = true } }, () => [h(CheckCircleOutlined), ' 审核']))
    return h('span', btns)
  }},
]
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-2 gradient-text">办公协同</h2>
    <p class="text-sm mb-6" :style="{ color: 'var(--text-muted)' }">流程审批 · 员工管理 · 归档查阅</p>
    <Spin :spinning="loading">
      <div class="glass-card p-4">
        <Tabs :items="[{ key:'workflows', tab:`🔄 审批流程 (${workflows.length})` }, { key:'employees', tab:`👥 员工列表 (${employees.length})` }]" />
        <div class="mb-3 mt-3"><Button type="primary" @click="wfModal = true"><PlusOutlined /> 新建流程</Button></div>
        <Table :columns="wfCols" :dataSource="workflows" rowKey="id" size="middle" :pagination="{ pageSize: 10 }" />
      </div>
    </Spin>

    <Modal v-model:open="wfModal" title="新建审批流程" @ok="handleCreate" okText="创建" cancelText="取消">
      <div class="space-y-3 py-2">
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">流程标题</label><Input v-model:value="wfForm.title" placeholder="例如：采购申请" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">描述</label><Input.TextArea v-model:value="wfForm.description" :rows="2" placeholder="流程说明" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">第一审核人</label><Select v-model:value="wfForm.reviewer_id" class="w-full" placeholder="选择员工" :options="employees.map((e:any)=>({value:e.id,label:`${e.name} (${e.department})`}))" /></div>
      </div>
    </Modal>

    <Modal v-model:open="detailModal" :title="`流程详情 — ${selectedWf?.title || ''}`" :footer="null" width="640px">
      <div v-if="selectedWf" class="space-y-4 py-2">
        <div v-for="(step, i) in selectedWf.steps" :key="i" class="flex items-center gap-3 py-2 border-b text-sm" :style="{ borderColor: 'var(--border-subtle)' }">
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs" :style="{ background: 'var(--input-bg)' }">{{ step.step_number }}</span>
          <span class="flex-1" :style="{ color: 'var(--text-secondary)' }">{{ step.reviewer_id?.slice(0, 8) }}...</span>
          <Tag :color="step.status==='approved'?'green':step.status==='rejected'?'red':'default'">{{ step.status }}</Tag>
        </div>
      </div>
    </Modal>

    <Modal v-model:open="reviewModal" title="审批操作" @ok="handleReview" okText="提交" cancelText="取消">
      <div class="space-y-3 py-2">
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">操作</label><Select v-model:value="reviewForm.action" class="w-full" :options="[{value:'approve',label:'✅ 通过'},{value:'reject',label:'❌ 退回'}]" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">备注</label><Input.TextArea v-model:value="reviewForm.comment" :rows="3" placeholder="审核意见..." /></div>
      </div>
    </Modal>
  </div>
</template>
