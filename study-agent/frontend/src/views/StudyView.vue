<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { BookOpen, Calendar, Clock, Paperclip, Tag, Upload, User } from 'lucide-vue-next'
import { createReading, getReading, listReadings, updateReading, uploadReadingAttachment } from '../api/readings'
import { useToastStore } from '../stores/toast'
import { isAllowedAttachment, isImageFile } from '../utils/file'
import { formatClock } from '../utils/format'
import MarkdownEditor from '../components/MarkdownEditor.vue'

const toast = useToastStore()

// 研读页：精读 = 左论文 + 右笔记；泛读 = 上传区向左收起，笔记居中
// 从详情页「修改」进来（/edit/:id）时变成编辑模式：带入内容，保存 = 更新
const route = useRoute()
const router = useRouter()

const recordId = ref(null)  // 有值 = 编辑已有记录
const title = ref('')
const mode = ref('close')   // close 精读 / skim 泛读
const tag = ref('')         // 分类标签（选填，可自创或选已有）
const author = ref('')      // 文献信息（选填）
const published = ref('')
const journal = ref('')
const note = ref('')
const attachment = ref('')  // 论文文件名（精读，已存到服务器的）
const saving = ref(false)

const tagOptions = ref([])      // 已有标签候选（从记录里收集）
const tagOpen = ref(false)      // 标签候选面板显隐
const pickedFile = ref(null)    // 新选择的文件（保存后自动上传）
const fileInput = ref(null)     // 隐藏的文件选择框
const dragOver = ref(false)     // 拖拽悬停高亮

// 左区显示的文件名：优先显示新选的文件，否则显示已有附件
const displayFileName = computed(() => pickedFile.value?.name || attachment.value)

// 新选文件的本地预览地址（保存前也能在左区看到内容；换文件时释放旧地址）
const previewUrl = ref('')
watch(pickedFile, (f) => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = f ? URL.createObjectURL(f) : ''
})

// 左区显示什么：优先新选文件的本地预览，否则已存附件（后端地址）
const viewerSrc = computed(() => {
  if (pickedFile.value) return previewUrl.value
  if (recordId.value && attachment.value) return `/api/readings/${recordId.value}/attachment`
  return ''
})

// 图片走 <img> 直接显示；PDF 走 <iframe> 调浏览器内置阅读器（翻页/缩放都可用）
const viewerIsImage = computed(() => isImageFile(pickedFile.value?.name || attachment.value))

// 标签候选：按输入过滤（空输入显示全部）
const tagSuggestions = computed(() => {
  const kw = tag.value.trim().toLowerCase()
  return tagOptions.value.filter((t) => !kw || t.toLowerCase().includes(kw))
})

const canSave = computed(() => !!(title.value.trim() || note.value.trim() || pickedFile.value))

function acceptFile(file) {
  if (!file) return
  if (!isAllowedAttachment(file.name)) {
    toast.error('只支持 PDF / 图片文件（pdf、png、jpg、jpeg、gif、webp）')
    return
  }
  pickedFile.value = file
  markDirty()
}

function onPick(e) {
  acceptFile(e.target.files?.[0])
  e.target.value = ''   // 清空，允许再次选择同一个文件
}

function onDrop(e) {
  dragOver.value = false
  acceptFile(e.dataTransfer?.files?.[0])
}

function pickTag(t) {
  tag.value = t
  tagOpen.value = false
}

// 失焦延迟关面板：给候选按钮的 mousedown 留出点选时间
function closeTagLater() {
  setTimeout(() => { tagOpen.value = false }, 120)
}

// ---- 自动保存 ----
// 思路：内容改完停手 1.2 秒就保存一次（防抖）。
// version 记"内容改过几次"、savedVersion 记"最后一次存成功时的版本"——
// 两者相等 = 没有新改动 = 不用发请求（这是和手动保存最大的不同点）。
const AUTO_SAVE_DELAY = 1200
const saveState = ref('idle')     // idle / pending / saving / saved / error
let saveTimer = null
let version = 0
let savedVersion = 0
let savingPromise = null          // 正在进行的保存（用来串行化并发请求）
let hydrating = true              // 编辑模式回填内容期间，不触发自动保存
let lastUploadErrorAt = 0         // 附件上传失败提示的节流时间

// 标一次"有改动"：版本 +1 并排一个防抖定时器
function markDirty() {
  version++
  saveState.value = 'pending'
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => { flushSave() }, AUTO_SAVE_DELAY)
}

// 只盯"手输字段"；选文件不走这里（acceptFile 里主动标），
// 避免保存成功后程序化清空 pickedFile 又触发一轮多余保存
watch([title, mode, tag, author, published, journal, note], () => {
  if (hydrating) return
  markDirty()
})

