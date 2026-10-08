<script setup>
import { computed, ref } from 'vue'
import { uploadKnowledge } from '../../api/kb'
import { errText } from '../../utils/error'
import { KIND_LABELS } from '../../utils/meta'
import PageHeader from '../../components/PageHeader.vue'

// 上传知识页：文件 → 解析 → AI 识别分类 → 入库 → 自动向量化（经调度器代理转发 kb-agent）
// 多选批量上传：后端是单文件接口，批量在前端做并发（服务端是同步路由 + 线程池，每个文件独立处理）
const CONCURRENCY = 3

const files = ref([])      // 队列：{ id, file, phase: pending|uploading|processing|done|error, percent, message }
const kind = ref('')       // '' = 自动识别；policy/document/workflow 手动覆盖
const category = ref('')   // 业务分类，不填则由 AI 拟定
let nextId = 1

// 类型下拉：首项"自动识别" + 中文名映射统一来自 utils/meta
const KINDS = [
  { value: '', label: '自动识别' },
  ...Object.entries(KIND_LABELS).map(([value, label]) => ({ value, label })),
]

const pending = computed(() => files.value.filter((i) => i.phase === 'pending'))
const uploading = computed(() => files.value.some((i) => i.phase === 'uploading' || i.phase === 'processing'))
const finished = computed(() => files.value.filter((i) => i.phase === 'done' || i.phase === 'error'))
const doneCount = computed(() => files.value.filter((i) => i.phase === 'done').length)

const STATUS_TEXT = { pending: '等待', uploading: '上传中', processing: '处理中', done: '成功', error: '失败' }
const STATUS_BADGE = { pending: 'badge-ghost', uploading: 'badge-info', processing: 'badge-info', done: 'badge-success', error: 'badge-error' }
const BAR_CLASS = { pending: '', uploading: 'progress-info', processing: 'progress-info', done: 'progress-success', error: 'progress-error' }

function statusText(item) {
  return item.phase === 'uploading' ? `上传中 ${item.percent}%` : STATUS_TEXT[item.phase]
}

function barValue(item) {
  if (item.phase === 'pending') return 0
  if (item.phase === 'done') return 100
  if (item.phase === 'error') return item.percent || 100   // 失败也把进度条画满，一眼看出这条没成
  return item.percent
}

function fmtSize(bytes) {
  return bytes >= 1024 * 1024
    ? (bytes / 1024 / 1024).toFixed(1) + ' MB'
    : Math.max(1, Math.round(bytes / 1024)) + ' KB'
}

// 打开选择框前先清空 value：重复选同一文件也能触发 change
// （选中后不清空，让原生控件正常显示已选文件名 / 数量）
function onPick(e) {
  e.target.value = ''
}

// 追加到队列；重复选中同一个文件只保留一份（已上传过的同理，避免误建重复知识）
function onSelect(e) {
  for (const f of e.target.files) {
    const dup = files.value.some((i) => i.file.name === f.name && i.file.size === f.size)
    if (!dup) files.value.push({ id: nextId++, file: f, phase: 'pending', percent: 0, message: '' })
  }
}

function removeItem(id) {
  files.value = files.value.filter((i) => i.id !== id)
}

function clearFinished() {
  files.value = files.value.filter((i) => i.phase === 'pending' || i.phase === 'uploading' || i.phase === 'processing')
}

async function uploadOne(item) {
  item.phase = 'uploading'
  item.percent = 0
  try {
    const resp = await uploadKnowledge(item.file, {
      kind: kind.value,
      category: category.value,
      // 传输进度（转完即 100%）——之后的解析 / 分类 / 向量化在服务端，只能显示"处理中"
      onProgress: (ratio) => {
        item.percent = Math.round(ratio * 100)
        if (ratio >= 1) item.phase = 'processing'
      },
    })
    if (resp.data) {
      item.phase = 'done'
      item.message = `${KIND_LABELS[resp.data.kind] || resp.data.kind} · ${resp.data.category}`
    } else {
      item.phase = 'error'
      item.message = resp.message || '入库失败'
    }
  } catch (e) {
    item.phase = 'error'
    item.message = errText(e)
  }
}

// 并发池：CONCURRENCY 个 worker 从同一个队列依次取任务，全部跑完才返回
async function upload() {
  if (!pending.value.length || uploading.value) return
  const queue = [...pending.value]
  let cursor = 0
  const worker = async () => {
    while (cursor < queue.length) await uploadOne(queue[cursor++])
  }
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, queue.length) }, worker))
}
</script>

<template>
  <div class="p-6 space-y-6">
    <PageHeader title="上传知识" desc="支持多选批量上传；文件自动解析、识别分类、入库并向量化，立即可问答" />

    <div class="card bg-base-100 shadow">
      <div class="card-body gap-4">
        <input
          type="file"
          multiple
          accept=".txt,.md,.pdf,.docx,.png,.jpg,.jpeg,.webp"
          class="file-input file-input-bordered w-full"
          @click="onPick"
          @change="onSelect"
        />

        <!-- 类型与分类固定一行：前者不收缩，后者占满剩余宽度 -->
        <div class="flex items-center gap-6 text-sm">
          <label class="flex items-center gap-2 shrink-0">
            知识类型
            <select v-model="kind" class="select select-bordered select-sm w-32">
              <option v-for="k in KINDS" :key="k.value" :value="k.value">{{ k.label }}</option>
            </select>
          </label>
          <label class="flex items-center gap-2 flex-1 min-w-0">
            业务分类
            <input v-model="category" class="input input-bordered input-sm flex-1" placeholder="不填则由 AI 拟定" />
          </label>
        </div>

        <div class="flex items-center gap-3">
          <button class="btn btn-primary" :disabled="!pending.length || uploading" @click="upload">
            {{ uploading ? '上传中…' : pending.length ? `上传（${pending.length}）` : '上传' }}
          </button>
          <button v-if="finished.length" class="btn btn-ghost" @click="clearFinished">清空已结束</button>
          <span v-if="files.length" class="text-xs text-base-content/60">
            共 {{ files.length }} 个文件<template v-if="doneCount">，已成功 {{ doneCount }}</template>
          </span>
        </div>

        <ul v-if="files.length" class="border-t border-base-200 text-sm">
          <li
            v-for="item in files"
            :key="item.id"
            class="flex items-center gap-3 border-b border-base-200 py-2 last:border-b-0"
          >
            <span class="flex-1 min-w-0 truncate" :title="item.file.name">{{ item.file.name }}</span>
            <span class="w-14 shrink-0 text-right text-xs text-base-content/50">{{ fmtSize(item.file.size) }}</span>
            <!-- 进度条：传输阶段是真实百分比；服务端处理阶段（解析/分类/向量化）无法上报，用条纹动画 -->
            <progress
              v-if="item.phase === 'processing'"
              class="progress progress-info w-24 shrink-0"
            ></progress>
            <progress
              v-else
              class="progress w-24 shrink-0"
              :class="BAR_CLASS[item.phase]"
              :value="barValue(item)"
              max="100"
            ></progress>
            <span class="w-24 shrink-0 justify-center badge badge-sm" :class="STATUS_BADGE[item.phase]">
              {{ statusText(item) }}
            </span>
            <span v-if="item.message" class="max-w-56 shrink-0 truncate text-xs text-base-content/60" :title="item.message">
              {{ item.message }}
            </span>
            <button
              class="btn btn-ghost btn-xs shrink-0"
              :disabled="item.phase === 'uploading' || item.phase === 'processing'"
              @click="removeItem(item.id)"
            >
              移除
            </button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
