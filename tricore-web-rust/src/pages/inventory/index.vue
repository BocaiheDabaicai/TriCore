<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { Table, Tag, Button, Modal, Input, InputNumber, Select, message, Spin, Tabs, Space } from 'ant-design-vue'
import { PlusOutlined, CheckCircleOutlined, EditOutlined } from '@ant-design/icons-vue'
import { inventoryAPI, oaAPI } from '@/services/api'

const loading = ref(true)
const products = ref<any[]>([])
const stockIn = ref<any[]>([])
const stockOut = ref<any[]>([])
const issues = ref<any[]>([])
const warehouses = ref<any[]>([])
const employees = ref<any[]>([])
const issueModal = ref(false)
const adjustModal = ref(false)
const adjustingProduct = ref<any>(null)
const issueForm = ref({ description: '', severity: 'medium', related_type: 'product', related_id: '', reported_by: '' })
const adjustForm = ref({ type: 'in' as 'in' | 'out', quantity: 1, notes: '', warehouse_id: '' })
const adjustSubmitting = ref(false)
const activeTab = ref('stock')

const severityColor: Record<string, string> = { critical: 'magenta', high: 'red', medium: 'orange', low: 'green' }
const severityLabel: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }

const defaultWarehouseId = computed(() => warehouses.value[0]?.id || '')
const defaultOperatorId = computed(() => employees.value[0]?.id || '')

const load = async () => {
  loading.value = true
  try {
    const [p, si, so, iss, wh, emp]: any[] = await Promise.all([
      inventoryAPI.listProducts(),
      inventoryAPI.listStockIn({ per_page: 50 }),
      inventoryAPI.listStockOut({ per_page: 50 }),
      inventoryAPI.listIssues({ per_page: 50 }),
      inventoryAPI.listWarehouses().catch(() => ({ data: [] })),
      oaAPI.listEmployees({ per_page: 999 }).catch(() => ({ data: [] })),
    ])
    products.value = p?.data || []
    stockIn.value = si?.data?.data || si?.data || []
    stockOut.value = so?.data?.data || so?.data || []
    issues.value = iss?.data?.data || iss?.data || []
    warehouses.value = wh?.data || []
    employees.value = emp?.data?.data || emp?.data || []
  } catch { message.error('加载数据失败') } finally { loading.value = false }
}
onMounted(load)

const openAdjust = (product: any) => {
  adjustingProduct.value = product
  adjustForm.value = { type: 'in', quantity: 1, notes: '', warehouse_id: defaultWarehouseId.value }
  adjustModal.value = true
}

const handleAdjust = async () => {
  if (!adjustingProduct.value || adjustForm.value.quantity <= 0) {
    message.warning('请输入有效的调整数量')
    return
  }
  if (!adjustForm.value.warehouse_id) { message.warning('请选择仓库'); return }
  if (!defaultOperatorId.value) { message.warning('没有可用的操作员'); return }

  adjustSubmitting.value = true
  try {
    if (adjustForm.value.type === 'in') {
      // Stock-in flow: create → verify → complete
      const createRes: any = await inventoryAPI.createStockIn({
        warehouse_id: adjustForm.value.warehouse_id,
        operator_id: defaultOperatorId.value,
        notes: adjustForm.value.notes || `手动调整: ${adjustingProduct.value.name} +${adjustForm.value.quantity}`,
        items: [{
          product_id: adjustingProduct.value.id,
          expected_quantity: adjustForm.value.quantity,
          actual_quantity: adjustForm.value.quantity,
        }],
      })
      const created = createRes?.data || createRes
      const item = created?.items?.[0]
      if (item) {
        await inventoryAPI.verifyStockIn(created.id, {
          items: [{ item_id: item.id, actual_quantity: adjustForm.value.quantity }],
        })
        await inventoryAPI.completeStockIn(created.id)
      }
      message.success(`${adjustingProduct.value.name} 入库 +${adjustForm.value.quantity}`)
    } else {
      // Stock-out flow: create (auto-deducts inventory)
      await inventoryAPI.createStockOut({
        warehouse_id: adjustForm.value.warehouse_id,
        operator_id: defaultOperatorId.value,
        notes: adjustForm.value.notes || `手动调整: ${adjustingProduct.value.name} -${adjustForm.value.quantity}`,
        items: [{
          product_id: adjustingProduct.value.id,
          quantity: adjustForm.value.quantity,
        }],
      })
      message.success(`${adjustingProduct.value.name} 出库 -${adjustForm.value.quantity}`)
    }
    adjustModal.value = false
    adjustingProduct.value = null
    load()
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || '操作失败'
    message.error(msg)
  } finally { adjustSubmitting.value = false }
}

