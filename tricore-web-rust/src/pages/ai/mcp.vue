<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { Button, Input, Select, message, Spin, Table, Modal, Tag, Switch, Space } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, EditOutlined, ReloadOutlined, ApiOutlined } from '@ant-design/icons-vue'
import { mcpAPI } from '@/services/ai'

const servers = ref<any[]>([])
const tools = ref<any[]>([])
const loading = ref(false)
const serverModal = ref(false)
const serverSaving = ref(false)
const editingId = ref<string | null>(null)
const serverForm = ref({ name: '', transport: 'stdio', command: '', args: '', url: '' })

const transportOptions = [
  { value: 'stdio', label: 'stdio (本地进程)' },
  { value: 'sse', label: 'SSE (远程 HTTP)' },
]

const loadServers = async () => {
  loading.value = true
  try { const r: any = await mcpAPI.listServers(); servers.value = r?.data || [] } catch { message.error('加载失败') } finally { loading.value = false }
}

const loadTools = async () => {
  try { const r: any = await mcpAPI.listTools(); tools.value = r?.data || [] } catch { /* ignore */ }
}

onMounted(() => { loadServers(); loadTools() })

const openAdd = () => {
  editingId.value = null; serverForm.value = { name: '', transport: 'stdio', command: '', args: '', url: '' }; serverModal.value = true
}

const openEdit = (record: any) => {
  editingId.value = record.id
  serverForm.value = { name: record.name, transport: record.transport, command: record.command || '', args: record.args || '', url: record.url || '' }
  serverModal.value = true
}

const handleSave = async () => {
  if (!serverForm.value.name.trim()) { message.warning('请输入服务名称'); return }
  if (serverForm.value.transport === 'stdio' && !serverForm.value.command.trim()) { message.warning('请输入启动命令'); return }
  if (serverForm.value.transport === 'sse' && !serverForm.value.url.trim()) { message.warning('请输入 URL'); return }
  serverSaving.value = true
  try {
    const data: any = { ...serverForm.value, command: serverForm.value.command || null, args: serverForm.value.args || null, url: serverForm.value.url || null }
    if (editingId.value) { await mcpAPI.updateServer(editingId.value, data); message.success('已更新') }
    else { await mcpAPI.createServer(data); message.success('已添加') }
    serverModal.value = false; loadServers(); loadTools()
  } catch (err: any) { message.error(err?.response?.data?.message || '保存失败') } finally { serverSaving.value = false }
}

const handleDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除', content: `确定要删除 MCP 服务「${record.name}」吗？`, okText: '确认删除', okType: 'danger', cancelText: '取消',
    onOk: async () => { try { await mcpAPI.deleteServer(record.id); message.success('已删除'); loadServers(); loadTools() } catch { message.error('删除失败') } },
  })
}

const handleToggle = async (record: any) => {
  try { await mcpAPI.updateServer(record.id, { is_enabled: !record.is_enabled }); loadServers(); loadTools() } catch { message.error('操作失败') }
}

const handleRefresh = async () => {
  try { await mcpAPI.refresh(); message.success('已刷新'); loadTools() } catch { message.error('刷新失败') }
}

const serverCols = [
  { title: '名称', dataIndex: 'name', customRender: ({ text }: any) => h('span', { style: { fontWeight: 600, color: 'var(--text-primary)' } }, text) },
  { title: '传输', dataIndex: 'transport', width: 90, customRender: ({ text }: any) => h(Tag, { color: text === 'sse' ? 'blue' : 'green' }, () => text.toUpperCase()) },
  { title: '地址', ellipsis: true, customRender: ({ record }: any) => h('code', { style: { fontSize: '11px' } }, record.transport === 'sse' ? record.url : record.command) },
  { title: '启用', dataIndex: 'is_enabled', width: 70, customRender: ({ record }: any) => h(Switch, { checked: record.is_enabled, size: 'small', onChange: () => handleToggle(record) }) },
  { title: '操作', width: 90, customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
    h(Button, { type: 'link', size: 'small', onClick: () => openEdit(record) }, () => [h(EditOutlined)]),
    h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleDelete(record) }, () => [h(DeleteOutlined)]),
  ])},
]

