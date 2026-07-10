<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { Table, Tag, Button, Modal, Input, InputNumber, Select, message, Spin, Tabs, Space } from 'ant-design-vue'
import { PlusOutlined, EyeOutlined, DeleteOutlined, ShoppingCartOutlined } from '@ant-design/icons-vue'
import { salesAPI } from '@/services/api'

const loading = ref(true)
const products = ref<any[]>([])
const orders = ref<any[]>([])
const users = ref<any[]>([])
const activeTab = ref('orders')

// ── Product form ──
const modalOpen = ref(false)
const editing = ref<any>(null)
const form = ref({ sku: '', name: '', original_price: 0, category: '', description: '' })
const categories = ['电子产品', '日用品', '食品', '服装', '办公用品', '医疗', '运动']

// ── Order create / edit ──
const orderModal = ref(false)
const editOrderModal = ref(false)
const editingOrder = ref<any>(null)
const orderItems = ref<{ product_id: string; quantity: number; unit_price: number }[]>([])
const orderForm = ref({ customer_id: '', notes: '', discount_amount: 0, vehicle_info: '', driver_info: '' })
const orderSaving = ref(false)

// ── Order detail ──
const detailModal = ref(false)
const selectedOrder = ref<any>(null)

// ── Status change ──
const statusModal = ref(false)
const statusForm = ref({ status: '', vehicle_info: '', driver_info: '' })

const statusColors: Record<string, string> = { pending: 'default', confirmed: 'blue', processing: 'purple', shipped: 'cyan', delivered: 'green', cancelled: 'red' }
const statusLabels: Record<string, string> = { pending: '待处理', confirmed: '已确认', processing: '处理中', shipped: '已发货', delivered: '已交付', cancelled: '已取消' }
const nextStatus: Record<string, string[]> = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['processing', 'cancelled'],
  processing: ['shipped'],
  shipped: ['delivered'],
}

const productMap = computed(() => {
  const m = new Map<string, any>(); for (const p of products.value) m.set(p.id, p); return m
})
const userMap = computed(() => {
  const m = new Map<string, any>(); for (const u of users.value) m.set(u.id, u); return m
})
const customerOptions = computed(() =>
  users.value.filter((u: any) => u.role === 'customer').map((u: any) => ({ value: u.id, label: `${u.full_name} (${u.username})` }))
)
const productOptions = computed(() =>
  products.value.map((p: any) => ({ value: p.id, label: `${p.name} (${p.sku}) — ¥${Number(p.original_price).toFixed(2)} · 库存: ${p.quantity}` }))
)

const orderTotal = computed(() =>
  orderItems.value.reduce((sum, i) => sum + i.unit_price * i.quantity, 0)
)
const orderFinal = computed(() =>
  Math.max(0, orderTotal.value - (orderForm.value.discount_amount || 0))
)

const load = async () => {
  loading.value = true
  try {
    const [p, o, u]: any[] = await Promise.all([
      salesAPI.listProducts({ per_page: 200 }),
      salesAPI.listOrders({ per_page: 100 }),
      salesAPI.listUsers({ per_page: 200 }).catch(() => ({ data: [] })),
    ])
    products.value = p?.data?.data || p?.data || []
    orders.value = o?.data?.data || o?.data || []
    users.value = u?.data?.data || u?.data || []
  } catch { message.error('加载失败') } finally { loading.value = false }
}
onMounted(load)

// ── Product CRUD ──
const handleSave = async () => {
  if (!form.value.name || !form.value.sku) { message.warning('请填写名称和SKU'); return }
  try {
    if (editing.value) { await salesAPI.updateProduct(editing.value.id, form.value); message.success('已更新') }
    else { await salesAPI.createProduct(form.value); message.success('已创建') }
    modalOpen.value = false; editing.value = null
    form.value = { sku: '', name: '', original_price: 0, category: '', description: '' }
    load()
  } catch { message.error('操作失败') }
}

