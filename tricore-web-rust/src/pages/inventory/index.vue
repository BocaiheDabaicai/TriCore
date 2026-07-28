<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { Table, Tag, Button, Modal, Input, InputNumber, Select, message, Spin, Tabs, Space } from 'ant-design-vue'
import { PlusOutlined, CheckCircleOutlined, EditOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons-vue'
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
const adjustSubmitting = ref(false)
const activeTab = ref('stock')

const severityColor: Record<string, string> = { critical: 'magenta', high: 'red', medium: 'orange', low: 'green' }
const severityLabel: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }

const defaultOperatorId = computed(() => employees.value[0]?.id || '')

// ── Adjust modal state (per-warehouse) ──
type WarehouseAdjustEntry = { warehouse_id: string; warehouse_name: string; current: number; target: number }
const adjustEntries = ref<WarehouseAdjustEntry[]>([])
const adjustNotes = ref('')
const warehouseInventory = ref<any[]>([])

const calcDelta = (entry: WarehouseAdjustEntry) => entry.target - entry.current
const deltaLabel = (entry: WarehouseAdjustEntry) => {
  const d = calcDelta(entry)
  if (d > 0) return { text: `入库 +${d}`, color: '#00b894' }
  if (d < 0) return { text: `出库 ${d}`, color: '#e17055' }
  return { text: '不变', color: 'var(--text-muted)' }
}

