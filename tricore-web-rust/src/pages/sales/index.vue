<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { Table, Tag, Button, Modal, Input, InputNumber, Select, message, Spin, Tabs, Space } from 'ant-design-vue'
import { PlusOutlined, EyeOutlined, DeleteOutlined, ShoppingCartOutlined, CheckCircleOutlined } from '@ant-design/icons-vue'
import { salesAPI, masterDataAPI, inventoryAPI } from '@/services/api'

const loading = ref(true)
const products = ref<any[]>([])
const orders = ref<any[]>([])
const users = ref<any[]>([])
const catList = ref<any[]>([])
const mdCustomers = ref<any[]>([])
const mdVehicles = ref<any[]>([])
const activeTab = ref('orders')

// ── Product form ──
const modalOpen = ref(false)
const editing = ref<any>(null)
const form = ref({ sku: '', name: '', original_price: 0, category: '', description: '' })

const generateSku = () => {
  const today = new Date()
  const dateStr = today.getFullYear().toString() +
    String(today.getMonth() + 1).padStart(2, '0') +
    String(today.getDate()).padStart(2, '0')
  const count = products.value.length + 1
  return `SKU${dateStr}${String(count).padStart(4, '0')}`
}

const categoryOptions = computed(() =>
  catList.value.map((c: any) => ({ value: c.name, label: c.name }))
)

// ── Category form ──
const catModalOpen = ref(false)
const catEditing = ref<any>(null)
const catForm = ref({ name: '', description: '' })
const catSaving = ref(false)

// ── Order create / edit ──
type Allocation = { warehouse_id: string; warehouse_name: string; available: number; quantity: number }
type OrderItemEntry = { product_id: string; unit_price: number; allocations: Allocation[] }
const orderModal = ref(false)
const editOrderModal = ref(false)
const editingOrder = ref<any>(null)
const orderItems = ref<OrderItemEntry[]>([])
type Discount = { mode: 'percent' | 'fixed'; value: number; note: string }
const discounts = ref<Discount[]>([])
const orderForm = ref({ customer_id: '', notes: '', vehicle_id: '', vehicle_info: '', driver_info: '' })
const orderSaving = ref(false)

// ── Order detail ──
const detailModal = ref(false)
const selectedOrder = ref<any>(null)
const detailLoading = ref(false)

// ── Status change ──
const statusModal = ref(false)
const statusForm = ref({ status: '' })

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
  mdCustomers.value.map((c: any) => ({ value: c.id, label: `${c.name}${c.phone ? ` (${c.phone})` : ''}` }))
)
const vehicleOptions = computed(() =>
  mdVehicles.value.filter((v: any) => v.status !== 'maintenance').map((v: any) => ({
    value: v.id,
    label: `${v.plate_number}${v.model ? ` · ${v.model}` : ''}${v.driver_name ? ` · ${v.driver_name}` : ''}`,
    driver_name: v.driver_name,
    driver_phone: v.driver_phone,
    plate_number: v.plate_number,
  }))
)
const productOptions = computed(() =>
  products.value
    .filter((p: any) => p.quantity > 0)
    .map((p: any) => ({ value: p.id, label: `${p.name} (${p.sku}) — ¥${Number(p.original_price).toFixed(2)} · 库存: ${p.quantity}` }))
)

const customerMap = computed(() => {
  const m = new Map<string, any>(); for (const c of mdCustomers.value) m.set(c.id, c); return m
})
const warehouseMap = ref<Map<string, any>>(new Map())

// ── Computed order totals ──
const itemTotalQty = (item: OrderItemEntry) =>
  item.allocations.reduce((s, a) => s + a.quantity, 0)

const orderTotal = computed(() =>
  orderItems.value.reduce((sum, item) => {
    const qty = itemTotalQty(item)
    return sum + item.unit_price * qty
  }, 0)
)

const discountDetails = computed(() => {
  let running = orderTotal.value
  return discounts.value.map(d => {
    const amount = d.mode === 'percent' ? running * (d.value || 0) / 100 : Math.min(running, d.value || 0)
    running = Math.max(0, running - amount)
    return { amount }
  })
})

const totalDiscount = computed(() =>
  discountDetails.value.reduce((sum, d) => sum + d.amount, 0)
)

const orderFinal = computed(() => Math.max(0, orderTotal.value - totalDiscount.value))

const addDiscount = () => discounts.value.push({ mode: 'percent', value: 0, note: '' })
const removeDiscount = (i: number) => discounts.value.splice(i, 1)

const load = async () => {
  loading.value = true
  try {
    const [p, o, u, c, mc, mv, wh]: any[] = await Promise.all([
      salesAPI.listProducts({ per_page: 200 }),
      salesAPI.listOrders({ per_page: 100 }),
      salesAPI.listUsers({ per_page: 200 }).catch(() => ({ data: [] })),
      salesAPI.listCategories().catch(() => ({ data: [] })),
      masterDataAPI.listCustomers().catch(() => ({ data: [] })),
      masterDataAPI.listVehicles().catch(() => ({ data: [] })),
      inventoryAPI.listWarehouses().catch(() => ({ data: [] })),
    ])
    products.value = p?.data?.data || p?.data || []
    orders.value = o?.data?.data || o?.data || []
    users.value = u?.data?.data || u?.data || []
    catList.value = c?.data || []
    mdCustomers.value = (mc as any).data || []
    mdVehicles.value = (mv as any).data || []
    const whList = wh?.data || []
    const wm = new Map<string, any>(); for (const w of whList) wm.set(w.id, w); warehouseMap.value = wm
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

// ── Category CRUD ──
const openCatCreate = () => { catEditing.value = null; catForm.value = { name: '', description: '' }; catModalOpen.value = true }
const openCatEdit = (record: any) => { catEditing.value = record; catForm.value = { name: record.name, description: record.description || '' }; catModalOpen.value = true }
const handleCatSave = async () => {
  if (!catForm.value.name.trim()) { message.warning('请输入分类名称'); return }
  catSaving.value = true
  try {
    if (catEditing.value) { await salesAPI.updateCategory(catEditing.value.id, catForm.value); message.success('已更新') }
    else { await salesAPI.createCategory(catForm.value); message.success('已创建') }
    catModalOpen.value = false; load()
  } catch { message.error('操作失败') } finally { catSaving.value = false }
}
const handleCatDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除', content: `确定要删除分类「${record.name}」吗？`, okText: '确认删除', okType: 'danger', cancelText: '取消',
    onOk: async () => { try { await salesAPI.deleteCategory(record.id); message.success('已删除'); load() } catch { message.error('删除失败') } },
  })
}