// 状态文字：固定三字、不带时间——写作时尽量察觉不到它的变化
const saveHint = computed(() => {
  if (saveState.value === 'saving') return '保存中'
  if (saveState.value === 'pending') return '未保存'
  if (saveState.value === 'saved') return '已保存'
  if (saveState.value === 'error') return '保存失败'
  return ''
})

function collectPayload() {
  return {
    title: title.value.trim(),
    mode: mode.value,
    tag: tag.value.trim(),
    author: author.value.trim(),
    published: published.value.trim(),
    journal: journal.value.trim(),
    note: note.value,
  }
}

// 立即保存（不等防抖）：自动保存的定时器、离开页面、点保存按钮 都走这里
async function flushSave() {
  if (savingPromise) { await savingPromise; return true }   // 等上一轮，避免并发打架
  clearTimeout(saveTimer)
  if (!canSave.value) return false
  // 没有新改动、也没有待传附件 → 不用保存
  if (recordId.value && version === savedVersion && !pickedFile.value) return true

  savingPromise = (async () => {
    saving.value = true
    saveState.value = 'saving'
    const v = version
    try {
      let id = recordId.value
      if (id) {
        await updateReading(id, collectPayload())
      } else {
        // 首次保存 = 创建：拿到 id 后把地址栏换成 /edit/:id，之后都走"更新"
        const res = await createReading(collectPayload())
        id = res.data.id
        recordId.value = id
        router.replace(`/edit/${id}`)
      }

      // 待传附件搭车上传（失败则保留，下次保存自动重试）
      if (pickedFile.value) {
        try {
          const up = await uploadReadingAttachment(id, pickedFile.value)
          attachment.value = up.data.attachment
          pickedFile.value = null
        } catch {
          if (Date.now() - lastUploadErrorAt > 3000) {
            lastUploadErrorAt = Date.now()
            toast.error('附件上传失败，将继续保留、稍后自动重试')
          }
        }
      }

      savedVersion = v
      // 保存期间又有新改动的话（version 变了），保持"未保存"，等下一轮定时器
      if (version === v) {
        saveState.value = 'saved'
      }
      return true
    } catch {
      saveState.value = 'error'
      toast.error('自动保存失败，请确认后端服务（8003）在运行')
      return false
    } finally {
      saving.value = false
    }
  })()

  try {
    return await savingPromise
  } finally {
    savingPromise = null
  }
}

// 按钮 = 立即保存（不等防抖）+ 去详情看结果
async function save() {
  const isEdit = !!recordId.value
  const ok = await flushSave()
  if (!ok) return
  toast.success(isEdit ? '已更新' : '笔记已创建')
  router.push(`/review/${recordId.value}`)
}

// 离开页面（切导航等）前把最后的改动补存上；不阻塞跳转
onBeforeRouteLeave(async () => {
  await flushSave()
})

// ---- 底部实时时钟：年月日 + 星期 + 时分秒（每秒走一格） ----
const now = ref(new Date())
let timer = null

onMounted(async () => {
  timer = setInterval(() => { now.value = new Date() }, 1000)

  // 编辑模式：把记录内容带入本页
  if (route.params.id) {
    const res = await getReading(route.params.id)
    if (res.data) {
      const r = res.data
      recordId.value = r.id
      title.value = r.title
      mode.value = r.mode
      tag.value = r.tag || ''
      author.value = r.author || ''
      published.value = r.published || ''
      journal.value = r.journal || ''
      note.value = r.note || ''
      attachment.value = r.attachment || ''
    }
  }

  // 标签候选：收集已有记录的标签（去重）
  const all = (await listReadings()).data
  tagOptions.value = [...new Set(all.map((r) => r.tag).filter(Boolean))]

  // 回填 + 拉候选都完成后，再放开自动保存（否则回填本身会被当成"改动"）
  await nextTick()
  hydrating = false
})
onUnmounted(() => {
  clearInterval(timer)
  clearTimeout(saveTimer)
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})

const clockText = computed(() => formatClock(now.value))
</script>

