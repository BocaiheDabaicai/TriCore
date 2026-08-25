<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { Table, Tag, Button, Modal, Input, Select, message, Spin, Space, Upload } from 'ant-design-vue'
import { PlusOutlined, EyeOutlined, DeleteOutlined, UploadOutlined, FolderOpenOutlined } from '@ant-design/icons-vue'
import { regulationsAPI } from '@/services/regulations'
import axios from 'axios'

const loading = ref(true)
const files = ref<any[]>([])
const categories = ref<any[]>([])

const searchTitle = ref('')
const searchCategoryId = ref<string | undefined>(undefined)

// ── Upload modal ──
const uploadModal = ref(false)
const uploadForm = ref({ title: '', category_id: undefined as string | undefined, notes: '' })
const uploadFile = ref<File | null>(null)
const uploadSaving = ref(false)

// ── Category management modal ──
const catModal = ref(false)
const catSearch = ref('')
const newCatName = ref('')
const catSaving = ref(false)

const categoryOptions = ref<any[]>([])

const loadCategories = async () => {
  try {
    const res: any = await regulationsAPI.listCategories({ name: catSearch.value || undefined })
    const data = res?.data || []
    categories.value = data
    categoryOptions.value = data.map((c: any) => ({ value: c.id, label: c.name }))
  } catch { /* ignore */ }
}

const loadFiles = async () => {
  loading.value = true
  try {
    const params: any = { page: 1, per_page: 100 }
    if (searchTitle.value) params.title = searchTitle.value
    if (searchCategoryId.value) params.category_id = searchCategoryId.value
    const res: any = await regulationsAPI.listFiles(params)
    const data = res?.data
    files.value = data?.data || data || []
  } catch { message.error('加载文件列表失败') } finally { loading.value = false }
}

onMounted(async () => {
  await loadCategories()
  await loadFiles()
})

const handleSearch = () => loadFiles()

const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ── Upload ──
const openUpload = () => {
  uploadForm.value = { title: '', category_id: undefined, notes: '' }
  uploadFile.value = null
  uploadModal.value = true
}

const handleFileChange = (info: any) => {
  const f = info.fileList?.[info.fileList.length - 1]
  uploadFile.value = f?.originFileObj || null
}

const handleUpload = async () => {
  if (!uploadForm.value.title.trim()) { message.warning('请输入文件标题'); return }
  if (!uploadFile.value) { message.warning('请选择文件'); return }
  uploadSaving.value = true
  try {
    const fd = new FormData()
    fd.append('title', uploadForm.value.title.trim())
    if (uploadForm.value.category_id) fd.append('category_id', uploadForm.value.category_id)
    fd.append('notes', uploadForm.value.notes)
    fd.append('file', uploadFile.value)
    await regulationsAPI.uploadFile(fd)
    message.success('上传成功')
    uploadModal.value = false
    loadFiles()
  } catch (err: any) {
    message.error(err?.response?.data?.message || '上传失败')
  } finally { uploadSaving.value = false }
}

// ── Delete file ──
const handleDeleteFile = (record: any) => {
  Modal.confirm({
    title: '确认删除', content: `确定要删除文件「${record.title}」吗？`, okText: '确认删除', okType: 'danger', cancelText: '取消',
    onOk: async () => { try { await regulationsAPI.deleteFile(record.id); message.success('已删除'); loadFiles() } catch { message.error('删除失败') } },
  })
}