const handleCreateIssue = async () => {
  if (!issueForm.value.description || !issueForm.value.related_id) { message.warning('请填写描述和关联商品'); return }
  if (!issueForm.value.reported_by) { message.warning('没有可用的报告人'); return }
  try { await inventoryAPI.createIssue(issueForm.value); message.success('已登记'); issueModal.value = false; load() } catch { message.error('操作失败') }
}

const resolveModal = ref(false)
const resolveId = ref('')
const resolveText = ref('')
const resolveSubmitting = ref(false)

const openResolve = (id: string) => {
  resolveId.value = id
  resolveText.value = ''
  resolveModal.value = true
}

const handleResolve = async () => {
  if (!resolveText.value.trim()) { message.warning('请输入解决方案'); return }
  resolveSubmitting.value = true
  try {
    await inventoryAPI.resolveIssue(resolveId.value, { resolution: resolveText.value.trim() })
    message.success('已解决')
    resolveModal.value = false
    load()
  } catch { message.error('操作失败') } finally { resolveSubmitting.value = false }
}

const productCols = [
  { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 130,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: 500 } }, text) },
  { title: '商品名称', dataIndex: 'name', key: 'name',
    customRender: ({ text }: any) => h('span', { style: { fontWeight: 500 } }, text) },
  { title: '库存', dataIndex: 'quantity', key: 'qty', width: 120,
    customRender: ({ text }: any) => {
      const c = text < 50 ? 'var(--danger)' : text < 200 ? 'var(--warning)' : 'var(--success)'
      return h('span', { style: { color: c, fontWeight: 600, fontFamily: 'ui-monospace, monospace' } }, `${text} ${text < 50 ? '⚠' : ''}`)
    }},
  { title: '单价', dataIndex: 'original_price', key: 'price', width: 120,
    customRender: ({ text }: any) => h('span', { style: { color: '#f59e0b', fontFamily: 'ui-monospace, monospace', fontSize: '13px' } }, `¥${Number(text).toFixed(2)}`) },
  { title: '分类', dataIndex: 'category', key: 'cat', width: 110,
    customRender: ({ text }: any) => text ? h(Tag, {}, () => text) : h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '操作', key: 'action', width: 120,
    customRender: ({ record }: any) =>
      h(Button, { type: 'link', size: 'small', onClick: () => openAdjust(record) }, () => [h(EditOutlined), ' 调整']) },
]

const issueCols = [
  { title: '问题描述', dataIndex: 'description', key: 'desc', ellipsis: true,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--text-primary)' } }, text) },
  { title: '类型', dataIndex: 'related_type', key: 'type', width: 100,
    customRender: ({ text }: any) => h(Tag, {}, () => text) },
  { title: '严重程度', dataIndex: 'severity', key: 'sev', width: 110,
    customRender: ({ text }: any) => h(Tag, { color: severityColor[text] || 'default' }, () => severityLabel[text] || text) },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100,
    customRender: ({ text }: any) => { const c = text === 'open' ? 'red' : text === 'in_progress' ? 'blue' : 'green'; return h(Tag, { color: c }, () => text) }},
  { title: '操作', key: 'action', width: 100,
    customRender: ({ record }: any) => record.status !== 'resolved' && record.status !== 'closed' ? h(Button, { type: 'link', size: 'small', onClick: () => openResolve(record.id) }, () => [h(CheckCircleOutlined), ' 解决']) : h('span', { style: { color: 'var(--success)', fontSize: '12px' } }, '已解决') },
]

const siCols = [
  { title: '入库单号', dataIndex: 'stock_in_no', key: 'no', width: 190,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '12px' } }, text) },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110,
    customRender: ({ text }: any) => h(Tag, { color: text === 'completed' ? 'green' : text === 'verified' ? 'blue' : 'default' }, () => text) },
  { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true,
    customRender: ({ text }: any) => text || h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '时间', dataIndex: 'created_at', key: 'time', width: 130,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleDateString('zh-CN')) },
]