<template>
  <!-- grid 双列布局做动画：切泛读时左列 1fr → 0（连带 gap 消失），右列顺势滑向中央 -->
  <div
    class="h-screen grid p-4 transition-all duration-500 ease-in-out"
    :class="mode === 'close'
      ? 'grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-4'
      : 'grid-cols-[minmax(0,0fr)_minmax(0,1fr)] gap-0'"
  >
    <!-- 左：论文 / 截图（仅精读显示；收起时淡出并压缩到 0 宽）
         有文件直接内嵌显示（PDF 调浏览器阅读器、图片直接显示）方便对照翻阅；空着时点击/拖拽选文件 -->
    <div
      class="min-w-0 overflow-hidden transition-opacity duration-300"
      :class="mode === 'close' ? 'opacity-100' : 'opacity-0'"
    >
      <div
        class="h-full rounded-2xl border-2 relative overflow-hidden flex flex-col items-center justify-center transition-colors"
        :class="dragOver
          ? 'border-primary/60 bg-primary/10'
          : viewerSrc
            ? 'border-base-300 bg-base-100'
            : 'border-dashed border-base-300 bg-base-200/40 hover:border-primary/40 hover:bg-primary/5 cursor-pointer select-none'"
        @click="!viewerSrc && fileInput?.click()"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
      >
        <input
          ref="fileInput"
          type="file"
          class="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.gif,.webp"
          @change="onPick"
        />

        <!-- 有文件：内嵌显示 -->
        <template v-if="viewerSrc">
          <iframe
            v-if="!viewerIsImage"
            :src="viewerSrc"
            :title="displayFileName"
            class="w-full h-full border-0"
          ></iframe>
          <img
            v-else
            :src="viewerSrc"
            :alt="displayFileName"
            class="max-w-full max-h-full object-contain p-3 drop-shadow"
          />

          <!-- 悬浮：上传状态 + 替换 -->
          <div class="absolute top-3 right-3 flex items-center gap-2">
            <span v-if="pickedFile" class="badge badge-sm badge-ghost bg-base-100/90 shadow-sm">保存后上传</span>
            <button class="btn btn-xs bg-base-100/90 shadow-sm" @click.stop="fileInput?.click()">替换</button>
          </div>
        </template>

        <!-- 没文件：引导选择 -->
        <template v-else>
          <Upload class="w-10 h-10 text-base-content/30" />
          <div class="text-sm text-base-content/60">点击选择，或拖拽 PDF / 图片到这里</div>
        </template>
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

      <!-- 文献信息（选填）：作者 / 出版时间（手填 YYYY-MM）/ 期刊 / 分类标签（可输入或选已有） -->
      <div class="flex flex-wrap items-center gap-2">
        <span class="badge badge-ghost badge-sm text-base-content/50 shrink-0">选填</span>

        <label class="input input-sm flex-1 min-w-36">
          <User class="w-3.5 h-3.5 opacity-40" />
          <input v-model="author" class="grow" placeholder="作者" />
        </label>

        <label class="input input-sm flex-1 min-w-36">
          <Calendar class="w-3.5 h-3.5 opacity-40" />
          <input v-model="published" class="grow" placeholder="出版时间（如 2024-06）" />
        </label>

        <label class="input input-sm flex-1 min-w-36">
          <BookOpen class="w-3.5 h-3.5 opacity-40" />
          <input v-model="journal" class="grow" placeholder="期刊" />
        </label>

        <div class="relative flex-1 min-w-36">
          <label class="input input-sm w-full">
            <Tag class="w-3.5 h-3.5 opacity-40" />
            <input
              v-model="tag"
              class="grow"
              placeholder="分类标签（可自创或选已有）"
              @focus="tagOpen = true"
              @input="tagOpen = true"
              @blur="closeTagLater"
              @keydown.esc="tagOpen = false"
            />
          </label>
          <!-- 候选面板：由 Vue 控制显隐（浏览器原生 datalist 的下拉会被自动收走，不可靠） -->
          <div
            v-if="tagOpen && tagSuggestions.length"
            class="absolute z-30 left-0 right-0 top-full mt-1 rounded-xl bg-base-100 border border-base-300 shadow-lg p-1 max-h-44 overflow-auto"
          >
            <button
              v-for="t in tagSuggestions"
              :key="t"
              class="block w-full text-left px-2.5 py-1.5 rounded-lg text-sm hover:bg-base-200"
              @mousedown.prevent="pickTag(t)"
            >
              {{ t }}
            </button>
          </div>
        </div>
      </div>

      <MarkdownEditor v-model="note" />

      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-4 min-w-0">
          <!-- 精读记录：显示论文文件名，点击打开（原文件由后端提供） -->
          <a
            v-if="mode === 'close' && recordId && attachment"
            :href="`/api/readings/${recordId}/attachment`"
            target="_blank"
            rel="noopener"
            class="flex items-center gap-1.5 text-sm text-primary hover:underline min-w-0"
            :title="attachment"
          >
            <Paperclip class="w-4 h-4 shrink-0" />
            <span class="truncate">{{ attachment }}</span>
          </a>
          <div class="flex items-center gap-1.5 text-sm text-base-content/50 tabular-nums shrink-0">
            <Clock class="w-4 h-4" />
            {{ clockText }}
          </div>
        </div>
        <!-- 保存状态：固定三字、固定宽度的槽位——写作时几乎察觉不到它的变化 -->
        <div class="flex items-center gap-3 shrink-0">
          <span
            class="w-12 text-right text-xs transition-colors duration-300"
            :class="saveState === 'error' ? 'text-error' : 'text-base-content/30'"
          >
            {{ saveHint }}
          </span>
          <button class="btn btn-primary" :disabled="!canSave" @click="save">
            {{ recordId ? '更新' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