// ── Order item management ──
const defaultAllocations = (): Allocation[] => [{ warehouse_id: '', warehouse_name: '', available: 0, quantity: 0 }]

const addOrderItem = () => orderItems.value.push({ product_id: '', unit_price: 0, allocations: defaultAllocations() })

const removeOrderItem = (i: number) => {
  if (orderItems.value.length <= 1) { message.warning('至少需要一个商品'); return }
  orderItems.value.splice(i, 1)
}

const onProductSelect = async (i: number, pid: string) => {
  const p = productMap.value.get(pid)
  if (!p) return
  orderItems.value[i].unit_price = Number(p.original_price)
  // Load per-warehouse inventory
  try {
    const res: any = await inventoryAPI.getWarehouseInventory(pid)
    const data = res?.data || []
    if (data.length > 0) {
      orderItems.value[i].allocations = data.map((wi: any) => ({
        warehouse_id: wi.warehouse_id || wi.inv?.warehouse_id,
        warehouse_name: wi.warehouse_name || warehouseMap.value.get(wi.warehouse_id || wi.inv?.warehouse_id)?.name || '未知仓库',
        available: wi.quantity ?? wi.inv?.quantity ?? 0,
        quantity: 0,
      }))
    } else {
      orderItems.value[i].allocations = defaultAllocations()
    }
  } catch {
    orderItems.value[i].allocations = defaultAllocations()
  }
}

const onVehicleSelect = (vid: string) => {
  const v = vehicleOptions.value.find((x: any) => x.value === vid)
  if (v) {
    orderForm.value.vehicle_info = v.plate_number
    orderForm.value.driver_info = [v.driver_name, v.driver_phone].filter(Boolean).join(' / ')
  }
}

const openOrderCreate = () => {
  editingOrder.value = null
  orderForm.value = { customer_id: '', notes: '', vehicle_id: '', vehicle_info: '', driver_info: '' }
  orderItems.value = [{ product_id: '', unit_price: 0, allocations: defaultAllocations() }]
  discounts.value = []
  orderModal.value = true
}

const openOrderEdit = async (data: any) => {
  // get_order returns { order: {...}, items: [...] }; flatten to top-level for the form
  const record = data.order ? { ...data.order, items: data.items } : data
  editingOrder.value = record
  // Match vehicle by plate number from the saved vehicle_info
  const savedPlate = record.vehicle_info || ''
  const matchedVehicle = savedPlate
    ? vehicleOptions.value.find((v: any) => v.plate_number === savedPlate)
    : null
  orderForm.value = {
    customer_id: record.customer_id, notes: record.notes || '',
    vehicle_id: matchedVehicle?.value || '',
    vehicle_info: savedPlate,
    driver_info: record.driver_info || '',
  }
  // Restore discounts from saved order
  const savedDiscounts: any[] = record.discounts || []
  discounts.value = savedDiscounts.map((d: any) => ({
    mode: d.mode as 'percent' | 'fixed',
    value: Number(d.value) || 0,
    note: d.note || '',
  }))
  const items = record.items || []
  if (items.length === 0) {
    orderItems.value = [{ product_id: '', unit_price: 0, allocations: defaultAllocations() }]
  } else {
    // Load per-warehouse inventory for each product to show allocation UI
    orderItems.value = items.map((it: any) => {
      const savedAllocs: any[] = it.warehouse_allocations || []
      return {
        product_id: it.product_id,
        unit_price: Number(it.unit_price),
        allocations: savedAllocs.length > 0
          ? savedAllocs.map((a: any) => ({
              warehouse_id: a.warehouse_id,
              warehouse_name: warehouseMap.value.get(a.warehouse_id)?.name || '未知仓库',
              available: 0,  // will be updated by onProductSelect
              quantity: a.quantity,
            }))
          : [{ warehouse_id: '', warehouse_name: '未记录分配', available: 0, quantity: it.quantity }],
      }
    })
    // Refresh warehouse inventory for each product, preserving saved allocations
    for (const item of orderItems.value) {
      if (item.product_id) {
        try {
          const res: any = await inventoryAPI.getWarehouseInventory(item.product_id)
          const data = res?.data || []
          const allocMap = new Map<string, number>()
          for (const a of item.allocations) if (a.warehouse_id) allocMap.set(a.warehouse_id, a.quantity)

          // Build allocations from current inventory (with available quantities)
          const merged: Allocation[] = data.length > 0
            ? data.map((wi: any) => {
                const wid = wi.warehouse_id || wi.inv?.warehouse_id
                return {
                  warehouse_id: wid,
                  warehouse_name: wi.warehouse_name || warehouseMap.value.get(wid)?.name || '未知仓库',
                  available: wi.quantity ?? wi.inv?.quantity ?? 0,
                  quantity: allocMap.get(wid) || 0,
                }
              })
            : []

          // Preserve saved allocations for warehouses NOT in current inventory response
          for (const a of item.allocations) {
            if (a.warehouse_id && !merged.find(m => m.warehouse_id === a.warehouse_id)) {
              merged.push({ ...a, available: 0 })
            }
          }

          if (merged.length > 0) item.allocations = merged
        } catch { /* keep saved allocations */ }
      }
    }
  }
  editOrderModal.value = true
}

