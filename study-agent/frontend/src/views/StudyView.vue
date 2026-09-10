<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { BookOpen, Calendar, Clock, Upload, User } from 'lucide-vue-next'
import { createReading } from '../api/readings'
import MarkdownEditor from '../components/MarkdownEditor.vue'

// 研读页：精读 = 左论文 + 右笔记；泛读 = 上传区向左收起，笔记居中
const router = useRouter()

const title = ref('')
const mode = ref('close')   // close 精读 / skim 泛读
const author = ref('')      // 文献信息（选填）
const published = ref('')
const journal = ref('')
const note = ref('')
const saving = ref(false)

const canSave = computed(() => title.value.trim() || note.value.trim())

async function save() {
  if (!canSave.value || saving.value) return
  saving.value = true
  try {
    const res = await createReading({
      title: title.value.trim(),
      mode: mode.value,
      author: author.value.trim(),
      published: published.value.trim(),
      journal: journal.value.trim(),
      note: note.value,
    })
    router.push(`/review/${res.data.id}`)
  } finally {
    saving.value = false
  }
}

// ---- 底部实时时钟：年月日 + 星期 + 时分秒（每秒走一格） ----
const now = ref(new Date())
const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']
let timer = null

onMounted(() => {
  timer = setInterval(() => { now.value = new Date() }, 1000)
})
onUnmounted(() => clearInterval(timer))

const clockText = computed(() => {
  const d = now.value
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${WEEKDAYS[d.getDay()]} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
})
</script>

<template>
  <!-- grid 双列布局做动画：切泛读时左列 1fr → 0（连带 gap 消失），右列顺势滑向中央 -->
  <div
    class="h-screen grid p-4 transition-all duration-500 ease-in-out"
    :class="mode === 'close'
      ? 'grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-4'
      : 'grid-cols-[minmax(0,0fr)_minmax(0,1fr)] gap-0'"
  >
    <!-- 左：论文 / 截图（仅精读显示；收起时淡出并压缩到 0 宽） -->
    <div
      class="min-w-0 overflow-hidden transition-opacity duration-300"
      :class="mode === 'close' ? 'opacity-100' : 'opacity-0'"
    >
      <div
        class="h-full rounded-2xl border-2 border-dashed border-base-300 bg-base-200/40
               flex flex-col items-center justify-center gap-3 select-none
               hover:border-primary/40 hover:bg-primary/5 transition-colors"
      >
        <Upload class="w-10 h-10 text-base-content/30" />
        <div class="text-sm text-base-content/60">拖拽 PDF / 图片到这里</div>
        <div class="badge badge-sm badge-ghost">上传功能下一步接入</div>
      </div>
    </div>

    <!-- 右：笔记（精读占半屏；泛读居中收窄到阅读宽度） -->
    <div
      class="min-w-0 h-full mx-auto w-full flex flex-col gap-3
             transition-all duration-500 ease-in-out"
      :class="mode === 'close' ? 'max-w-7xl' : 'max-w-3xl'"
    >
      <div class="flex items-center gap-2">
        <input v-model="title" class="input flex-1" placeholder="文献标题" />
        <div class="join">
          <button class="btn join-item" :class="mode === 'close' ? 'btn-primary' : 'btn-ghost'" @click="mode = 'close'">
            精读
          </button>
          <button class="btn join-item" :class="mode === 'skim' ? 'btn-primary' : 'btn-ghost'" @click="mode = 'skim'">
            泛读
          </button>
        </div>
      </div>

      <!-- 文献信息（选填）：选填徽章 + 三个带图标前缀的输入；出版时间用原生月份选择器 -->
      <div class="flex items-center gap-2">
        <span class="badge badge-ghost badge-sm text-base-content/50 shrink-0">选填</span>

        <label class="input input-sm flex-1">
          <User class="w-3.5 h-3.5 opacity-40" />
          <input v-model="author" class="grow" placeholder="作者" />
        </label>

        <label class="input input-sm flex-1">
          <Calendar class="w-3.5 h-3.5 opacity-40" />
          <input v-model="published" class="grow" placeholder="出版时间（如 2024-06）" />
        </label>

        <label class="input input-sm flex-1">
          <BookOpen class="w-3.5 h-3.5 opacity-40" />
          <input v-model="journal" class="grow" placeholder="期刊" />
        </label>
      </div>

      <MarkdownEditor v-model="note" />

      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5 text-sm text-base-content/50 tabular-nums">
          <Clock class="w-4 h-4" />
          {{ clockText }}
        </div>
        <button class="btn btn-primary" :disabled="!canSave || saving" @click="save">
          <span v-if="saving" class="loading loading-spinner loading-xs"></span>
          保存
        </button>
      </div>
    </div>
  </div>
</template>
