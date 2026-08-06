<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { Table, Tag, Button, Modal, message, Spin, Space } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { snapshotAPI } from '@/services/data-snapshots'

const loading = ref(false)
const snapshots = ref<any[]>([])

const loadSnapshots = async () => {
  loading.value = true
  try {
    const res: any = await snapshotAPI.list()
    snapshots.value = res?.data || []
  } catch {
    message.error('加载快照列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => loadSnapshots())

const handleCreate = async () => {
  try {
    await snapshotAPI.create()
    message.success('快照创建成功')
    loadSnapshots()
  } catch {
    message.error('创建快照失败')
  }
}

const handleRestore = (record: any) => {
  Modal.confirm({
    title: '确认恢复数据',
    content: `确定要恢复到此快照「${new Date(record.snapshot_time).toLocaleString('zh-CN')}」的数据吗？当前所有数据将被替换，此操作不可撤销。`,
    okText: '确认恢复',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await snapshotAPI.restore(record.id)
        message.success('数据恢复成功')
      } catch {
        message.error('数据恢复失败')
      }
    },
  })
}

const handleDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除快照「${new Date(record.snapshot_time).toLocaleString('zh-CN')}」吗？`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await snapshotAPI.delete(record.id)
        message.success('已删除')
        loadSnapshots()
      } catch {
        message.error('删除失败')
      }
    },
  })
}

const cols = [
  {
    title: '快照时间', dataIndex: 'snapshot_time', key: 'time', width: 180,
    customRender: ({ text }: any) => h('span', { style: { fontWeight: 600, color: 'var(--text-primary)', fontSize: '13px' } }, new Date(text).toLocaleString('zh-CN')),
  },
  {
    title: '覆盖表数', dataIndex: 'table_count', key: 'count', width: 90,
    customRender: ({ text }: any) => h(Tag, { color: 'blue' }, () => String(text)),
  },
  {
    title: '状态', dataIndex: 'status', key: 'status', width: 90,
    customRender: ({ text }: any) => {
      const color = text === 'completed' ? 'green' : text === 'in_progress' ? 'orange' : 'red'
      const label = text === 'completed' ? '已完成' : text === 'in_progress' ? '进行中' : '失败'
      return h(Tag, { color }, () => label)
    },
  },
  {
    title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true,
    customRender: ({ text }: any) => text
      ? h('span', { style: { color: 'var(--text-secondary)' } }, text)
      : h('span', { style: { color: 'var(--text-muted)' } }, '—'),
  },
  {
    title: '创建时间', dataIndex: 'created_at', key: 'created', width: 160,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleString('zh-CN')),
  },
  {
    title: '操作', key: 'action', width: 140,
    customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
      h(Button, { type: 'link', size: 'small', onClick: () => handleRestore(record), disabled: record.status !== 'completed' }, () => [h(ReloadOutlined), ' 恢复']),
      h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleDelete(record) }, () => [h(DeleteOutlined)]),
    ]),
  },
]
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">数据快照</h2>
      <p>定时备份数据库 · 最多保留 12 条 · 支持一键恢复</p>
    </div>

    <Spin :spinning="loading">
      <div class="glass-card p-6 space-y-4">
        <div class="flex items-center gap-3">
          <div class="flex-1" />
          <Button type="primary" @click="handleCreate">
            <PlusOutlined /> 创建快照
          </Button>
        </div>

        <Table
          :columns="cols"
          :dataSource="snapshots"
          rowKey="id"
          size="middle"
          :pagination="{ pageSize: 15, showSizeChanger: false }"
        >
          <template #emptyText>暂无快照，点击「创建快照」手动备份，或等待系统自动备份</template>
        </Table>
      </div>
    </Spin>
  </div>
</template>
