<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { Table, Tag, Button, Modal, Input, InputNumber, Select, message, Spin, Tabs } from 'ant-design-vue'
import { PlusOutlined, EyeOutlined } from '@ant-design/icons-vue'
import { salesAPI } from '@/services/api'

const loading = ref(true)
const products = ref<any[]>([])
const orders = ref<any[]>([])
const modalOpen = ref(false)
const orderModal = ref(false)
const selectedOrder = ref<any>(null)
const editing = ref<any>(null)
const form = ref({ sku: '', name: '', original_price: 0, category: '', description: '' })

const load = async () => {
  loading.value = true
  try {
    const [p, o]: any[] = await Promise.all([salesAPI.listProducts({ per_page: 100 }), salesAPI.listOrders({ per_page: 50 })])
    products.value = p?.data?.data || p?.data || []
    orders.value = o?.data?.data || o?.data || []
  } catch { message.error('加载失败') } finally { loading.value = false }
}
onMounted(load)

const handleSave = async () => {
  if (!form.value.name || !form.value.sku) { message.warning('请填写名称和SKU'); return }
  try {
    if (editing.value) { await salesAPI.updateProduct(editing.value.id, form.value); message.success('已更新') }
    else { await salesAPI.createProduct(form.value); message.success('已创建') }
    modalOpen.value = false; editing.value = null; form.value = { sku: '', name: '', original_price: 0, category: '', description: '' }; load()
  } catch { message.error('操作失败') }
}

const openOrder = async (id: string) => {
  try { const res: any = await salesAPI.getOrder(id); selectedOrder.value = res?.data || res; orderModal.value = true } catch { message.error('加载失败') }
}

const productCols = [
  { title: 'SKU', dataIndex: 'sku', key: 'sku' },
  { title: '商品名称', dataIndex: 'name', key: 'name' },
  { title: '价格', dataIndex: 'original_price', key: 'price' },
  { title: '库存', dataIndex: 'quantity', key: 'qty' },
  { title: '操作', key: 'action', customRender: ({ record }: any) =>
    h(Button, { type: 'link', size: 'small', onClick: () => { editing.value = record; form.value = { sku: record.sku, name: record.name, original_price: Number(record.original_price), category: record.category || '', description: record.description || '' }; modalOpen.value = true } }, () => '编辑') },
]

const orderCols = [
  { title: '订单号', dataIndex: 'order_no', key: 'no' },
  { title: '金额', dataIndex: 'final_amount', key: 'amt' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action', customRender: ({ record }: any) =>
    h(Button, { type: 'link', size: 'small', onClick: () => openOrder(record.id) }, () => [h(EyeOutlined), ' 详情']) },
]
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-2 gradient-text">销售管理</h2>
    <p class="text-sm mb-6" :style="{ color: 'var(--text-muted)' }">商品定价 · 订单管理 · 捆绑销售 · 退单处理</p>
    <Spin :spinning="loading">
      <div class="glass-card p-4">
        <Tabs :items="[
          { key: 'orders', tab: `📋 订单列表 (${orders.length})` },
          { key: 'products', tab: `📦 商品管理 (${products.length})` },
        ]" />
        <div class="mb-3 mt-3"><Button type="primary" @click="() => { editing = null; form = { sku: '', name: '', original_price: 0, category: '', description: '' }; modalOpen = true }"><PlusOutlined /> 新增商品</Button></div>
        <Table :columns="productCols" :dataSource="products" rowKey="id" size="middle" :pagination="{ pageSize: 10 }" />
      </div>
    </Spin>

    <Modal v-model:open="modalOpen" :title="editing ? '编辑商品' : '新增商品'" @ok="handleSave" okText="保存" cancelText="取消">
      <div class="space-y-3 py-2">
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">SKU</label><Input v-model:value="form.sku" placeholder="PRO-001" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">商品名称</label><Input v-model:value="form.name" placeholder="商品名称" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">价格</label><InputNumber v-model:value="form.original_price" class="w-full" :min="0" :step="0.01" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">分类</label><Select v-model:value="form.category" class="w-full" allowClear placeholder="选择分类" :options="['电子产品','日用品','食品','服装','办公用品','医疗','运动'].map(c=>({value:c,label:c}))" /></div>
      </div>
    </Modal>

    <Modal v-model:open="orderModal" :title="`订单详情 — ${selectedOrder?.order_no || ''}`" :footer="null" width="640px">
      <div v-if="selectedOrder" class="space-y-4 py-2">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div><span :style="{ color: 'var(--text-secondary)' }">订单号：</span><span class="font-mono" :style="{ color: 'var(--text-primary)' }">{{ selectedOrder.order_no }}</span></div>
          <div><span :style="{ color: 'var(--text-secondary)' }">状态：</span><Tag>{{ selectedOrder.status }}</Tag></div>
          <div><span :style="{ color: 'var(--text-secondary)' }">原价：</span><span :style="{ color: 'var(--text-primary)' }">¥{{ Number(selectedOrder.total_amount).toFixed(2) }}</span></div>
          <div><span :style="{ color: 'var(--text-secondary)' }">实付：</span><span class="text-amber-500 font-bold">¥{{ Number(selectedOrder.final_amount).toFixed(2) }}</span></div>
        </div>
      </div>
    </Modal>
  </div>
</template>
