<script setup lang="ts">
import { ref, onMounted, h, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Tabs, Space } from 'ant-design-vue'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { masterDataAPI } from '@/services/api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const mdCustomers = ref<any[]>([])
const mdDepartments = ref<any[]>([])
const mdPositions = ref<any[]>([])
const mdVehicles = ref<any[]>([])
const mdModal = ref(false)
const mdEditing = ref<any>(null)
const mdEntity = ref('')
const mdForm = ref<Record<string, any>>({})
const mdSaving = ref(false)

const activeTab = ref('customers')

watch(() => route.path, (p) => {
  const seg = p.split('/').pop()
  if (seg && ['customers', 'departments', 'positions', 'vehicles'].includes(seg)) {
    activeTab.value = seg
  }
}, { immediate: true })

const onTabChange = (key: string) => {
  router.push(`/master-data/${key}`)
}

const loadMasterData = async () => {
  loading.value = true
  try {
    const [c, d, p, v] = await Promise.all([
      masterDataAPI.listCustomers().catch(() => ({ data: [] })),
      masterDataAPI.listDepartments().catch(() => ({ data: [] })),
      masterDataAPI.listPositions().catch(() => ({ data: [] })),
      masterDataAPI.listVehicles().catch(() => ({ data: [] })),
    ])
    mdCustomers.value = (c as any).data || []
    mdDepartments.value = (d as any).data || []
    mdPositions.value = (p as any).data || []
    mdVehicles.value = (v as any).data || []
  } catch { /* ok */ } finally { loading.value = false }
}
onMounted(loadMasterData)

const getMdApi = () => {
  if (mdEntity.value === 'customer') return { create: masterDataAPI.createCustomer, update: masterDataAPI.updateCustomer, del: masterDataAPI.deleteCustomer }
  if (mdEntity.value === 'department') return { create: masterDataAPI.createDepartment, update: masterDataAPI.updateDepartment, del: masterDataAPI.deleteDepartment }
  if (mdEntity.value === 'position') return { create: masterDataAPI.createPosition, update: masterDataAPI.updatePosition, del: masterDataAPI.deletePosition }
  return { create: masterDataAPI.createVehicle, update: masterDataAPI.updateVehicle, del: masterDataAPI.deleteVehicle }
}

const openMdCreate = (entity: string) => {
  mdEntity.value = entity; mdEditing.value = null
  if (entity === 'vehicle') mdForm.value = { plate_number: '', model: '', capacity: '', driver_name: '', driver_phone: '', notes: '' }
  else if (entity === 'position') mdForm.value = { name: '', department_id: '', description: '' }
  else mdForm.value = { name: '', description: '' }
  mdModal.value = true
}
const openMdEdit = (entity: string, record: any) => {
  mdEntity.value = entity; mdEditing.value = record
  if (entity === 'customer') mdForm.value = { name: record.name, contact_person: record.contact_person, phone: record.phone, email: record.email, address: record.address, notes: record.notes }
  else if (entity === 'department') mdForm.value = { name: record.name, description: record.description }
  else if (entity === 'position') mdForm.value = { name: record.name, department_id: record.department_id, description: record.description }
  else mdForm.value = { plate_number: record.plate_number, model: record.model, capacity: record.capacity, driver_name: record.driver_name, driver_phone: record.driver_phone, notes: record.notes }
  mdModal.value = true
}
const handleMdSave = async () => {
  const api = getMdApi()
  mdSaving.value = true
  try {
    if (mdEditing.value) { await api.update(mdEditing.value.id, mdForm.value); message.success('已更新') }
    else { await api.create(mdForm.value); message.success('已创建') }
    mdModal.value = false; loadMasterData()
  } catch (err: any) { message.error(err?.response?.data?.message || '操作失败') } finally { mdSaving.value = false }
}
const handleMdDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除', content: '确定要删除吗？', okText: '确认删除', okType: 'danger', cancelText: '取消',
    onOk: async () => { try { await getMdApi().del(record.id); message.success('已删除'); loadMasterData() } catch { message.error('删除失败') } },
  })
}

const vehicleStatusColors: Record<string, string> = { available: 'green', in_use: 'blue', maintenance: 'orange' }

