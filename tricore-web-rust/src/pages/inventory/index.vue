<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs } from 'ant-design-vue'
import { PlusOutlined, CheckCircleOutlined } from '@ant-design/icons-vue'
import { inventoryAPI } from '@/services/api'

const loading = ref(true)
const products = ref<any[]>([])
const stockIn = ref<any[]>([])
const stockOut = ref<any[]>([])
const issues = ref<any[]>([])
const issueModal = ref(false)
const issueForm = ref({ description: '', severity: 'medium', related_type: 'product', related_id: '', reported_by: '' })

const load = async () => {
  loading.value = true
  try {
    const [p, si, so, iss]: any[] = await Promise.all([inventoryAPI.listProducts(), inventoryAPI.listStockIn({ per_page: 50 }), inventoryAPI.listStockOut({ per_page: 50 }), inventoryAPI.listIssues({ per_page: 50 })])
    products.value = p?.data || []; stockIn.value = si?.data?.data || si?.data || []; stockOut.value = so?.data?.data || so?.data || []; issues.value = iss?.data?.data || iss?.data || []
  } catch { message.error('加载失败') } finally { loading.value = false }
}
onMounted(load)

const handleResolve = async (id: string) => {
  const res = prompt('解决方案：'); if (!res) return
  try { await inventoryAPI.resolveIssue(id, { resolution: res }); message.success('已解决'); load() } catch { message.error('操作失败') }
}

const productCols = [
  { title: 'SKU', dataIndex: 'sku', key: 'sku' },
  { title: '商品', dataIndex: 'name', key: 'name' },
  { title: '库存', dataIndex: 'quantity', key: 'qty' },
  { title: '单价', dataIndex: 'original_price', key: 'price' },
]
const issueCols = [
  { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true },
  { title: '严重', dataIndex: 'severity', key: 'sev' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action', customRender: ({ record }: any) => record.status !== 'resolved' && record.status !== 'closed' ? h(Button, { type: 'link', size: 'small', onClick: () => handleResolve(record.id) }, () => [h(CheckCircleOutlined), ' 解决']) : h('span', { class: 'text-xs text-emerald-500' }, '已解决') },
]
const siCols = [
  { title: '单号', dataIndex: 'stock_in_no', key: 'no' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
  { title: '时间', dataIndex: 'created_at', key: 'time' },
]
const soCols = [
  { title: '单号', dataIndex: 'stock_out_no', key: 'no' },
  { title: '车辆', dataIndex: 'vehicle_info', key: 'vehicle' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '时间', dataIndex: 'created_at', key: 'time' },
]
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-2 gradient-text">库存管理</h2>
    <p class="text-sm mb-6" :style="{ color: 'var(--text-muted)' }">入库 · 出库 · 盘点 · 问题追踪</p>
    <Spin :spinning="loading">
      <div class="glass-card p-4">
        <Tabs :items="[
          { key:'stock', tab:`📦 库存 (${products.length})` },
          { key:'stock-in', tab:`📥 入库 (${stockIn.length})` },
          { key:'stock-out', tab:`📤 出库 (${stockOut.length})` },
          { key:'issues', tab:`⚠️ 问题 (${issues.length})` },
        ]" />
        <div class="mb-3 mt-3"><Button type="primary" @click="() => { issueForm.related_id = products[0]?.id || ''; issueModal = true }"><PlusOutlined /> 登记问题</Button></div>
        <Table :columns="productCols" :dataSource="products" rowKey="id" size="middle" :pagination="{ pageSize: 10 }" />
      </div>
    </Spin>

    <Modal v-model:open="issueModal" title="登记问题" @ok="async () => { try { await inventoryAPI.createIssue(issueForm); message.success('已登记'); issueModal = false; load() } catch { message.error('操作失败') } }" okText="提交" cancelText="取消">
      <div class="space-y-3 py-2">
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">关联类型</label><Select v-model:value="issueForm.related_type" class="w-full" :options="[{value:'product',label:'商品'},{value:'stock_in',label:'入库单'},{value:'stock_out',label:'出库单'},{value:'order',label:'订单'}]" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">关联ID</label><Select v-model:value="issueForm.related_id" class="w-full" showSearch :options="products.map((p:any)=>({value:p.id,label:`${p.name} (${p.sku})`}))" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">严重程度</label><Select v-model:value="issueForm.severity" class="w-full" :options="[{value:'low',label:'低'},{value:'medium',label:'中'},{value:'high',label:'高'},{value:'critical',label:'严重'}]" /></div>
        <div><label class="text-sm mb-1 block" :style="{ color: 'var(--text-secondary)' }">问题描述</label><Input.TextArea v-model:value="issueForm.description" :rows="3" placeholder="描述问题..." /></div>
      </div>
    </Modal>
  </div>
</template>