const buildOrderPayload = () => {
  return {
    customer_id: orderForm.value.customer_id,
    notes: orderForm.value.notes || undefined,
    discount_amount: totalDiscount.value,
    discounts: discounts.value.length > 0
      ? discounts.value.map(d => ({ mode: d.mode, value: d.value, note: d.note || undefined }))
      : undefined,
    vehicle_info: orderForm.value.vehicle_info || undefined,
    driver_info: orderForm.value.driver_info || undefined,
    items: orderItems.value.map(item => {
      const qty = itemTotalQty(item)
      return {
        product_id: item.product_id,
        quantity: qty,
        unit_price: item.unit_price,
        allocations: item.allocations
          .filter(a => a.quantity > 0 && a.warehouse_id)
          .map(a => ({ warehouse_id: a.warehouse_id, quantity: a.quantity })),
      }
    }),
  }
}

const handleCreateOrder = async () => {
  if (!orderForm.value.customer_id) { message.warning('请选择客户'); return }
  if (orderItems.value.some((item) => !item.product_id)) { message.warning('请选择所有商品'); return }
  if (orderItems.value.some((item) => itemTotalQty(item) <= 0)) { message.warning('请为每个商品分配至少一个仓库的数量'); return }
  orderSaving.value = true
  try {
    await salesAPI.createOrder(buildOrderPayload())
    message.success('订单已创建')
    orderModal.value = false
    load()
  } catch (err: any) { message.error(err?.response?.data?.message || '创建失败') } finally { orderSaving.value = false }
}

const handleUpdateOrder = async () => {
  if (orderItems.value.some((item) => !item.product_id)) { message.warning('请选择所有商品'); return }
  if (orderItems.value.some((item) => itemTotalQty(item) <= 0)) { message.warning('每个商品至少需要一个数量'); return }
  orderSaving.value = true
  try {
    const payload = buildOrderPayload()
    await salesAPI.updateOrder(editingOrder.value.id, {
      ...payload,
      customer_id: orderForm.value.customer_id || editingOrder.value.customer_id,
    })
    message.success('订单已更新')
    editOrderModal.value = false
    load()
  } catch (err: any) { message.error(err?.response?.data?.message || '更新失败') } finally { orderSaving.value = false }
}

// ── Order detail ──
const detailWarehouseStock = ref<Map<string, any[]>>(new Map())

const openOrderDetail = async (id: string) => {
  detailLoading.value = true
  detailModal.value = true
  selectedOrder.value = null
  detailWarehouseStock.value = new Map()
  try {
    const res: any = await salesAPI.getOrder(id)
    const orderData = res?.data || res
    selectedOrder.value = orderData
    // Load per-warehouse stock for each product in the order
    if (orderData?.items?.length) {
      const stocks = await Promise.all(
        orderData.items.map((it: any) =>
          inventoryAPI.getWarehouseInventory(it.product_id).catch(() => ({ data: [] }))
        )
      )
      const map = new Map<string, any[]>()
      orderData.items.forEach((it: any, idx: number) => {
        map.set(it.product_id, stocks[idx]?.data || [])
      })
      detailWarehouseStock.value = map
    }
  } catch { message.error('加载失败') } finally { detailLoading.value = false }
}

// ── Status change ──
const openStatusChange = (order: any) => { selectedOrder.value = order; statusForm.value = { status: '' }; statusModal.value = true }
const handleStatusChange = async () => {
  if (!statusForm.value.status) { message.warning('请选择状态'); return }
  try {
    await salesAPI.updateOrderStatus(selectedOrder.value.id, { status: statusForm.value.status })
    message.success('状态已更新'); statusModal.value = false; load()
  } catch { message.error('操作失败') }
}