const soCols = [
  { title: '出库单号', dataIndex: 'stock_out_no', key: 'no', width: 190,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '12px' } }, text) },
  { title: '车辆信息', dataIndex: 'vehicle_info', key: 'vehicle', width: 170,
    customRender: ({ text }: any) => text || h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110,
    customRender: ({ text }: any) => h(Tag, { color: text === 'delivered' ? 'green' : text === 'shipped' ? 'blue' : 'default' }, () => text) },
  { title: '时间', dataIndex: 'created_at', key: 'time', width: 130,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleDateString('zh-CN')) },
]
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">库存管理</h2>
      <p>入库 · 出库 · 盘点 · 问题追踪</p>
    </div>
    <Spin :spinning="loading">
      <div class="glass-card p-6">
        <Tabs v-model:activeKey="activeTab">
          <a-tab-pane key="stock" :tab="`库存 (${products.length})`">
            <Table :columns="productCols" :dataSource="products" rowKey="id" size="middle" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
          <a-tab-pane key="stock-in" :tab="`入库 (${stockIn.length})`">
            <Table :columns="siCols" :dataSource="stockIn" rowKey="id" size="middle" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
          <a-tab-pane key="stock-out" :tab="`出库 (${stockOut.length})`">
            <Table :columns="soCols" :dataSource="stockOut" rowKey="id" size="middle" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
          <a-tab-pane key="issues" :tab="`问题 (${issues.length})`">
            <div class="mb-3"><Button type="primary" @click="() => { issueForm.related_id = products[0]?.id || ''; issueForm.reported_by = defaultOperatorId; issueModal = true }"><PlusOutlined /> 登记问题</Button></div>
            <Table :columns="issueCols" :dataSource="issues" rowKey="id" size="middle" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
        </Tabs>
      </div>
    </Spin>

    <!-- 库存调整 Modal -->
    <Modal v-model:open="adjustModal" title="库存调整" @ok="handleAdjust" :confirmLoading="adjustSubmitting" okText="确认调整" cancelText="取消" :width="480">
      <div v-if="adjustingProduct" class="space-y-3 py-2">
        <div class="flex items-center gap-3 p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <div class="stat-icon-circle" :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">
            <EditOutlined />
          </div>
          <div>
            <p class="font-semibold" :style="{ color: 'var(--text-primary)' }">{{ adjustingProduct.name }}</p>
            <p class="text-xs" :style="{ color: 'var(--text-muted)' }">
              SKU: {{ adjustingProduct.sku }} · 当前库存:
              <span :style="{
                color: adjustingProduct.quantity < 50 ? 'var(--danger)' : adjustingProduct.quantity < 200 ? 'var(--warning)' : 'var(--success)',
                fontWeight: 600,
              }">{{ adjustingProduct.quantity }}</span>
            </p>
          </div>
        </div>

        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">仓库 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <Select v-model:value="adjustForm.warehouse_id" class="w-full" placeholder="选择仓库"
            :options="warehouses.map((w: any) => ({ value: w.id, label: w.name + (w.location ? ` (${w.location})` : '') }))" />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">调整类型</label>
            <Select v-model:value="adjustForm.type" class="w-full"
              :options="[{ value: 'in', label: '入库 (+)', color: 'green' }, { value: 'out', label: '出库 (−)', color: 'red' }]" />
          </div>
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">数量</label>
            <InputNumber v-model:value="adjustForm.quantity" class="w-full" :min="1" :max="adjustForm.type === 'out' ? adjustingProduct.quantity : 99999" />
          </div>
        </div>

        <div v-if="adjustForm.type === 'out'" class="text-xs px-3 py-2 rounded-lg flex items-center gap-2"
          :style="{ background: 'rgba(225,112,85,0.08)', color: 'var(--danger)' }">
          出库后将直接从库存中扣减 {{ adjustForm.quantity }} 件
        </div>
        <div v-else class="text-xs px-3 py-2 rounded-lg flex items-center gap-2"
          :style="{ background: 'rgba(0,184,148,0.08)', color: 'var(--success)' }">
          入库后将增加 {{ adjustForm.quantity }} 件，调整后库存: {{ adjustingProduct.quantity + adjustForm.quantity }}
        </div>

        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label>
          <Input.TextArea v-model:value="adjustForm.notes" :rows="2" placeholder="调整原因..." />
        </div>
      </div>
    </Modal>

    <!-- 登记问题 Modal -->
    <Modal v-model:open="issueModal" title="登记问题" @ok="handleCreateIssue" okText="提交" cancelText="取消" :width="480">
      <div class="space-y-3 py-2">
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">关联类型</label><Select v-model:value="issueForm.related_type" class="w-full" :options="[{value:'product',label:'商品'},{value:'stock_in',label:'入库单'},{value:'stock_out',label:'出库单'},{value:'order',label:'订单'}]" /></div>
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">严重程度</label><Select v-model:value="issueForm.severity" class="w-full" :options="[{value:'low',label:'低'},{value:'medium',label:'中'},{value:'high',label:'高'},{value:'critical',label:'严重'}]" /></div>
        </div>
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">关联商品</label><Select v-model:value="issueForm.related_id" class="w-full" showSearch :options="products.map((p:any)=>({value:p.id,label:`${p.name} (${p.sku})`}))" /></div>
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">问题描述</label><Input.TextArea v-model:value="issueForm.description" :rows="3" placeholder="描述问题..." /></div>
      </div>
    </Modal>

    <!-- 解决问题 Modal -->
    <Modal v-model:open="resolveModal" title="解决问题" @ok="handleResolve" :confirmLoading="resolveSubmitting" okText="确认解决" cancelText="取消" :width="480">
      <div class="py-2">
        <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">解决方案</label>
        <Input.TextArea v-model:value="resolveText" :rows="4" placeholder="请描述解决方案..." />
      </div>
    </Modal>
  </div>
</template>