// ── Order item management ──
const addOrderItem = () => orderItems.value.push({ product_id: '', quantity: 1, unit_price: 0 })
const removeOrderItem = (i: number) => {
  if (orderItems.value.length <= 1) { message.warning('至少需要一个商品'); return }
  orderItems.value.splice(i, 1)
}
const onProductSelect = (i: number, pid: string) => {
  const p = productMap.value.get(pid)
  if (p) orderItems.value[i].unit_price = Number(p.original_price)
}

const openOrderCreate = () => {
  editingOrder.value = null
  orderForm.value = { customer_id: '', notes: '', discount_amount: 0, vehicle_info: '', driver_info: '' }
  orderItems.value = [{ product_id: '', quantity: 1, unit_price: 0 }]
  orderModal.value = true
}

const openOrderEdit = (record: any) => {
  editingOrder.value = record
  orderForm.value = {
    customer_id: record.customer_id, notes: record.notes || '', discount_amount: Number(record.discount_amount),
    vehicle_info: record.vehicle_info || '', driver_info: record.driver_info || '',
  }
  orderItems.value = (record.items || []).map((i: any) => ({ product_id: i.product_id, quantity: i.quantity, unit_price: Number(i.unit_price) }))
  if (orderItems.value.length === 0) orderItems.value = [{ product_id: '', quantity: 1, unit_price: 0 }]
  editOrderModal.value = true
}

const handleCreateOrder = async () => {
  if (!orderForm.value.customer_id) { message.warning('请选择客户'); return }
  if (orderItems.value.some((i) => !i.product_id)) { message.warning('请选择所有商品'); return }
  orderSaving.value = true
  try {
    await salesAPI.createOrder({
      customer_id: orderForm.value.customer_id,
      notes: orderForm.value.notes || undefined,
      discount_amount: orderForm.value.discount_amount || 0,
      vehicle_info: orderForm.value.vehicle_info || undefined,
      driver_info: orderForm.value.driver_info || undefined,
      items: orderItems.value.map((i) => ({ product_id: i.product_id, quantity: i.quantity, unit_price: i.unit_price })),
    })
    message.success('订单已创建')
    orderModal.value = false
    load()
  } catch (err: any) { message.error(err?.response?.data?.message || '创建失败') } finally { orderSaving.value = false }
}

const handleUpdateOrder = async () => {
  if (orderItems.value.some((i) => !i.product_id)) { message.warning('请选择所有商品'); return }
  orderSaving.value = true
  try {
    await salesAPI.updateOrder(editingOrder.value.id, {
      notes: orderForm.value.notes || undefined,
      discount_amount: orderForm.value.discount_amount || 0,
      vehicle_info: orderForm.value.vehicle_info || undefined,
      driver_info: orderForm.value.driver_info || undefined,
    })
    message.success('订单已更新')
    editOrderModal.value = false
    load()
  } catch (err: any) { message.error(err?.response?.data?.message || '更新失败') } finally { orderSaving.value = false }
}

// ── Order detail ──
const openOrderDetail = async (id: string) => {
  try { const res: any = await salesAPI.getOrder(id); selectedOrder.value = res?.data || res; detailModal.value = true } catch { message.error('加载失败') }
}

// ── Status change ──
const openStatusChange = (order: any) => {
  selectedOrder.value = order
  statusForm.value = { status: '', vehicle_info: order.vehicle_info || '', driver_info: order.driver_info || '' }
  statusModal.value = true
}

const handleStatusChange = async () => {
  if (!statusForm.value.status) { message.warning('请选择状态'); return }
  try {
    await salesAPI.updateOrderStatus(selectedOrder.value.id, {
      status: statusForm.value.status,
      vehicle_info: statusForm.value.vehicle_info || undefined,
      driver_info: statusForm.value.driver_info || undefined,
    })
    message.success('状态已更新')
    statusModal.value = false
    load()
  } catch { message.error('操作失败') }
}