// ── Table columns ──
const orderCols = [
  { title: '订单号', dataIndex: 'order_no', key: 'no', width: 170,
    customRender: ({ text }: any) => h('span', { style: { fontFamily: 'ui-monospace, monospace', fontSize: '12px', color: 'var(--text-secondary)' } }, text) },
  { title: '客户', key: 'customer', width: 110,
    customRender: ({ record }: any) => {
      const c = customerMap.value.get(record.customer_id)
      return h('span', { style: { color: 'var(--text-primary)', fontWeight: 500 } }, c?.name || '—')
    }},
  { title: '金额', dataIndex: 'final_amount', key: 'amt', width: 120,
    customRender: ({ text }: any) => h('span', { style: { color: '#f59e0b', fontFamily: 'ui-monospace, monospace', fontWeight: 600 } }, `¥${Number(text).toFixed(2)}`) },
  { title: '状态', dataIndex: 'status', key: 'status', width: 90,
    customRender: ({ text }: any) => h(Tag, { color: statusColors[text] || 'default' }, () => statusLabels[text] || text) },
  { title: '车辆', dataIndex: 'vehicle_info', key: 'vehicle', width: 110, ellipsis: true,
    customRender: ({ text }: any) => text ? h('span', { style: { fontSize: '12px', color: 'var(--text-secondary)' } }, text) : h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '时间', dataIndex: 'created_at', key: 'time', width: 120,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleDateString('zh-CN')) },
  { title: '操作', key: 'action', width: 220,
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

const catCols = [
  { title: '名称', dataIndex: 'name', key: 'name',
    customRender: ({ text }: any) => h('span', { style: { fontWeight: 600, color: 'var(--text-primary)' } }, text) },
  { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true,
    customRender: ({ text }: any) => text || h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '状态', dataIndex: 'is_active', key: 'active', width: 80,
    customRender: ({ text }: any) => h(Tag, { color: text ? 'green' : 'default' }, () => text ? '启用' : '禁用') },
  { title: '操作', key: 'action', width: 110,
    customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
      h(Button, { type: 'link', size: 'small', onClick: () => openCatEdit(record) }, () => '编辑'),
      h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleCatDelete(record) }, () => [h(DeleteOutlined)]),
    ])},
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
          <a-tab-pane key="orders" :tab="`订单列表 (${orders.length})`">
            <div class="mb-3"><Button type="primary" @click="openOrderCreate"><PlusOutlined /> 创建订单</Button></div>
            <Table :columns="orderCols" :dataSource="orders" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>

          <a-tab-pane key="products" :tab="`商品管理 (${products.length})`">
            <div class="mb-3"><Button type="primary" @click="() => { editing = null; form = { sku: generateSku(), name: '', original_price: 0, category: '', description: '' }; modalOpen = true }"><PlusOutlined /> 新增商品</Button></div>
            <Table :columns="productCols" :dataSource="products" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>

          <a-tab-pane key="categories" :tab="`商品分类 (${catList.length})`">
            <div class="mb-3"><Button type="primary" @click="openCatCreate"><PlusOutlined /> 添加分类</Button></div>
            <Table :columns="catCols" :dataSource="catList" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
        </Tabs>
      </div>
    </Spin>

    <!-- ═══ Create Order modal ═══ -->
    <Modal v-model:open="orderModal" title="创建订单" @ok="handleCreateOrder" :confirmLoading="orderSaving" okText="创建订单" cancelText="取消" :width="960">
      <div class="space-y-4 py-2">
        <!-- Customer + Vehicle -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">客户 <span :style="{ color: 'var(--danger)' }">*</span></label>
            <Select v-model:value="orderForm.customer_id" class="w-full" placeholder="选择客户" :options="customerOptions" showSearch />
          </div>
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">配送车辆</label>
            <Select v-model:value="orderForm.vehicle_id" class="w-full" placeholder="选择车辆" :options="vehicleOptions" showSearch allowClear @change="(v: string) => onVehicleSelect(v)" />
          </div>
        </div>

        <!-- Vehicle info -->
        <div v-if="orderForm.vehicle_info" class="flex items-center gap-4 p-2.5 rounded-lg text-xs" :style="{ background: 'var(--input-bg)' }">
          <span :style="{ color: 'var(--text-muted)' }">车牌: <b :style="{ color: 'var(--accent)', fontFamily: 'ui-monospace, monospace' }">{{ orderForm.vehicle_info }}</b></span>
          <span :style="{ color: 'var(--text-muted)' }">司机: <b :style="{ color: 'var(--text-primary)' }">{{ orderForm.driver_info || '—' }}</b></span>
        </div>

        <!-- Items with per-warehouse allocation -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-medium" :style="{ color: 'var(--text-secondary)' }">订单商品</label>
            <Button type="link" size="small" @click="addOrderItem"><PlusOutlined /> 添加商品</Button>
          </div>
          <div class="space-y-3">
            <div v-for="(item, i) in orderItems" :key="i" class="p-3 rounded-lg" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-bold flex-shrink-0 min-w-5" :style="{ color: 'var(--text-muted)' }">#{{ i + 1 }}</span>
                <Select v-model:value="item.product_id" class="flex-1" placeholder="选择商品" :options="productOptions" showSearch @change="(v: string) => onProductSelect(i, v)" />
                <span class="text-xs flex-shrink-0" :style="{ color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace', minWidth: '70px', textAlign: 'right' }">¥{{ item.unit_price.toFixed(2) }}</span>
                <span class="text-xs font-mono flex-shrink-0" :style="{ color: '#f59e0b', fontWeight: 600, minWidth: '70px', textAlign: 'right' }">
                  共 {{ itemTotalQty(item) }} 件 · ¥{{ (item.unit_price * itemTotalQty(item)).toFixed(2) }}
                </span>
                <Button type="text" size="small" danger @click="removeOrderItem(i)"><DeleteOutlined /></Button>
              </div>
              <!-- Per-warehouse allocation sub-rows -->
              <div v-if="item.product_id" class="ml-6 space-y-1">
                <div class="text-xs mb-1" :style="{ color: 'var(--text-muted)' }">仓库分配数量（合计须 > 0）：</div>
                <div v-for="(alloc, ai) in item.allocations" :key="ai"
                  class="flex items-center gap-2 px-2 py-1 rounded" :style="{ background: ai % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.03)' }">
                  <span class="text-xs flex-1" :style="{ color: 'var(--text-primary)' }">{{ alloc.warehouse_name }}</span>
                  <span class="text-xs" :style="{ color: 'var(--text-muted)' }">可用: {{ alloc.available }}</span>
                  <InputNumber v-model:value="alloc.quantity" :min="0" :max="alloc.available" size="small" style="width:90px" placeholder="0" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Discounts -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-medium" :style="{ color: 'var(--text-secondary)' }">优惠方式</label>
            <Button type="link" size="small" @click="addDiscount"><PlusOutlined /> 添加优惠</Button>
          </div>
          <div v-if="discounts.length === 0" class="text-xs p-2 text-center rounded" :style="{ color: 'var(--text-muted)', background: 'var(--input-bg)' }">暂未添加优惠</div>
          <div v-for="(d, i) in discounts" :key="i" class="flex items-center gap-2 p-2 rounded-lg" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
            <span class="text-xs font-bold flex-shrink-0 min-w-5" :style="{ color: 'var(--text-muted)' }">#{{ i + 1 }}</span>
            <Select v-model:value="d.mode" style="width:110px" size="small" :options="[{value:'percent',label:'百分比 %'},{value:'fixed',label:'固定金额 ¥'}]" />
            <template v-if="d.mode === 'percent'">
              <InputNumber v-model:value="d.value" :min="0" :max="100" :step="1" style="width:80px" size="small" />
              <span class="text-xs" :style="{ color: 'var(--text-muted)' }">%</span>
            </template>
            <template v-else>
              <InputNumber v-model:value="d.value" :min="0" :step="0.01" style="width:120px" size="small" />
              <span class="text-xs" :style="{ color: 'var(--text-muted)' }">元</span>
            </template>
            <span class="text-xs font-mono flex-shrink-0" :style="{ color: 'var(--danger)', fontWeight: 600, minWidth: '60px', textAlign: 'right' }">
              −¥{{ discountDetails[i]?.amount?.toFixed(2) || '0.00' }}
            </span>
            <Input v-model:value="d.note" size="small" placeholder="备注" style="width:110px" />
            <Button type="text" size="small" danger @click="removeDiscount(i)"><DeleteOutlined /></Button>
          </div>
        </div>

        <!-- Summary -->
        <div class="flex justify-end gap-6 text-sm p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <span :style="{ color: 'var(--text-muted)' }">商品总额: <b :style="{ color: 'var(--text-primary)' }">¥{{ orderTotal.toFixed(2) }}</b></span>
          <span v-if="totalDiscount > 0" :style="{ color: 'var(--text-muted)' }">优惠合计: <b :style="{ color: 'var(--danger)' }">−¥{{ totalDiscount.toFixed(2) }}</b></span>
          <span :style="{ color: 'var(--text-muted)' }">实付: <b :style="{ color: 'var(--accent)', fontSize: '16px' }">¥{{ orderFinal.toFixed(2) }}</b></span>
        </div>

        <!-- Notes -->
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label>
          <Input.TextArea v-model:value="orderForm.notes" :rows="2" placeholder="订单备注..." />
        </div>
      </div>
    </Modal>

    <!-- ═══ Edit Order modal (full create UI) ═══ -->
    <Modal v-model:open="editOrderModal" title="编辑订单" @ok="handleUpdateOrder" :confirmLoading="orderSaving" okText="保存修改" cancelText="取消" :width="960">
      <div class="space-y-4 py-2">
        <div class="flex items-center gap-3 p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <div class="stat-icon-circle" :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }"><ShoppingCartOutlined /></div>
          <div>
            <p class="font-semibold" :style="{ color: 'var(--text-primary)' }">{{ editingOrder?.order_no }}</p>
            <p class="text-xs" :style="{ color: 'var(--text-muted)' }">待处理订单 — 可修改全部信息（商品、优惠、配送、备注）</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">客户</label>
            <Select v-model:value="orderForm.customer_id" class="w-full" placeholder="选择客户" :options="customerOptions" showSearch />
          </div>
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">配送车辆</label>
            <Select v-model:value="orderForm.vehicle_id" class="w-full" placeholder="选择车辆" :options="vehicleOptions" showSearch allowClear @change="(v: string) => onVehicleSelect(v)" />
          </div>
        </div>

        <!-- Vehicle info -->
        <div v-if="orderForm.vehicle_info" class="flex items-center gap-4 p-2.5 rounded-lg text-xs" :style="{ background: 'var(--input-bg)' }">
          <span :style="{ color: 'var(--text-muted)' }">车牌: <b :style="{ color: 'var(--accent)', fontFamily: 'ui-monospace, monospace' }">{{ orderForm.vehicle_info }}</b></span>
          <span :style="{ color: 'var(--text-muted)' }">司机: <b :style="{ color: 'var(--text-primary)' }">{{ orderForm.driver_info || '—' }}</b></span>
        </div>

        <!-- Items with per-warehouse allocation (edit mode) -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-medium" :style="{ color: 'var(--text-secondary)' }">订单商品</label>
            <Button type="link" size="small" @click="addOrderItem"><PlusOutlined /> 添加商品</Button>
          </div>
          <div class="space-y-3">
            <div v-for="(item, i) in orderItems" :key="i" class="p-3 rounded-lg" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-bold flex-shrink-0 min-w-5" :style="{ color: 'var(--text-muted)' }">#{{ i + 1 }}</span>
                <Select v-model:value="item.product_id" class="flex-1" placeholder="选择商品" :options="productOptions" showSearch @change="(v: string) => onProductSelect(i, v)" />
                <span class="text-xs flex-shrink-0" :style="{ color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace', minWidth: '70px', textAlign: 'right' }">¥{{ item.unit_price.toFixed(2) }}</span>
                <span class="text-xs font-mono flex-shrink-0" :style="{ color: '#f59e0b', fontWeight: 600, minWidth: '80px', textAlign: 'right' }">
                  共 {{ itemTotalQty(item) }} 件 · ¥{{ (item.unit_price * itemTotalQty(item)).toFixed(2) }}
                </span>
                <Button type="text" size="small" danger @click="removeOrderItem(i)"><DeleteOutlined /></Button>
              </div>
              <div v-if="item.product_id && item.allocations.length > 0" class="ml-6 space-y-1">
                <div class="text-xs mb-1" :style="{ color: 'var(--text-muted)' }">仓库分配数量：</div>
                <div v-for="(alloc, ai) in item.allocations" :key="ai"
                  class="flex items-center gap-2 px-2 py-1 rounded" :style="{ background: ai % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.03)' }">
                  <span class="text-xs flex-1" :style="{ color: 'var(--text-primary)' }">{{ alloc.warehouse_name }}</span>
                  <span class="text-xs" :style="{ color: 'var(--text-muted)' }">可用: {{ alloc.available }}</span>
                  <InputNumber v-model:value="alloc.quantity" :min="0" :max="alloc.available" size="small" style="width:90px" placeholder="0" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Discounts -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-medium" :style="{ color: 'var(--text-secondary)' }">优惠方式</label>
            <Button type="link" size="small" @click="addDiscount"><PlusOutlined /> 添加优惠</Button>
          </div>
          <div v-if="discounts.length === 0" class="text-xs p-2 text-center rounded" :style="{ color: 'var(--text-muted)', background: 'var(--input-bg)' }">暂未添加优惠</div>
          <div v-for="(d, i) in discounts" :key="i" class="flex items-center gap-2 p-2 rounded-lg" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
            <span class="text-xs font-bold flex-shrink-0 min-w-5" :style="{ color: 'var(--text-muted)' }">#{{ i + 1 }}</span>
            <Select v-model:value="d.mode" style="width:110px" size="small" :options="[{value:'percent',label:'百分比 %'},{value:'fixed',label:'固定金额 ¥'}]" />
            <template v-if="d.mode === 'percent'">
              <InputNumber v-model:value="d.value" :min="0" :max="100" :step="1" style="width:80px" size="small" />
              <span class="text-xs" :style="{ color: 'var(--text-muted)' }">%</span>
            </template>
            <template v-else>
              <InputNumber v-model:value="d.value" :min="0" :step="0.01" style="width:120px" size="small" />
              <span class="text-xs" :style="{ color: 'var(--text-muted)' }">元</span>
            </template>
            <span class="text-xs font-mono flex-shrink-0" :style="{ color: 'var(--danger)', fontWeight: 600, minWidth: '60px', textAlign: 'right' }">
              −¥{{ discountDetails[i]?.amount?.toFixed(2) || '0.00' }}
            </span>
            <Input v-model:value="d.note" size="small" placeholder="备注" style="width:110px" />
            <Button type="text" size="small" danger @click="removeDiscount(i)"><DeleteOutlined /></Button>
          </div>
        </div>

        <!-- Summary -->
        <div class="flex justify-end gap-6 text-sm p-3 rounded-lg" :style="{ background: 'var(--input-bg)' }">
          <span :style="{ color: 'var(--text-muted)' }">商品总额: <b :style="{ color: 'var(--text-primary)' }">¥{{ orderTotal.toFixed(2) }}</b></span>
          <span v-if="totalDiscount > 0" :style="{ color: 'var(--text-muted)' }">优惠合计: <b :style="{ color: 'var(--danger)' }">−¥{{ totalDiscount.toFixed(2) }}</b></span>
          <span :style="{ color: 'var(--text-muted)' }">实付: <b :style="{ color: 'var(--accent)', fontSize: '16px' }">¥{{ orderFinal.toFixed(2) }}</b></span>
        </div>

        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label>
          <Input.TextArea v-model:value="orderForm.notes" :rows="2" placeholder="订单备注..." />
        </div>
      </div>
    </Modal>

    <!-- ═══ Order Detail modal ═══ -->
    <Modal v-model:open="detailModal" :footer="null" :width="820" @cancel="selectedOrder = null">
      <template #title>
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center" :style="{ background: 'var(--accent-soft)' }">
            <ShoppingCartOutlined :style="{ color: 'var(--accent)', fontSize:'16px' }" />
          </div>
          <div>
            <p class="font-semibold text-sm" :style="{ color: 'var(--text-primary)' }">订单详情</p>
            <p class="text-xs" :style="{ color: 'var(--accent)', fontFamily:'ui-monospace,monospace' }">{{ selectedOrder?.order_no || '' }}</p>
          </div>
        </div>
      </template>
      <Spin :spinning="detailLoading">
        <div v-if="selectedOrder" class="space-y-4 py-2">
          <!-- ═══ 基本信息 ═══ -->
          <div class="rounded-xl p-4" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
            <div class="flex items-center gap-2 mb-3">
              <span class="w-1 h-4 rounded-full" :style="{ background: 'var(--accent)' }"></span>
              <span class="text-xs font-semibold tracking-wide uppercase" :style="{ color: 'var(--text-secondary)' }">基本信息</span>
            </div>
            <div class="grid grid-cols-4 gap-4 text-sm">
              <div>
                <p class="text-xs mb-0.5" :style="{ color: 'var(--text-muted)' }">订单状态</p>
                <Tag :color="statusColors[selectedOrder.status]">{{ statusLabels[selectedOrder.status] || selectedOrder.status }}</Tag>
              </div>
              <div>
                <p class="text-xs mb-0.5" :style="{ color: 'var(--text-muted)' }">客户名称</p>
                <p class="font-medium" :style="{ color: 'var(--text-primary)' }">{{ customerMap.get(selectedOrder.customer_id)?.name || '—' }}</p>
              </div>
              <div>
                <p class="text-xs mb-0.5" :style="{ color: 'var(--text-muted)' }">创建时间</p>
                <p class="text-xs" :style="{ color: 'var(--text-primary)' }">{{ new Date(selectedOrder.created_at).toLocaleString('zh-CN') }}</p>
              </div>
              <div>
                <p class="text-xs mb-0.5" :style="{ color: 'var(--text-muted)' }">更新时间</p>
                <p class="text-xs" :style="{ color: 'var(--text-primary)' }">{{ new Date(selectedOrder.updated_at).toLocaleString('zh-CN') }}</p>
              </div>
            </div>
          </div>

          <!-- ═══ 客户与配送 ═══ -->
          <div class="grid grid-cols-2 gap-4">
            <div class="rounded-xl p-4" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
              <div class="flex items-center gap-2 mb-3">
                <span class="w-1 h-4 rounded-full" :style="{ background: '#6366f1' }"></span>
                <span class="text-xs font-semibold tracking-wide uppercase" :style="{ color: 'var(--text-secondary)' }">客户信息</span>
              </div>
              <div v-if="customerMap.get(selectedOrder.customer_id)" class="space-y-1.5 text-sm">
                <div class="flex justify-between"><span :style="{ color:'var(--text-muted)' }">联系人</span><span :style="{ color:'var(--text-primary)', fontWeight:500 }">{{ customerMap.get(selectedOrder.customer_id)?.contact_person || '—' }}</span></div>
                <div class="flex justify-between"><span :style="{ color:'var(--text-muted)' }">电话</span><span :style="{ color:'var(--text-primary)' }">{{ customerMap.get(selectedOrder.customer_id)?.phone || '—' }}</span></div>
                <div class="flex justify-between"><span :style="{ color:'var(--text-muted)' }">邮箱</span><span :style="{ color:'var(--text-primary)' }">{{ customerMap.get(selectedOrder.customer_id)?.email || '—' }}</span></div>
                <div class="flex justify-between"><span :style="{ color:'var(--text-muted)' }">地址</span><span :style="{ color:'var(--text-primary)', fontSize:'12px' }">{{ customerMap.get(selectedOrder.customer_id)?.address || '—' }}</span></div>
              </div>
              <p v-else class="text-xs" :style="{ color:'var(--text-muted)' }">客户信息未录入</p>
            </div>
            <div class="rounded-xl p-4" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
              <div class="flex items-center gap-2 mb-3">
                <span class="w-1 h-4 rounded-full" :style="{ background: '#f59e0b' }"></span>
                <span class="text-xs font-semibold tracking-wide uppercase" :style="{ color: 'var(--text-secondary)' }">配送信息</span>
              </div>
              <div v-if="selectedOrder.vehicle_info || selectedOrder.driver_info" class="space-y-1.5 text-sm">
                <div class="flex justify-between"><span :style="{ color:'var(--text-muted)' }">车辆</span><span :style="{ color:'var(--text-primary)', fontFamily:'ui-monospace,monospace' }">{{ selectedOrder.vehicle_info || '—' }}</span></div>
                <div class="flex justify-between"><span :style="{ color:'var(--text-muted)' }">司机</span><span :style="{ color:'var(--text-primary)' }">{{ selectedOrder.driver_info || '—' }}</span></div>
              </div>
              <p v-else class="text-xs" :style="{ color:'var(--text-muted)' }">未指定配送信息</p>
            </div>
          </div>

          <!-- ═══ 金额概览 ═══ -->
          <div class="rounded-xl p-4" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
            <div class="flex items-center gap-2 mb-3">
              <span class="w-1 h-4 rounded-full" :style="{ background: '#00b894' }"></span>
              <span class="text-xs font-semibold tracking-wide uppercase" :style="{ color: 'var(--text-secondary)' }">金额明细</span>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-6">
                <div class="text-center">
                  <p class="text-xs mb-1" :style="{ color:'var(--text-muted)' }">商品总额</p>
                  <p class="text-lg font-semibold" :style="{ color:'var(--text-primary)' }">¥{{ Number(selectedOrder.total_amount).toFixed(2) }}</p>
                </div>
                <span class="text-xl" :style="{ color:'var(--text-muted)' }">−</span>
                <div class="text-center">
                  <p class="text-xs mb-1" :style="{ color:'var(--text-muted)' }">优惠折扣</p>
                  <p class="text-lg font-semibold" :style="{ color:'var(--danger)' }">¥{{ Number(selectedOrder.discount_amount).toFixed(2) }}</p>
                </div>
                <span class="text-xl" :style="{ color:'var(--text-muted)' }">=</span>
                <div class="text-center px-4 py-2 rounded-lg" :style="{ background: 'rgba(245,158,11,0.08)' }">
                  <p class="text-xs mb-0.5" style="color:#f59e0b">实付金额</p>
                  <p class="text-xl font-bold" style="color:#f59e0b">¥{{ Number(selectedOrder.final_amount).toFixed(2) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- ═══ 商品明细（含仓库分配） ═══ -->
          <div v-if="selectedOrder.items?.length" class="rounded-xl p-4" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
            <div class="flex items-center gap-2 mb-3">
              <span class="w-1 h-4 rounded-full" :style="{ background: '#e17055' }"></span>
              <span class="text-xs font-semibold tracking-wide uppercase" :style="{ color: 'var(--text-secondary)' }">商品明细 · {{ selectedOrder.items.length }} 项</span>
            </div>
            <div class="space-y-2">
              <div v-for="(item, i) in selectedOrder.items" :key="i"
                class="rounded-lg p-3" :style="{ background: i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.04)', border: '1px solid var(--border-subtle)' }">
                <!-- Item header -->
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-3">
                    <span class="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold"
                      :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">{{ i + 1 }}</span>
                    <div>
                      <p class="text-sm font-semibold" :style="{ color:'var(--text-primary)' }">{{ productMap.get(item.product_id)?.name || item.product_id?.slice(0,8) }}</p>
                      <p class="text-xs" :style="{ color:'var(--accent)', fontFamily:'ui-monospace,monospace' }">{{ productMap.get(item.product_id)?.sku || '—' }}</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <p class="text-sm font-semibold" :style="{ color:'#f59e0b', fontFamily:'ui-monospace,monospace' }">¥{{ Number(item.subtotal).toFixed(2) }}</p>
                    <p class="text-xs" :style="{ color:'var(--text-muted)' }">{{ item.quantity }} 件 × ¥{{ Number(item.unit_price).toFixed(2) }}</p>
                  </div>
                </div>
                <!-- Per-warehouse allocation from order -->
                <div v-if="item.warehouse_allocations?.length" class="mt-2 pt-2 border-t" :style="{ borderColor: 'var(--border-subtle)' }">
                  <p class="text-xs mb-1.5" :style="{ color:'var(--text-muted)' }">下单仓库分配</p>
                  <div class="space-y-1">
                    <div v-for="(alloc, ai) in item.warehouse_allocations" :key="ai"
                      class="flex items-center justify-between px-2 py-1.5 rounded text-xs"
                      :style="{ background: ai % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.04)' }">
                      <div class="flex items-center gap-2">
                        <span class="w-1.5 h-1.5 rounded-full" :style="{ background: 'var(--accent)' }"></span>
                        <span :style="{ color:'var(--text-primary)' }">{{ warehouseMap.get(alloc.warehouse_id)?.name || alloc.warehouse_id?.slice(0,8) }}</span>
                      </div>
                      <span class="font-mono font-semibold text-xs px-2 py-0.5 rounded" :style="{ color:'var(--accent)', background: 'var(--accent-soft)' }">{{ alloc.quantity }} 件</span>
                    </div>
                  </div>
                </div>
                <!-- Fallback: show current stock if no allocation data -->
                <div v-else-if="detailWarehouseStock.get(item.product_id)?.length" class="mt-2 pt-2 border-t" :style="{ borderColor: 'var(--border-subtle)' }">
                  <p class="text-xs mb-1.5" :style="{ color:'var(--text-muted)' }">各仓库当前库存（无分配记录）</p>
                  <div class="grid grid-cols-3 gap-2">
                    <div v-for="(ws, wi) in detailWarehouseStock.get(item.product_id)?.slice(0, 6)" :key="wi"
                      class="flex items-center justify-between px-2 py-1 rounded text-xs"
                      :style="{ background: 'rgba(255,255,255,0.03)' }">
                      <span :style="{ color:'var(--text-primary)' }">{{ ws.warehouse_name || warehouseMap.get(ws.warehouse_id || ws.inv?.warehouse_id)?.name || '—' }}</span>
                      <span class="font-mono font-semibold" :style="{ color:'var(--text-secondary)' }">{{ ws.quantity ?? ws.inv?.quantity ?? 0 }} 件</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ═══ 备注 ═══ -->
          <div v-if="selectedOrder.notes" class="rounded-xl p-4" :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
            <div class="flex items-center gap-2 mb-3">
              <span class="w-1 h-4 rounded-full" :style="{ background: '#a29bfe' }"></span>
              <span class="text-xs font-semibold tracking-wide uppercase" :style="{ color: 'var(--text-secondary)' }">备注</span>
            </div>
            <p class="text-sm leading-relaxed" :style="{ color:'var(--text-secondary)' }">{{ selectedOrder.notes }}</p>
          </div>

          <!-- Stock-out notice -->
          <div v-if="selectedOrder.status === 'shipped' || selectedOrder.status === 'delivered'" class="rounded-xl p-3 text-xs flex items-center gap-2"
            :style="{ background: 'rgba(0,184,148,0.06)', color: 'var(--success)', border: '1px solid rgba(0,184,148,0.15)' }">
            <CheckCircleOutlined /> 此订单已自动生成出库单，对应商品库存已在发货时扣减。可在「库存管理 → 出库」中查看详情。
          </div>

          <!-- Status actions -->
          <div v-if="nextStatus[selectedOrder.status]?.length" class="flex justify-end gap-2 pt-1">
            <Button @click="() => { openStatusChange(selectedOrder); detailModal = false }">变更状态</Button>
          </div>
        </div>
      </Spin>
    </Modal>

    <!-- ═══ Status change modal ═══ -->
    <Modal v-model:open="statusModal" title="变更订单状态" @ok="handleStatusChange" okText="确认" cancelText="取消" :width="420">
      <div class="space-y-4 py-2">
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">当前状态</label>
          <Tag :color="statusColors[selectedOrder?.status]">{{ statusLabels[selectedOrder?.status] || selectedOrder?.status }}</Tag>
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">新状态</label>
          <Select v-model:value="statusForm.status" class="w-full" placeholder="选择新状态"
            :options="(nextStatus[selectedOrder?.status] || []).map((s: string) => ({ value: s, label: statusLabels[s] }))" />
        </div>
      </div>
    </Modal>

    <!-- ═══ Product edit modal ═══ -->
    <Modal :title="editing ? '编辑商品' : '新增商品'" v-model:open="modalOpen" @ok="handleSave" okText="保存" cancelText="取消" :width="480">
      <div class="grid grid-cols-2 gap-3 py-2">
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">SKU</label><Input v-model:value="form.sku" placeholder="自动生成" disabled /></div>
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">价格</label><InputNumber v-model:value="form.original_price" class="w-full" :min="0" :step="0.01" /></div>
        <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">商品名称</label><Input v-model:value="form.name" placeholder="商品名称" /></div>
        <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">分类</label><Select v-model:value="form.category" class="w-full" allowClear placeholder="选择分类" :options="categoryOptions" /></div>
      </div>
    </Modal>

    <!-- ═══ Category modal ═══ -->
    <Modal :title="catEditing ? '编辑分类' : '添加分类'" v-model:open="catModalOpen" @ok="handleCatSave" :confirmLoading="catSaving" okText="保存" cancelText="取消" :width="460">
      <div class="grid gap-3 py-2">
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">名称 <span :style="{ color: 'var(--danger)' }">*</span></label><Input v-model:value="catForm.name" placeholder="分类名称" /></div>
        <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">描述</label><Input.TextArea v-model:value="catForm.description" :rows="2" placeholder="分类描述" /></div>
      </div>
    </Modal>
  </div>
</template>