const makeCols = (entity: string) => {
  if (entity === 'customers') return [
    { title: '名称', dataIndex: 'name', key: 'name', customRender: ({ text }: any) => h('span', { style: { fontWeight: 600, color: 'var(--text-primary)' } }, text) },
    { title: '联系人', dataIndex: 'contact_person', key: 'cp', width: 100 },
    { title: '电话', dataIndex: 'phone', key: 'phone', width: 130 },
    { title: '邮箱', dataIndex: 'email', key: 'email', width: 180, customRender: ({ text }: any) => text || h('span', { style: { color: 'var(--text-muted)' } }, '—') },
    { title: '操作', key: 'action', width: 110, customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
      h(Button, { type: 'link', size: 'small', onClick: () => openMdEdit('customer', record) }, () => '编辑'),
      h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleMdDelete(record) }, () => [h(DeleteOutlined)]),
    ])},
  ]
  if (entity === 'departments') return [
    { title: '名称', dataIndex: 'name', key: 'name', customRender: ({ text }: any) => h('span', { style: { fontWeight: 600, color: 'var(--text-primary)' } }, text) },
    { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true },
    { title: '操作', key: 'action', width: 110, customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
      h(Button, { type: 'link', size: 'small', onClick: () => openMdEdit('department', record) }, () => '编辑'),
      h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleMdDelete(record) }, () => [h(DeleteOutlined)]),
    ])},
  ]
  if (entity === 'positions') return [
    { title: '名称', dataIndex: 'name', key: 'name', customRender: ({ text }: any) => h('span', { style: { fontWeight: 600, color: 'var(--text-primary)' } }, text) },
    { title: '所属部门', key: 'dept', width: 130, customRender: ({ record }: any) => {
      const d = mdDepartments.value.find((x: any) => x.id === record.department_id)
      return d ? h(Tag, {}, () => d.name) : h('span', { style: { color: 'var(--text-muted)' } }, '—')
    }},
    { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true },
    { title: '操作', key: 'action', width: 110, customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
      h(Button, { type: 'link', size: 'small', onClick: () => openMdEdit('position', record) }, () => '编辑'),
      h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleMdDelete(record) }, () => [h(DeleteOutlined)]),
    ])},
  ]
  return [
    { title: '车牌号', dataIndex: 'plate_number', key: 'plate', width: 130,
      customRender: ({ text }: any) => h('span', { style: { fontFamily: 'ui-monospace, monospace', fontWeight: 500, color: 'var(--accent)' } }, text) },
    { title: '车型', dataIndex: 'model', key: 'model', width: 110 },
    { title: '载重', dataIndex: 'capacity', key: 'cap', width: 90, customRender: ({ text }: any) => text || h('span', { style: { color: 'var(--text-muted)' } }, '—') },
    { title: '司机', dataIndex: 'driver_name', key: 'driver', width: 100, customRender: ({ text }: any) => text || h('span', { style: { color: 'var(--text-muted)' } }, '—') },
    { title: '状态', dataIndex: 'status', key: 'status', width: 85,
      customRender: ({ text }: any) => h(Tag, { color: vehicleStatusColors[text] || 'default' }, () => text === 'available' ? '空闲' : text === 'in_use' ? '使用中' : '维护中') },
    { title: '操作', key: 'action', width: 110, customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
      h(Button, { type: 'link', size: 'small', onClick: () => openMdEdit('vehicle', record) }, () => '编辑'),
      h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleMdDelete(record) }, () => [h(DeleteOutlined)]),
    ])},
  ]
}