const load = async () => {
  loading.value = true
  try {
    const [p, si, so, iss, wh, emp]: any[] = await Promise.all([
      inventoryAPI.listProducts(),
      inventoryAPI.listStockIn({ per_page: 100 }),
      inventoryAPI.listStockOut({ per_page: 100 }),
      inventoryAPI.listIssues({ per_page: 100 }),
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

const productMap = computed(() => {
  const m = new Map<string, any>(); for (const p of products.value) m.set(p.id, p); return m
})
const warehouseMap = computed(() => {
  const m = new Map<string, any>(); for (const w of warehouses.value) m.set(w.id, w); return m
})

// ── Adjust modal ──
const openAdjust = async (product: any) => {
  adjustingProduct.value = product
  adjustNotes.value = ''
  try {
    const res: any = await inventoryAPI.getWarehouseInventory(product.id)
    warehouseInventory.value = res?.data || []
  } catch { warehouseInventory.value = [] }

  // Build entries from warehouse_inventory
  const existing = new Map<string, number>()
  for (const wi of warehouseInventory.value) {
    existing.set(wi.warehouse_id || wi.inv?.warehouse_id, wi.quantity ?? wi.inv?.quantity ?? 0)
  }

  const usedIds = new Set<string>()
  adjustEntries.value = warehouseInventory.value.map((wi: any) => {
    const wid = wi.warehouse_id || wi.inv?.warehouse_id
    usedIds.add(wid)
    return {
      warehouse_id: wid,
      warehouse_name: wi.warehouse_name || warehouseMap.value.get(wid)?.name || '未知仓库',
      current: wi.quantity ?? wi.inv?.quantity ?? 0,
      target: wi.quantity ?? wi.inv?.quantity ?? 0,
    }
  })
  adjustModal.value = true
}

const addAdjustEntry = () => {
  const used = new Set(adjustEntries.value.map(e => e.warehouse_id))
  if (used.size >= warehouses.value.length) { message.warning('没有更多可用仓库'); return }
  adjustEntries.value.push({
    warehouse_id: '',
    warehouse_name: '',
    current: 0,
    target: 0,
  })
}

const onAdjustWarehouseSelect = (i: number, wid: string) => {
  const w = warehouseMap.value.get(wid)
  if (!w) return
  const entry = adjustEntries.value[i]
  // Check for duplicate selection
  const dup = adjustEntries.value.findIndex((e, idx) => idx !== i && e.warehouse_id === wid)
  if (dup !== -1) { message.warning('该仓库已存在'); adjustEntries.value[i].warehouse_id = ''; return }
  entry.warehouse_id = wid
  entry.warehouse_name = w.name
  // Look up current stock from warehouse_inventory data
  const existing = warehouseInventory.value.find((wi: any) => (wi.warehouse_id || wi.inv?.warehouse_id) === wid)
  entry.current = existing ? (existing.quantity ?? existing.inv?.quantity ?? 0) : 0
  entry.target = entry.current
}

const warehouseOptions = computed(() =>
  warehouses.value.map((w: any) => ({ value: w.id, label: `${w.name}${w.location ? ` (${w.location})` : ''}` }))
)

const removeAdjustEntry = (i: number) => {
  if (adjustEntries.value.length <= 1) { message.warning('至少保留一个仓库项'); return }
  adjustEntries.value.splice(i, 1)
}

const handleAdjust = async () => {
  if (!adjustingProduct.value) return
  if (!defaultOperatorId.value) { message.warning('没有可用的操作员'); return }

  adjustSubmitting.value = true
  try {
    const adjustments = adjustEntries.value
      .filter(e => e.target !== e.current)
      .map(e => ({ warehouse_id: e.warehouse_id, quantity: e.target }))

    if (adjustments.length === 0) {
      message.info('没有需要调整的仓库')
      adjustSubmitting.value = false
      return
    }

    const res: any = await inventoryAPI.adjustInventory({
      product_id: adjustingProduct.value.id,
      operator_id: defaultOperatorId.value,
      notes: adjustNotes.value || undefined,
      adjustments,
    })
    const data = res?.data || res
    message.success(data?.message || '调整完成')
    adjustModal.value = false
    adjustingProduct.value = null
    load()
  } catch (err: any) {
    message.error(err?.response?.data?.message || err?.message || '操作失败')
  } finally { adjustSubmitting.value = false }
}

// ── Issue ──
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
    message.success('已解决'); resolveModal.value = false; load()
  } catch { message.error('操作失败') } finally { resolveSubmitting.value = false }
}

// ── Detail modals ──
const siDetail = ref(false)
const siDetailData = ref<any>(null)
const siDetailLoading = ref(false)
const openSiDetail = async (id: string) => {
  siDetailLoading.value = true; siDetail.value = true
  try { const res: any = await inventoryAPI.getStockIn(id); siDetailData.value = res?.data || res } catch { message.error('加载失败') } finally { siDetailLoading.value = false }
}

const soDetail = ref(false)
const soDetailData = ref<any>(null)
const soDetailLoading = ref(false)
const openSoDetail = async (id: string) => {
  soDetailLoading.value = true; soDetail.value = true
  try { const res: any = await inventoryAPI.getStockOut(id); soDetailData.value = res?.data || res } catch { message.error('加载失败') } finally { soDetailLoading.value = false }
}

const statusLabel: Record<string, string> = { pending: '待处理', verified: '已盘点', completed: '已完成', shipped: '已发货', delivered: '已送达' }
const statusColor: Record<string, string> = { pending: 'default', verified: 'blue', completed: 'green', shipped: 'blue', delivered: 'green' }

// ── Table columns ──
const productCols = [
  { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 130,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: 500 } }, text) },
  { title: '商品名称', dataIndex: 'name', key: 'name',
    customRender: ({ text }: any) => h('span', { style: { fontWeight: 500 } }, text) },
  { title: '总库存', dataIndex: 'quantity', key: 'qty', width: 120,
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

const siCols = [
  { title: '入库单号', dataIndex: 'stock_in_no', key: 'no', width: 200,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '12px' } }, text) },
  { title: '仓库', key: 'warehouse', width: 120,
    customRender: ({ record }: any) => h('span', { style: { color: 'var(--text-primary)' } }, warehouseMap.value.get(record.warehouse_id)?.name || '—') },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110,
    customRender: ({ text }: any) => h(Tag, { color: statusColor[text] || 'default' }, () => statusLabel[text] || text) },
  { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true,
    customRender: ({ text }: any) => text || h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '时间', dataIndex: 'created_at', key: 'time', width: 130,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleDateString('zh-CN')) },
  { title: '操作', key: 'action', width: 90,
    customRender: ({ record }: any) =>
      h(Button, { type: 'link', size: 'small', onClick: () => openSiDetail(record.id) }, () => [h(EyeOutlined), ' 详情']) },
]

const soCols = [
  { title: '出库单号', dataIndex: 'stock_out_no', key: 'no', width: 200,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '12px' } }, text) },
  { title: '仓库', key: 'warehouse', width: 120,
    customRender: ({ record }: any) => h('span', { style: { color: 'var(--text-primary)' } }, warehouseMap.value.get(record.warehouse_id)?.name || '—') },
  { title: '车辆信息', dataIndex: 'vehicle_info', key: 'vehicle', width: 140,
    customRender: ({ text }: any) => text || h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110,
    customRender: ({ text }: any) => h(Tag, { color: statusColor[text] || 'default' }, () => statusLabel[text] || text) },
  { title: '时间', dataIndex: 'created_at', key: 'time', width: 130,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleDateString('zh-CN')) },
  { title: '操作', key: 'action', width: 90,
    customRender: ({ record }: any) =>
      h(Button, { type: 'link', size: 'small', onClick: () => openSoDetail(record.id) }, () => [h(EyeOutlined), ' 详情']) },
]