// ── Table columns ──
const orderCols = [
  { title: '订单号', dataIndex: 'order_no', key: 'no', width: 170,
    customRender: ({ text }: any) => h('span', { style: { fontFamily: 'ui-monospace, monospace', fontSize: '12px', color: 'var(--text-secondary)' } }, text) },
  { title: '客户', key: 'customer', width: 100,
    customRender: ({ record }: any) => {
      const u = userMap.value.get(record.customer_id)
      return h('span', { style: { color: 'var(--text-primary)', fontWeight: 500 } }, u?.full_name || '—')
    }},
  { title: '金额', dataIndex: 'final_amount', key: 'amt', width: 110,
    customRender: ({ text }: any) => h('span', { style: { color: '#f59e0b', fontFamily: 'ui-monospace, monospace', fontWeight: 600 } }, `¥${Number(text).toFixed(2)}`) },
  { title: '状态', dataIndex: 'status', key: 'status', width: 90,
    customRender: ({ text }: any) => h(Tag, { color: statusColors[text] || 'default' }, () => statusLabels[text] || text) },
  { title: '车辆', dataIndex: 'vehicle_info', key: 'vehicle', width: 100, ellipsis: true,
    customRender: ({ text }: any) => text ? h('span', { style: { fontSize: '12px', color: 'var(--text-secondary)' } }, text) : h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '时间', dataIndex: 'created_at', key: 'time', width: 110,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleDateString('zh-CN')) },
  { title: '操作', key: 'action', width: 200,
    customRender: ({ record }: any) => {
      const btns = [h(Button, { type: 'link', size: 'small', onClick: () => openOrderDetail(record.id) }, () => [h(EyeOutlined), ' 详情'])]
      if (record.status === 'pending') {
        btns.push(h(Button, { type: 'link', size: 'small', onClick: async () => {
          try { const res: any = await salesAPI.getOrder(record.id); const data = res?.data || res; openOrderEdit(data) } catch { message.error('加载失败') }
        } }, () => '编辑'))
      }
      const ns = nextStatus[record.status]
      if (ns && ns.length > 0) {
        btns.push(h(Button, { type: 'link', size: 'small', onClick: () => openStatusChange(record) }, () => '变更状态'))
      }
      return h(Space, { size: 4 }, () => btns)
    }},
]

