<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { marked } from 'marked'
import { getReading, updateReading } from '../api/readings'

// 笔记详情：从回顾页点进来，先看为主（继续编辑等后端阶段一起做）
const route = useRoute()
const router = useRouter()

const item = ref(null)
const loading = ref(true)
const marking = ref(false)

onMounted(async () => {
  try {
    item.value = (await getReading(route.params.id)).data
  } finally {
    loading.value = false
  }
})

// 笔记按 Markdown 渲染（marked 把 md 文本转成 HTML）
const renderedNote = computed(() => (item.value?.note ? marked.parse(item.value.note) : ''))

// 作者 / 期刊 / 出版时间（选填，填了才显示）
const metaText = computed(() =>
  [
    item.value?.author && `作者：${item.value.author}`,
    item.value?.journal && `期刊：${item.value.journal}`,
    item.value?.published && `出版：${item.value.published}`,
  ]
    .filter(Boolean)
    .join(' · '),
)

async function markDone() {
  marking.value = true
  try {
    const res = await updateReading(item.value.id, { status: 'done' })
    item.value = res.data
  } finally {
    marking.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-3xl mx-auto">
    <button class="btn btn-ghost btn-sm mb-4" @click="router.push('/review')">
      <ArrowLeft class="w-4 h-4" /> 返回回顾
    </button>

    <div v-if="loading" class="flex justify-center py-20">
      <span class="loading loading-spinner"></span>
    </div>

    <div v-else-if="!item" class="text-center text-base-content/40 py-20">记录不存在</div>

    <div v-else class="card bg-base-100 shadow">
      <div class="card-body">
        <h1 class="text-xl font-bold">{{ item.title }}</h1>
        <div v-if="metaText" class="text-xs text-base-content/50 mt-1">{{ metaText }}</div>

        <div class="flex items-center gap-2 mt-2">
          <span class="badge badge-sm" :class="item.mode === 'close' ? 'badge-primary' : 'badge-secondary'">
            {{ item.mode === 'close' ? '精读' : '泛读' }}
          </span>
          <span class="badge badge-sm" :class="item.status === 'draft' ? 'badge-warning' : 'badge-success'">
            {{ item.status === 'draft' ? '草稿' : '完成' }}
          </span>
          <span class="text-xs text-base-content/50 ml-2">
            创建 {{ item.created_at }} · 更新 {{ item.updated_at }}
          </span>
        </div>

        <div class="divider my-2"></div>

        <div v-if="item.note" class="md-body text-sm leading-relaxed" v-html="renderedNote"></div>
        <div v-else class="text-sm text-base-content/40">（还没有笔记内容）</div>

        <div class="card-actions justify-end mt-4">
          <button v-if="item.status === 'draft'" class="btn btn-primary btn-sm" :disabled="marking" @click="markDone">
            <span v-if="marking" class="loading loading-spinner loading-xs"></span>
            标记完成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* v-html 渲染出的 Markdown 内容：Tailwind preflight 会抹掉浏览器默认排版，这里补回基本的 */
.md-body :deep(h1) { font-size: 1.25rem; font-weight: 700; margin: 1em 0 0.4em; }
.md-body :deep(h2) { font-size: 1.1rem; font-weight: 700; margin: 1em 0 0.4em; }
.md-body :deep(h3) { font-size: 1rem; font-weight: 700; margin: 0.8em 0 0.3em; }
.md-body :deep(p) { margin: 0.5em 0; }
.md-body :deep(ul), .md-body :deep(ol) { margin: 0.5em 0; padding-left: 1.4em; }
.md-body :deep(ul) { list-style: disc; }
.md-body :deep(ol) { list-style: decimal; }
.md-body :deep(li) { margin: 0.2em 0; }
.md-body :deep(code) { background: #f3f4f6; border-radius: 0.25rem; padding: 0.1em 0.35em; font-size: 0.9em; }
.md-body :deep(pre) { background: #f3f4f6; border-radius: 0.5rem; padding: 0.75rem 1rem; overflow: auto; margin: 0.6em 0; }
.md-body :deep(pre code) { background: none; padding: 0; }
.md-body :deep(blockquote) { border-left: 3px solid #d1d5db; padding-left: 0.9em; color: #6b7280; margin: 0.6em 0; }
</style>