const createEntity = computed(() => {
  if (activeTab.value === 'customers') return 'customer'
  if (activeTab.value === 'departments') return 'department'
  if (activeTab.value === 'positions') return 'position'
  return 'vehicle'
})
const getData = (key: string) => {
  if (key === 'customers') return mdCustomers.value
  if (key === 'departments') return mdDepartments.value
  if (key === 'positions') return mdPositions.value
  return mdVehicles.value
}
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">基础数据</h2>
      <p>客户 · 部门 · 职位 · 车辆管理</p>
    </div>
    <Spin :spinning="loading">
      <div class="glass-card p-6">
        <Tabs v-model:activeKey="activeTab" @change="onTabChange">
          <a-tab-pane key="customers" :tab="`客户 (${mdCustomers.length})`">
            <div class="mb-3"><Button type="primary" @click="openMdCreate('customer')"><PlusOutlined /> 添加客户</Button></div>
            <Table :columns="makeCols('customers')" :dataSource="mdCustomers" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
          <a-tab-pane key="departments" :tab="`部门 (${mdDepartments.length})`">
            <div class="mb-3"><Button type="primary" @click="openMdCreate('department')"><PlusOutlined /> 添加部门</Button></div>
            <Table :columns="makeCols('departments')" :dataSource="mdDepartments" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
          <a-tab-pane key="positions" :tab="`职位 (${mdPositions.length})`">
            <div class="mb-3"><Button type="primary" @click="openMdCreate('position')"><PlusOutlined /> 添加职位</Button></div>
            <Table :columns="makeCols('positions')" :dataSource="mdPositions" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
          <a-tab-pane key="vehicles" :tab="`车辆 (${mdVehicles.length})`">
            <div class="mb-3"><Button type="primary" @click="openMdCreate('vehicle')"><PlusOutlined /> 添加车辆</Button></div>
            <Table :columns="makeCols('vehicles')" :dataSource="mdVehicles" rowKey="id" size="small" :pagination="{ pageSize: 10, showSizeChanger: false }">
              <template #emptyText>暂无数据</template>
            </Table>
          </a-tab-pane>
        </Tabs>
      </div>
    </Spin>

    <!-- Form modal -->
    <Modal v-model:open="mdModal" :title="mdEditing ? '编辑' : '添加'" @ok="handleMdSave" :confirmLoading="mdSaving" okText="保存" cancelText="取消" :width="520">
      <div class="grid grid-cols-2 gap-3 py-2">
        <template v-if="mdEntity === 'customer'">
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">名称 <span :style="{ color: 'var(--danger)' }">*</span></label><Input v-model:value="mdForm.name" placeholder="客户名称" /></div>
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">联系人</label><Input v-model:value="mdForm.contact_person" placeholder="联系人" /></div>
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">电话</label><Input v-model:value="mdForm.phone" placeholder="电话" /></div>
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">邮箱</label><Input v-model:value="mdForm.email" placeholder="email@example.com" /></div>
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">地址</label><Input v-model:value="mdForm.address" placeholder="地址" /></div>
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label><Input.TextArea v-model:value="mdForm.notes" :rows="2" placeholder="备注" /></div>
        </template>
        <template v-if="mdEntity === 'department'">
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">名称 <span :style="{ color: 'var(--danger)' }">*</span></label><Input v-model:value="mdForm.name" placeholder="部门名称" /></div>
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">描述</label><Input.TextArea v-model:value="mdForm.description" :rows="2" placeholder="部门描述" /></div>
        </template>
        <template v-if="mdEntity === 'position'">
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">名称 <span :style="{ color: 'var(--danger)' }">*</span></label><Input v-model:value="mdForm.name" placeholder="职位名称" /></div>
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">所属部门</label><Select v-model:value="mdForm.department_id" class="w-full" placeholder="选择部门" :options="mdDepartments.map((d:any)=>({value:d.id,label:d.name}))" showSearch allowClear /></div>
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">描述</label><Input.TextArea v-model:value="mdForm.description" :rows="2" placeholder="职位描述" /></div>
        </template>
        <template v-if="mdEntity === 'vehicle'">
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">车牌号 <span :style="{ color: 'var(--danger)' }">*</span></label><Input v-model:value="mdForm.plate_number" placeholder="京A·12345" /></div>
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">车型</label><Input v-model:value="mdForm.model" placeholder="车型" /></div>
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">载重/容量</label><Input v-model:value="mdForm.capacity" placeholder="载重" /></div>
          <div><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">司机姓名</label><Input v-model:value="mdForm.driver_name" placeholder="司机" /></div>
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">司机电话</label><Input v-model:value="mdForm.driver_phone" placeholder="电话" /></div>
          <div class="col-span-2"><label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label><Input.TextArea v-model:value="mdForm.notes" :rows="2" placeholder="备注" /></div>
        </template>
      </div>
    </Modal>
  </div>
</template>