const issueCols = [
  { title: '问题描述', dataIndex: 'description', key: 'desc', ellipsis: true,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--text-primary)' } }, text) },
  { title: '类型', dataIndex: 'related_type', key: 'type', width: 100,
    customRender: ({ text }: any) => h(Tag, {}, () => text) },
  { title: '严重程度', dataIndex: 'severity', key: 'sev', width: 110,
    customRender: ({ text }: any) => h(Tag, { color: severityColor[text] || 'default' }, () => severityLabel[text] || text) },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110,
    customRender: ({ text }: any) => { const c = text === 'open' ? 'red' : text === 'in_progress' ? 'blue' : 'green'; return h(Tag, { color: c }, () => text) }},
  { title: '操作', key: 'action', width: 110,
    customRender: ({ record }: any) => record.status !== 'resolved' && record.status !== 'closed' ? h(Button, { type: 'link', size: 'small', onClick: () => openResolve(record.id) }, () => [h(CheckCircleOutlined), ' 解决']) : h('span', { style: { color: 'var(--success)', fontSize: '12px' } }, '已解决') },
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

    <!-- ═══ 库存调整 Modal ═══ -->
    <Modal v-model:open="adjustModal" title="库存调整" @ok="handleAdjust" :confirmLoading="adjustSubmitting" okText="确认调整" cancelText="取消" :width="720">
      <div v-if="adjustingProduct" class="space-y-4 py-2">
        <!-- Product info -->
        <div class="flex items-center gap-3 p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <div class="stat-icon-circle" :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">
            <EditOutlined />
          </div>
          <div>
            <p class="font-semibold" :style="{ color: 'var(--text-primary)' }">{{ adjustingProduct.name }}</p>
            <p class="text-xs" :style="{ color: 'var(--text-muted)' }">
              SKU: {{ adjustingProduct.sku }} · 总库存:
              <span :style="{
                color: adjustingProduct.quantity < 50 ? 'var(--danger)' : adjustingProduct.quantity < 200 ? 'var(--warning)' : 'var(--success)',
                fontWeight: 600,
              }">{{ adjustingProduct.quantity }}</span>
            </p>
          </div>
        </div>

        <!-- Warehouse adjust entries -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-medium" :style="{ color: 'var(--text-secondary)' }">仓库库存调整</label>
            <Button type="link" size="small" @click="addAdjustEntry"><PlusOutlined /> 添加仓库</Button>
          </div>
          <div class="space-y-2">
            <div v-for="(entry, i) in adjustEntries" :key="i"
              class="flex items-center gap-2 p-2.5 rounded-lg" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
              <span class="text-xs font-bold flex-shrink-0 min-w-5" :style="{ color: 'var(--text-muted)' }">#{{ i + 1 }}</span>
              <Select v-model:value="entry.warehouse_id" class="flex-1" placeholder="选择仓库"
                :options="warehouseOptions"
                @change="(v: string) => onAdjustWarehouseSelect(i, v)" />
              <div class="flex items-center gap-2 flex-shrink-0">
                <span class="text-xs" :style="{ color: 'var(--text-muted)' }">当前:</span>
                <span class="text-sm font-mono font-semibold" :style="{ color: 'var(--text-primary)', minWidth: '40px', textAlign: 'right' }">{{ entry.current }}</span>
              </div>
              <span class="text-xs flex-shrink-0" :style="{ color: 'var(--text-muted)' }">→</span>
              <InputNumber v-model:value="entry.target" class="flex-shrink-0" style="width:100px" :min="0" />
              <Tag :color="calcDelta(entry) > 0 ? 'green' : calcDelta(entry) < 0 ? 'red' : 'default'"
                class="flex-shrink-0" style="min-width:70px;text-align:center">
                {{ deltaLabel(entry).text }}
              </Tag>
              <Button type="text" size="small" danger @click="removeAdjustEntry(i)"><DeleteOutlined /></Button>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注 <span class="text-xs" style="color:var(--text-muted)">（将关联到生成的入库/出库单）</span></label>
          <Input.TextArea v-model:value="adjustNotes" :rows="3" placeholder="调整原因、备注信息..." />
        </div>

        <!-- Summary -->
        <div v-if="adjustEntries.some(e => e.target !== e.current)" class="p-3 rounded-lg text-xs space-y-1" :style="{ background: 'var(--input-bg)' }">
          <div v-for="(entry, i) in adjustEntries.filter(e => e.target !== e.current)" :key="'s'+i"
            :style="{ color: calcDelta(entry) > 0 ? 'var(--success)' : 'var(--danger)' }">
            {{ entry.warehouse_name }}: {{ entry.current }} → {{ entry.target }}
            ({{ calcDelta(entry) > 0 ? '+' : '' }}{{ calcDelta(entry) }})
            → {{ calcDelta(entry) > 0 ? '生成入库单' : '生成出库单' }}
          </div>
        </div>
      </div>
    </Modal>

    <!-- ═══ 入库详情 Modal ═══ -->
    <Modal v-model:open="siDetail" :footer="null" :width="680" @cancel="siDetailData = null">
      <template #title>
        <div class="flex items-center gap-2">
          <span :style="{ color: 'var(--accent)' }">📦</span>
          <span>入库详情 — {{ siDetailData?.stock_in_no || '' }}</span>
        </div>
      </template>
      <Spin :spinning="siDetailLoading">
        <div v-if="siDetailData" class="space-y-4 py-1">
          <div class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div class="flex gap-2"><span :style="{ color: 'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">单号</span><span :style="{ color: 'var(--accent)', fontFamily:'ui-monospace,monospace', fontSize:'12px' }">{{ siDetailData.stock_in_no }}</span></div>
            <div class="flex gap-2"><span :style="{ color: 'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">状态</span><Tag :color="statusColor[siDetailData.status]">{{ statusLabel[siDetailData.status] || siDetailData.status }}</Tag></div>
            <div class="flex gap-2"><span :style="{ color: 'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">仓库</span><span :style="{ color:'var(--text-primary)', fontWeight:500 }">{{ warehouseMap.get(siDetailData.warehouse_id)?.name || '—' }}</span></div>
            <div class="flex gap-2"><span :style="{ color: 'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">时间</span><span :style="{ color:'var(--text-primary)', fontSize:'13px' }">{{ new Date(siDetailData.created_at).toLocaleString('zh-CN') }}</span></div>
          </div>
          <div v-if="siDetailData.notes" class="p-3 rounded-lg" :style="{ background:'var(--input-bg)' }">
            <p class="text-xs mb-1 font-medium" :style="{ color:'var(--text-muted)' }">备注</p>
            <p class="text-sm" :style="{ color:'var(--text-secondary)' }">{{ siDetailData.notes }}</p>
          </div>
          <div v-if="siDetailData.items?.length">
            <p class="text-xs font-semibold mb-2" :style="{ color:'var(--text-secondary)' }">入库商品</p>
            <div class="rounded-lg overflow-hidden border" :style="{ borderColor:'var(--border-subtle)' }">
              <div class="grid grid-cols-4 gap-2 px-4 py-2 text-xs font-medium" :style="{ background:'var(--input-bg)', color:'var(--text-muted)' }">
                <span>商品</span><span class="text-center">预期数量</span><span class="text-center">实际数量</span><span class="text-right">单价</span>
              </div>
              <div v-for="(item, i) in siDetailData.items" :key="i" class="grid grid-cols-4 gap-2 px-4 py-2.5 text-sm"
                :style="{ background: i%2===0 ? 'transparent' : 'var(--input-bg)' }">
                <span :style="{ color:'var(--text-primary)', fontWeight:500 }">{{ productMap.get(item.product_id)?.name || item.product_id?.slice(0,8) }}</span>
                <span class="text-center" :style="{ color:'var(--text-primary)', fontFamily:'ui-monospace,monospace' }">{{ item.expected_quantity }}</span>
                <span class="text-center" :style="{ color:'var(--accent)', fontFamily:'ui-monospace,monospace', fontWeight:600 }">{{ item.actual_quantity }}</span>
                <span class="text-right" :style="{ color:'var(--text-secondary)', fontFamily:'ui-monospace,monospace' }">{{ item.unit_price ? '¥'+Number(item.unit_price).toFixed(2) : '—' }}</span>
              </div>
            </div>
          </div>
        </div>
      </Spin>
    </Modal>

    <!-- ═══ 出库详情 Modal ═══ -->
    <Modal v-model:open="soDetail" :footer="null" :width="680" @cancel="soDetailData = null">
      <template #title>
        <div class="flex items-center gap-2">
          <span :style="{ color: 'var(--warning)' }">🚚</span>
          <span>出库详情 — {{ soDetailData?.stock_out_no || '' }}</span>
        </div>
      </template>
      <Spin :spinning="soDetailLoading">
        <div v-if="soDetailData" class="space-y-4 py-1">
          <div class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div class="flex gap-2"><span :style="{ color:'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">单号</span><span :style="{ color:'var(--accent)', fontFamily:'ui-monospace,monospace', fontSize:'12px' }">{{ soDetailData.stock_out_no }}</span></div>
            <div class="flex gap-2"><span :style="{ color:'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">状态</span><Tag :color="statusColor[soDetailData.status]">{{ statusLabel[soDetailData.status] || soDetailData.status }}</Tag></div>
            <div class="flex gap-2"><span :style="{ color:'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">仓库</span><span :style="{ color:'var(--text-primary)', fontWeight:500 }">{{ warehouseMap.get(soDetailData.warehouse_id)?.name || '—' }}</span></div>
            <div class="flex gap-2"><span :style="{ color:'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">时间</span><span :style="{ color:'var(--text-primary)', fontSize:'13px' }">{{ new Date(soDetailData.created_at).toLocaleString('zh-CN') }}</span></div>
            <div v-if="soDetailData.vehicle_info" class="flex gap-2"><span :style="{ color:'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">车辆</span><span :style="{ color:'var(--text-primary)', fontSize:'13px' }">{{ soDetailData.vehicle_info }}</span></div>
            <div v-if="soDetailData.driver_info" class="flex gap-2"><span :style="{ color:'var(--text-muted)', fontSize:'12px', minWidth:'48px' }">司机</span><span :style="{ color:'var(--text-primary)', fontSize:'13px' }">{{ soDetailData.driver_info }}</span></div>
          </div>
          <div v-if="soDetailData.notes" class="p-3 rounded-lg" :style="{ background:'var(--input-bg)' }">
            <p class="text-xs mb-1 font-medium" :style="{ color:'var(--text-muted)' }">备注</p>
            <p class="text-sm" :style="{ color:'var(--text-secondary)' }">{{ soDetailData.notes }}</p>
          </div>
          <div v-if="soDetailData.items?.length">
            <p class="text-xs font-semibold mb-2" :style="{ color:'var(--text-secondary)' }">出库商品</p>
            <div class="rounded-lg overflow-hidden border" :style="{ borderColor:'var(--border-subtle)' }">
              <div class="grid grid-cols-3 gap-2 px-4 py-2 text-xs font-medium" :style="{ background:'var(--input-bg)', color:'var(--text-muted)' }">
                <span>商品</span><span class="text-center">数量</span><span class="text-right">单价</span>
              </div>
              <div v-for="(item, i) in soDetailData.items" :key="i" class="grid grid-cols-3 gap-2 px-4 py-2.5 text-sm"
                :style="{ background: i%2===0 ? 'transparent' : 'var(--input-bg)' }">
                <span :style="{ color:'var(--text-primary)', fontWeight:500 }">{{ productMap.get(item.product_id)?.name || item.product_id?.slice(0,8) }}</span>
                <span class="text-center" :style="{ color:'var(--danger)', fontFamily:'ui-monospace,monospace', fontWeight:600 }">{{ item.quantity }}</span>
                <span class="text-right" :style="{ color:'var(--text-secondary)', fontFamily:'ui-monospace,monospace' }">{{ item.unit_price ? '¥'+Number(item.unit_price).toFixed(2) : '—' }}</span>
              </div>
            </div>
          </div>
        </div>
      </Spin>
    </Modal>

    <!-- ═══ 登记问题 Modal ═══ -->
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

    <!-- ═══ 解决问题 Modal ═══ -->
    <Modal v-model:open="resolveModal" title="解决问题" @ok="handleResolve" :confirmLoading="resolveSubmitting" okText="确认解决" cancelText="取消" :width="480">
      <div class="py-2">
        <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">解决方案</label>
        <Input.TextArea v-model:value="resolveText" :rows="4" placeholder="请描述解决方案..." />
      </div>
    </Modal>
  </div>
</template>
