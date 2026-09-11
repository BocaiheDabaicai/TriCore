<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Paperclip, Pencil, Trash2 } from 'lucide-vue-next'
import { marked } from 'marked'
import { deleteReading, getReading } from '../api/readings'
import { useToastStore } from '../stores/toast'
import { MODE_META } from '../utils/reading'

// 笔记详情：从回顾页点进来查看；「修改」把内容带入研读界面继续写；「删除」带确认弹窗
const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const item = ref(null)
const loading = ref(true)

const deleteDialog = ref(null)
const deleting = ref(false)

async function doDelete() {
  if (deleting.value) return
  deleting.value = true
  try {
    await deleteReading(item.value.id)
    toast.success('记录已删除')
    router.push('/review')
  } catch {
    toast.error('删除失败，请重试')
  } finally {
    deleting.value = false
  }
}

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
          <span class="badge badge-sm" :class="MODE_META[item.mode]?.badge">{{ MODE_META[item.mode]?.text }}</span>
          <span v-if="item.tag" class="badge badge-sm badge-outline">{{ item.tag }}</span>
          <span class="text-xs text-base-content/50 ml-2">
            创建 {{ item.created_at }} · 更新 {{ item.updated_at }}
          </span>
        </div>

        <div class="divider my-2"></div>

        <div v-if="item.note" class="md-body text-sm leading-relaxed" v-html="renderedNote"></div>
        <div v-else class="text-sm text-base-content/40">（还没有笔记内容）</div>

        <!-- 底部一行：左边论文文件（精读才有，点击打开），右边修改按钮 -->
        <div class="card-actions justify-between mt-4 w-full">
          <a
            v-if="item.attachment"
            :href="`/api/readings/${item.id}/attachment`"
            target="_blank"
            rel="noopener"
            class="btn btn-ghost btn-sm max-w-[60%]"
            :title="item.attachment"
          >
            <Paperclip class="w-4 h-4" />
            <span class="truncate">{{ item.attachment }}</span>
          </a>
          <span v-else></span>

          <div class="flex items-center gap-2">
            <button class="btn btn-ghost btn-sm text-error" @click="deleteDialog?.showModal()">
              <Trash2 class="w-4 h-4" />
              删除
            </button>
            <button class="btn btn-primary btn-sm" @click="router.push(`/edit/${item.id}`)">
              <Pencil class="w-4 h-4" />
              修改
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- 删除确认：daisyUI dialog（showModal 原生模态，点 backdrop / 取消都能关） -->
    <dialog ref="deleteDialog" class="modal">
      <div class="modal-box max-w-sm">
        <h3 class="font-bold">删除这条记录？</h3>
        <p class="py-2 text-sm text-base-content/60">
          「{{ item?.title }}」的笔记和附件会一并删除，不可恢复。
        </p>
        <div class="modal-action">
          <form method="dialog">
            <button class="btn btn-sm">取消</button>
          </form>
          <button class="btn btn-sm btn-error" :disabled="deleting" @click="doDelete">
            <span v-if="deleting" class="loading loading-spinner loading-xs"></span>
            删除
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop"><button>close</button></form>
    </dialog>
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
