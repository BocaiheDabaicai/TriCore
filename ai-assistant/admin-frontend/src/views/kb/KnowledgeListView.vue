<script setup>
import { onMounted, reactive, ref } from 'vue'
import { deleteKnowledge, listKnowledge } from '../../api/kb'

// 知识列表页：知识库内容管理（筛选 / 删除，经调度器代理转发 kb-agent）
const KIND_LABELS = { policy: '制度', document: '文档', workflow: '流程' }

const items = ref([])
const total = ref(0)
const loading = ref(false)
const error = ref('')
const filters = reactive({ keyword: '', kind: '', category: '' })

async function load() {
  loading.value = true
  error.value = ''
  try {
    const resp = await listKnowledge(filters)
    items.value = resp.data
    total.value = resp.total
  } catch (e) {
    error.value = '加载失败：' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

function reset() {
  filters.keyword = ''
  filters.kind = ''
  filters.category = ''
  load()
}

async function remove(item) {
  if (!confirm(`确定删除「${item.title}」？删除后不可恢复。`)) return
  try {
    await deleteKnowledge(item.id)
    load()
  } catch (e) {
    alert('删除失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(load)
</script>

<template>
  <div class="p-6 space-y-6">
    <div>
      <h1 class="text-2xl font-bold">知识列表</h1>
      <p class="text-sm text-base-content/60 mt-1">知识库内容管理：筛选、删除（共 {{ total }} 条）</p>
    </div>

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <!-- 筛选栏：关键字（标题/内容模糊）/ 类型 / 分类（精确匹配） -->
        <div class="flex flex-wrap gap-3 items-center">
          <input v-model="filters.keyword" class="input input-bordered input-sm w-56" placeholder="标题/内容关键字" @keyup.enter="load" />
          <select v-model="filters.kind" class="select select-bordered select-sm">
            <option value="">全部类型</option>
            <option value="policy">制度</option>
            <option value="document">文档</option>
            <option value="workflow">流程</option>
          </select>
          <input v-model="filters.category" class="input input-bordered input-sm w-40" placeholder="分类精确匹配" @keyup.enter="load" />
          <button class="btn btn-primary btn-sm" :disabled="loading" @click="load">
            {{ loading ? '查询中…' : '查询' }}
          </button>
          <button class="btn btn-ghost btn-sm" @click="reset">重置</button>
        </div>

        <div v-if="error" role="alert" class="alert alert-warning text-sm">{{ error }}</div>

        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>标题</th>
                <th>类型</th>
                <th>分类</th>
                <th>更新时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id">
                <td class="max-w-80 truncate" :title="item.title">{{ item.title }}</td>
                <td><span class="badge badge-outline badge-sm">{{ KIND_LABELS[item.kind] || item.kind }}</span></td>
                <td class="text-xs">{{ item.category }}</td>
                <td class="text-xs whitespace-nowrap">{{ item.created_at }}</td>
                <td>
                  <button class="btn btn-error btn-outline btn-xs" @click="remove(item)">删除</button>
                </td>
              </tr>
              <tr v-if="!items.length">
                <td colspan="5" class="text-center text-base-content/40 py-12">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