const toolCols = [
  { title: '工具名称', dataIndex: 'name', customRender: ({ text }: any) => h('code', text) },
  { title: '来源', dataIndex: 'server_name', width: 140, customRender: ({ text }: any) => h(Tag, () => text) },
  { title: '描述', dataIndex: 'description', ellipsis: true, customRender: ({ text }: any) => h('span', { style: { color: 'var(--text-muted)', fontSize: '12px' } }, text || '—') },
]
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">MCP 服务</h2>
      <p>接入外部 MCP Server，扩展 AI 能力</p>
    </div>

    <Spin :spinning="loading">
      <div class="glass-card" style="padding:24px">
        <div class="flex items-center gap-3" style="margin-bottom:16px">
          <div style="flex:1" />
          <Button size="small" @click="handleRefresh"><ReloadOutlined /> 刷新工具</Button>
          <Button type="primary" @click="openAdd"><PlusOutlined /> 添加服务</Button>
        </div>

        <div v-if="servers.length === 0" class="text-center" style="padding:32px 0;color:var(--text-muted);font-size:13px">
          暂无 MCP 服务。点击「添加服务」接入外部工具。
        </div>

        <Table v-else :columns="serverCols" :dataSource="servers" rowKey="id" size="middle" :pagination="false" />

        <div v-if="tools.length > 0" style="margin-top:24px">
          <div class="flex items-center gap-2" style="margin-bottom:12px">
            <ApiOutlined :style="{ color: 'var(--accent)' }" />
            <span style="font-weight:600;font-size:13px;color:var(--text-primary)">已发现工具（{{ tools.length }}）</span>
          </div>
          <Table :columns="toolCols" :dataSource="tools" :pagination="false" size="small" />
        </div>
      </div>
    </Spin>

    <Modal v-model:open="serverModal" :title="editingId ? '编辑 MCP 服务' : '添加 MCP 服务'" @ok="handleSave" :confirmLoading="serverSaving" okText="保存" cancelText="取消" :width="500">
      <div style="display:flex;flex-direction:column;gap:12px;padding-top:8px">
        <div>
          <label style="font-size:12px;margin-bottom:4px;display:block;font-weight:500;color:var(--text-secondary)">名称 <span style="color:var(--danger)">*</span></label>
          <Input v-model:value="serverForm.name" placeholder="如 GitHub、Filesystem" />
        </div>
        <div>
          <label style="font-size:12px;margin-bottom:4px;display:block;font-weight:500;color:var(--text-secondary)">传输方式</label>
          <Select v-model:value="serverForm.transport" :options="transportOptions" style="width:100%" />
        </div>
        <template v-if="serverForm.transport === 'stdio'">
          <div>
            <label style="font-size:12px;margin-bottom:4px;display:block;font-weight:500;color:var(--text-secondary)">启动命令 <span style="color:var(--danger)">*</span></label>
            <Input v-model:value="serverForm.command" placeholder="npx @anthropic/mcp-server-github" />
          </div>
          <div>
            <label style="font-size:12px;margin-bottom:4px;display:block;font-weight:500;color:var(--text-secondary)">参数（JSON 数组）</label>
            <Input v-model:value="serverForm.args" placeholder='["--token","ghp_xxx"]' />
          </div>
        </template>
        <div v-else>
          <label style="font-size:12px;margin-bottom:4px;display:block;font-weight:500;color:var(--text-secondary)">SSE URL <span style="color:var(--danger)">*</span></label>
          <Input v-model:value="serverForm.url" placeholder="http://localhost:3001/sse" />
        </div>
      </div>
    </Modal>
  </div>
</template>