// ── View / Preview file ──
const previewLoading = ref(false)
const handleViewFile = async (record: any) => {
  previewLoading.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(regulationsAPI.downloadUrl(record.id), {
      responseType: 'blob',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    const blob = new Blob([res.data], { type: res.headers['content-type'] || record.content_type })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  } catch {
    message.error('加载文件失败')
  } finally { previewLoading.value = false }
}
// ── Category management ──
const openCatModal = () => {
  catSearch.value = ''
  newCatName.value = ''
  catModal.value = true
  loadCategories()
}

const handleAddCategory = async () => {
  const name = newCatName.value.trim()
  if (!name) { message.warning('请输入分类名称'); return }
  catSaving.value = true
  try {
    await regulationsAPI.createCategory({ name })
    message.success('分类已添加')
    newCatName.value = ''
    loadCategories()
  } catch (err: any) { message.error(err?.response?.data?.message || '添加失败') } finally { catSaving.value = false }
}

const handleDeleteCategory = (record: any) => {
  Modal.confirm({
    title: '确认删除', content: `确定要删除分类「${record.name}」吗？相关文件的分类将变为空。`, okText: '确认删除', okType: 'danger', cancelText: '取消',
    onOk: async () => { try { await regulationsAPI.deleteCategory(record.id); message.success('已删除'); loadCategories() } catch { message.error('删除失败') } },
  })
}

// ── Table columns ──
const fileCols = [
  { title: '文件名称', dataIndex: 'title', key: 'title',
    customRender: ({ text }: any) => h('span', { style: { fontWeight: 600, color: 'var(--text-primary)' } }, text) },
  { title: '分类', dataIndex: 'category_name', key: 'cat', width: 120,
    customRender: ({ text }: any) => text ? h(Tag, { color: 'blue' }, () => text) : h('span', { style: { color: 'var(--text-muted)' } }, '—') },
  { title: '大小', dataIndex: 'file_size', key: 'size', width: 100,
    customRender: ({ text }: any) => h('span', { style: { color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace', fontSize: '12px' } }, formatSize(Number(text))) },
  { title: '上传时间', dataIndex: 'created_at', key: 'time', width: 160,
    customRender: ({ text }: any) => h('span', { style: { fontSize: '12px', color: 'var(--text-muted)' } }, new Date(text).toLocaleString('zh-CN')) },
  { title: '操作', key: 'action', width: 140,
    customRender: ({ record }: any) => h(Space, { size: 4 }, () => [
      h(Button, { type: 'link', size: 'small', onClick: () => handleViewFile(record) }, () => [h(EyeOutlined), ' 查看']),
      h(Button, { type: 'link', size: 'small', danger: true, onClick: () => handleDeleteFile(record) }, () => [h(DeleteOutlined)]),
    ])},
]
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">规章制度</h2>
      <p>文件管理 · 分类归档 · 快速查阅</p>
    </div>
    <Spin :spinning="loading">
      <div class="glass-card p-6 space-y-4">
        <!-- Search bar -->
        <div class="flex items-center gap-3 flex-wrap">
          <Input v-model:value="searchTitle" placeholder="文件名关键字..." style="width:200px" allowClear @pressEnter="handleSearch" />
          <Select v-model:value="searchCategoryId" placeholder="全部分类" style="width:160px" allowClear :options="categoryOptions" />
          <Button type="primary" @click="handleSearch">查询</Button>
          <div class="flex-1" />
          <Button type="primary" @click="openUpload"><PlusOutlined /> 上传文件</Button>
        </div>

        <!-- File table -->
        <Table :columns="fileCols" :dataSource="files" rowKey="id" size="middle" :pagination="{ pageSize: 15, showSizeChanger: false }">
          <template #emptyText>暂无文件，点击「上传文件」添加</template>
        </Table>
      </div>
    </Spin>

    <!-- ═══ Upload Modal ═══ -->
    <Modal v-model:open="uploadModal" title="上传文件" @ok="handleUpload" :confirmLoading="uploadSaving" okText="上传" cancelText="取消" :width="680">
      <div class="space-y-3 py-2">
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">文件标题 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <Input v-model:value="uploadForm.title" placeholder="输入文件标题" />
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">文件分类</label>
          <div class="flex gap-2">
            <Select v-model:value="uploadForm.category_id" class="flex-1" placeholder="选择分类" :options="categoryOptions" allowClear showSearch />
            <Button @click="openCatModal"><FolderOpenOutlined /> 分类管理</Button>
          </div>
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">备注</label>
          <Input.TextArea v-model:value="uploadForm.notes" :rows="2" placeholder="文件备注..." />
        </div>
        <div>
          <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">文件 <span :style="{ color: 'var(--danger)' }">*</span></label>
          <Upload :before-upload="() => false" :max-count="1" @change="handleFileChange">
            <Button><UploadOutlined /> 选择文件</Button>
          </Upload>
        </div>
      </div>
    </Modal>

    <!-- ═══ Category Management Modal ═══ -->
    <Modal v-model:open="catModal" title="分类管理" :footer="null" :width="480" :zIndex="1010">
      <div class="space-y-3 py-2">
        <!-- Add category -->
        <div class="flex gap-2">
          <Input v-model:value="newCatName" placeholder="输入新分类名称" size="middle" style="flex:1" @pressEnter="handleAddCategory" />
          <Button type="primary" size="middle" @click="handleAddCategory" :loading="catSaving"><PlusOutlined /> 添加</Button>
        </div>

        <!-- Category search -->
        <Input v-model:value="catSearch" placeholder="搜索分类..." size="middle" allowClear @input="loadCategories" />

        <!-- Category list -->
        <div class="max-h-60 overflow-y-auto space-y-1">
          <div v-if="categories.length === 0" class="text-center py-6 text-sm" :style="{ color: 'var(--text-muted)' }">
            {{ catSearch ? '没有匹配的分类' : '暂无分类，在上方添加' }}
          </div>
          <div v-for="cat in categories" :key="cat.id"
            class="flex items-center justify-between px-3 py-2 rounded-lg"
            :style="{ background: 'var(--input-bg)', border: '1px solid var(--border-subtle)' }">
            <span class="text-sm font-medium" :style="{ color: 'var(--text-primary)' }">{{ cat.name }}</span>
            <Button type="text" size="small" danger @click="handleDeleteCategory(cat)"><DeleteOutlined /></Button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>