const productCols = [
  { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 110,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: 500 } }, text) },
  { title: '商品名称', dataIndex: 'name', key: 'name',
    customRender: ({ text }: any) => h('span', { style: { fontWeight: 500 } }, text) },
  { title: '价格', dataIndex: 'original_price', key: 'price', width: 100,
    customRender: ({ text }: any) => h('span', { style: { color: '#f59e0b', fontFamily: 'ui-monospace, monospace', fontSize: '13px' } }, `¥${Number(text).toFixed(2)}`) },
  { title: '库存', dataIndex: 'quantity', key: 'qty', width: 80,
    customRender: ({ text }: any) => {
      const c = text < 50 ? 'var(--danger)' : text < 200 ? 'var(--warning)' : 'var(--success)'
      return h('span', { style: { color: c, fontWeight: 600, fontFamily: 'ui-monospace, monospace' } }, String(text))
    }},
  { title: '分类', dataIndex: 'category', key: 'cat', width: 90,
    customRender: ({ text }: any) => text ? h(Tag, {}, () => text) : h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '操作', key: 'action', width: 80,
    customRender: ({ record }: any) =>
      h(Button, { type: 'link', size: 'small', onClick: () => { editing.value = record; form.value = { sku: record.sku, name: record.name, original_price: Number(record.original_price), category: record.category || '', description: record.description || '' }; modalOpen.value = true } }, () => '编辑') },
]
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">销售管理</h2>
      <p>订单管理 · 商品定价 · 捆绑销售 · 退单处理</p>
    </div>
    <Spin :spinning="loading">
      <div class="glass-card p-6">
        <Tabs v-model:activeKey="activeTab">
          <!-- ═══ Orders tab ═══ -->
          <a-tab-pane key="orders" :tab="`订单列表 (${orders.length})`">
            <div class="mb-3"><Button type="primary" @click="openOrderCreate"><PlusOutlined /> 创建订单</Button></div>
            <Table :columns="orderCols" :dataSource="orders" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>

          <!-- ═══ Products tab ═══ -->
          <a-tab-pane key="products" :tab="`商品管理 (${products.length})`">
            <div class="mb-3"><Button type="primary" @click="() => { editing = null; form = { sku: '', name: '', original_price: 0, category: '', description: '' }; modalOpen = true }"><PlusOutlined /> 新增商品</Button></div>
            <Table :columns="productCols" :dataSource="products" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
        </Tabs>
      </div>
    </Spin>

    <!-- ═══ Create Order modal ═══ -->
    <Modal v-model:open="orderModal" title="创建订单" @ok="handleCreateOrder" :confirmLoading="orderSaving" okText="创建订单" cancelText="取消" :width="700">
      <div class="space-y-4 py-2">
        <!-- Header -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">客户 <span :style="{ color: 'var(--danger)' }">*</span></label>
            <Select v-model:value="orderForm.customer_id" class="w-full" placeholder="选择客户" :options="customerOptions" showSearch />
          </div>
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">折扣金额</label>
            <InputNumber v-model:value="orderForm.discount_amount" class="w-full" :min="0" :step="0.01" />
          </div>
        </div>

        <!-- Items -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-medium" :style="{ color: 'var(--text-secondary)' }">订单商品</label>
            <Button type="link" size="small" @click="addOrderItem"><PlusOutlined /> 添加商品</Button>
          </div>
          <div class="space-y-2">
            <div v-for="(item, i) in orderItems" :key="i" class="flex items-center gap-2 p-2 rounded-lg" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
              <span class="text-xs font-bold flex-shrink-0 min-w-5" :style="{ color: 'var(--text-muted)' }">#{{ i + 1 }}</span>
              <Select v-model:value="item.product_id" class="flex-1" placeholder="选择商品" :options="productOptions" showSearch @change="(v: string) => onProductSelect(i, v)" />
              <InputNumber v-model:value="item.quantity" :min="1" :max="999" style="width:80px" placeholder="数量" />
              <InputNumber v-model:value="item.unit_price" :min="0" :step="0.01" style="width:110px" placeholder="单价" />
              <span class="text-xs font-mono flex-shrink-0 min-w-16 text-right" :style="{ color: '#f59e0b', fontWeight: 600 }">¥{{ (item.unit_price * item.quantity).toFixed(2) }}</span>
              <Button type="text" size="small" danger @click="removeOrderItem(i)"><DeleteOutlined /></Button>
            </div>
          </div>
        </div>

        <!-- Summary -->
        <div class="flex justify-end gap-6 text-sm p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <span :style="{ color: 'var(--text-muted)' }">商品总额: <b :style="{ color: 'var(--text-primary)' }">¥{{ orderTotal.toFixed(2) }}</b></span>
          <span v-if="orderForm.discount_amount > 0" :style="{ color: 'var(--text-muted)' }">折扣: <b :style="{ color: 'var(--danger)' }">−¥{{ Number(orderForm.discount_amount).toFixed(2) }}</b></span>
          <span :style="{ color: 'var(--text-muted)' }">实付: <b :style="{ color: 'var(--accent)', fontSize: '16px' }">¥{{ orderFinal.toFixed(2) }}</b></span>
        </div>

        <!-- Vehicle & Notes -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">配送车辆</label>
            <Input v-model:value="orderForm.vehicle_info" placeholder="车牌号 / 车型" />
          </div>
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">司机信息</label>
            <Input v-model:value="orderForm.driver_info" placeholder="司机姓名 / 电话" />
          </div>
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label>
          <Input.TextArea v-model:value="orderForm.notes" :rows="2" placeholder="订单备注..." />
        </div>
      </div>
    </Modal>

    <!-- ═══ Edit Order modal (pending only) ═══ -->
    <Modal v-model:open="editOrderModal" title="编辑订单" @ok="handleUpdateOrder" :confirmLoading="orderSaving" okText="保存" cancelText="取消" :width="700">
      <div class="space-y-4 py-2">
        <div class="flex items-center gap-3 p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <div class="stat-icon-circle" :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">
            <ShoppingCartOutlined />
          </div>
          <div>
            <p class="font-semibold" :style="{ color: 'var(--text-primary)' }">{{ editingOrder?.order_no }}</p>
            <p class="text-xs" :style="{ color: 'var(--text-muted)' }">待处理订单 — 可修改配送信息和备注</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">配送车辆</label>
            <Input v-model:value="orderForm.vehicle_info" placeholder="车牌号 / 车型" />
          </div>
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">司机信息</label>
            <Input v-model:value="orderForm.driver_info" placeholder="司机姓名 / 电话" />
          </div>
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label>
          <Input.TextArea v-model:value="orderForm.notes" :rows="2" placeholder="订单备注..." />
        </div>
      </div>
    </Modal>

    <!-- ═══ Order Detail modal ═══ -->
    <Modal v-model:open="detailModal" :footer="null" :width="720">
      <template #title>
        <div class="flex items-center gap-2">
          <ShoppingCartOutlined :style="{ color: 'var(--accent)' }" />
          <span>订单详情 — {{ selectedOrder?.order_no || '' }}</span>
        </div>
      </template>
      <div v-if="selectedOrder" class="space-y-5 py-1">
        <!-- Info grid -->
        <div class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '48px' }">状态</span>
            <Tag :color="statusColors[selectedOrder.status]">{{ statusLabels[selectedOrder.status] || selectedOrder.status }}</Tag>
          </div>
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '48px' }">客户</span>
            <span :style="{ color: 'var(--text-primary)', fontWeight: 500 }">{{ userMap.get(selectedOrder.customer_id)?.full_name || '—' }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '48px' }">原价</span>
            <span :style="{ color: 'var(--text-primary)' }">¥{{ Number(selectedOrder.total_amount).toFixed(2) }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '48px' }">折扣</span>
            <span :style="{ color: 'var(--danger)' }">−¥{{ Number(selectedOrder.discount_amount).toFixed(2) }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '48px' }">实付</span>
            <span class="font-bold" style="color:#f59e0b">¥{{ Number(selectedOrder.final_amount).toFixed(2) }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '48px' }">时间</span>
            <span :style="{ color: 'var(--text-primary)', fontSize: '13px' }">{{ new Date(selectedOrder.created_at).toLocaleString('zh-CN') }}</span>
          </div>
          <div v-if="selectedOrder.vehicle_info" class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '48px' }">车辆</span>
            <span :style="{ color: 'var(--text-primary)', fontSize: '13px' }">{{ selectedOrder.vehicle_info }}</span>
          </div>
          <div v-if="selectedOrder.driver_info" class="flex items-center gap-2">
            <span :style="{ color: 'var(--text-muted)', fontSize: '12px', minWidth: '48px' }">司机</span>
            <span :style="{ color: 'var(--text-primary)', fontSize: '13px' }">{{ selectedOrder.driver_info }}</span>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedOrder.notes" class="p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <p class="text-xs mb-1 font-medium" :style="{ color: 'var(--text-muted)' }">备注</p>
          <p class="text-sm" :style="{ color: 'var(--text-secondary)' }">{{ selectedOrder.notes }}</p>
        </div>

        <!-- Items table -->
        <div v-if="selectedOrder.items?.length">
          <p class="text-xs font-semibold mb-2" :style="{ color: 'var(--text-secondary)' }">订单商品</p>
          <div class="rounded-lg overflow-hidden border" :style="{ borderColor: 'var(--border-subtle)' }">
            <div class="grid grid-cols-5 gap-2 px-4 py-2 text-xs font-medium" :style="{ background: 'var(--input-bg)', color: 'var(--text-muted)' }">
              <span>商品</span><span>SKU</span><span class="text-center">数量</span><span class="text-center">单价</span><span class="text-right">小计</span>
            </div>
            <div v-for="(item, i) in selectedOrder.items" :key="i" class="grid grid-cols-5 gap-2 px-4 py-2.5 text-sm"
              :style="{ background: i % 2 === 0 ? 'transparent' : 'var(--input-bg)' }">
              <span :style="{ color: 'var(--text-primary)', fontWeight: 500 }">{{ productMap.get(item.product_id)?.name || item.product_id?.slice(0, 8) }}</span>
              <span :style="{ color: 'var(--accent)', fontFamily: 'ui-monospace, monospace', fontSize: '11px' }">{{ productMap.get(item.product_id)?.sku || '—' }}</span>
              <span class="text-center" :style="{ color: 'var(--text-primary)', fontFamily: 'ui-monospace, monospace' }">{{ item.quantity }}</span>
              <span class="text-center" :style="{ color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }">¥{{ Number(item.unit_price).toFixed(2) }}</span>
              <span class="text-right" :style="{ color: '#f59e0b', fontWeight: 600, fontFamily: 'ui-monospace, monospace' }">¥{{ Number(item.subtotal).toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <!-- Stock-out notice -->
        <div v-if="selectedOrder.status === 'shipped' || selectedOrder.status === 'delivered'" class="p-3 rounded-lg text-xs" :style="{ background: 'rgba(0,184,148,0.08)', color: 'var(--success)' }">
          此订单已自动生成出库单，对应商品库存已在发货时扣减。可在「库存管理 → 出库」中查看详情。
        </div>

        <!-- Status actions -->
        <div v-if="nextStatus[selectedOrder.status]?.length" class="flex justify-end gap-2 pt-2 border-t" :style="{ borderColor: 'var(--border-subtle)' }">
          <Button @click="() => { openStatusChange(selectedOrder); detailModal = false }">变更状态</Button>
        </div>
      </div>
    </Modal>

    <!-- ═══ Status change modal ═══ -->
    <Modal v-model:open="statusModal" title="变更订单状态" @ok="handleStatusChange" okText="确认" cancelText="取消" :width="460">
      <div class="space-y-3 py-2">
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">当前状态</label>
          <Tag :color="statusColors[selectedOrder?.status]">{{ statusLabels[selectedOrder?.status] || selectedOrder?.status }}</Tag>
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">新状态</label>
          <Select v-model:value="statusForm.status" class="w-full" placeholder="选择新状态"
            :options="(nextStatus[selectedOrder?.status] || []).map((s: string) => ({ value: s, label: statusLabels[s] }))" />
        </div>
        <div v-if="statusForm.status === 'shipped' || selectedOrder?.status === 'shipped'" class="grid grid-cols-2 gap-3">
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">车辆信息</label><Input v-model:value="statusForm.vehicle_info" placeholder="车牌号 / 车型" /></div>
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">司机信息</label><Input v-model:value="statusForm.driver_info" placeholder="司机姓名 / 电话" /></div>
        </div>
      </div>
    </Modal>

    <!-- ═══ Product edit modal ═══ -->
    <Modal :title="editing ? '编辑商品' : '新增商品'" v-model:open="modalOpen" @ok="handleSave" okText="保存" cancelText="取消" :width="480">
      <div class="grid grid-cols-2 gap-3 py-2">
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">SKU</label><Input v-model:value="form.sku" placeholder="PRO-001" /></div>
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">价格</label><InputNumber v-model:value="form.original_price" class="w-full" :min="0" :step="0.01" /></div>
        <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">商品名称</label><Input v-model:value="form.name" placeholder="商品名称" /></div>
        <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">分类</label><Select v-model:value="form.category" class="w-full" allowClear placeholder="选择分类" :options="categories.map(c=>({value:c,label:c}))" /></div>
      </div>
    </Modal>
  </div>
</template>
