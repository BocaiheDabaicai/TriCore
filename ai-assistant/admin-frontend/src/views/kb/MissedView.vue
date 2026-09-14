<script setup>
import { onMounted, ref } from 'vue'
import { clearMissed, deleteMissed, listMissed } from '../../api/kb'
import { errText } from '../../utils/error'
import PageHeader from '../../components/PageHeader.vue'

// 未命中问题页：知识库答不上的问题清单（按被问次数排序）——知识库建设的输入
const items = ref([])
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = (await listMissed(100)).data
  } catch (e) {
    error.value = '加载失败：' + errText(e)
  } finally {
    loading.value = false
  }
}

async function remove(item) {
  if (!confirm(`确定删除「${item.question}」？（对应知识已补充后删除）`)) return
  try {
    await deleteMissed(item.id)
    load()
  } catch (e) {
    alert('删除失败：' + errText(e))
  }
}

async function clearAll() {
  if (!items.value.length) return
  if (!confirm(`确定清空全部 ${items.value.length} 条未命中记录？`)) return
  try {
    await clearMissed()
    load()
  } catch (e) {
    alert('清空失败：' + errText(e))
  }
}

onMounted(load)
</script>

<template>
  <div class="p-6 space-y-6">
    <PageHeader title="未命中问题" desc="用户问什么没答上，就是该往知识库补什么——补充资料后删除对应记录" />

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <div class="flex justify-between items-center">
          <span class="text-xs text-base-content/60">按被问次数排序（次数高 = 最该优先补充）</span>
          <button class="btn btn-outline btn-sm" :disabled="!items.length" @click="clearAll">清空全部</button>
        </div>

        <div v-if="error" role="alert" class="alert alert-warning text-sm">{{ error }}</div>

        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>问题</th>
                <th>被问次数</th>
                <th>最近提问时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id">
                <td class="max-w-96 truncate" :title="item.question">{{ item.question }}</td>
                <td><span class="badge badge-warning badge-sm">{{ item.count }} 次</span></td>
                <td class="text-xs whitespace-nowrap">{{ item.last_at }}</td>
                <td>
                  <button class="btn btn-error btn-outline btn-xs" @click="remove(item)">删除</button>
                </td>
              </tr>
              <tr v-if="!items.length">
                <td colspan="4" class="text-center text-base-content/40 py-12">暂无未命中问题</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
