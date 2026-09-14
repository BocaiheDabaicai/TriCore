<script setup>
import { ref } from 'vue'
import { uploadKnowledge } from '../../api/kb'
import { errText } from '../../utils/error'
import { KIND_LABELS } from '../../utils/meta'
import PageHeader from '../../components/PageHeader.vue'

// 上传知识页：文件 → 解析 → AI 识别分类 → 入库 → 自动向量化（经调度器代理转发 kb-agent）
const fileInput = ref(null)
const file = ref(null)
const kind = ref('')        // '' = 自动识别；policy/document/workflow 手动覆盖
const category = ref('')    // 业务分类，不填则由 AI 拟定
const uploading = ref(false)
const result = ref(null)    // { ok, text }

// 类型下拉：首项"自动识别" + 中文名映射统一来自 utils/meta
const KINDS = [
  { value: '', label: '自动识别' },
  ...Object.entries(KIND_LABELS).map(([value, label]) => ({ value, label })),
]

function onFile(e) {
  file.value = e.target.files[0] || null
}

async function upload() {
  if (!file.value || uploading.value) return
  uploading.value = true
  result.value = null
  try {
    const resp = await uploadKnowledge(file.value, { kind: kind.value, category: category.value })
    if (resp.data) {
      result.value = { ok: true, text: `「${resp.data.title}」上传成功（类型：${resp.data.kind}，分类：${resp.data.category}）` }
      file.value = null
      category.value = ''
      fileInput.value.value = ''   // 清空 input 才能重复选同一个文件
    } else {
      result.value = { ok: false, text: resp.message }
    }
  } catch (e) {
    result.value = { ok: false, text: '上传失败：' + errText(e) }
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <PageHeader title="上传知识" desc="文件上传后自动解析、识别分类、入库并向量化，立即可问答" />

    <div class="card bg-base-100 shadow">
      <div class="card-body gap-4">
        <input
          ref="fileInput"
          type="file"
          accept=".txt,.md,.pdf,.docx"
          class="file-input file-input-bordered w-full"
          @change="onFile"
        />

        <div class="flex flex-wrap gap-4 text-sm">
          <label class="flex items-center gap-2">
            知识类型
            <select v-model="kind" class="select select-bordered select-sm">
              <option v-for="k in KINDS" :key="k.value" :value="k.value">{{ k.label }}</option>
            </select>
          </label>
          <label class="flex items-center gap-2">
            业务分类
            <input v-model="category" class="input input-bordered input-sm" placeholder="不填则由 AI 拟定" />
          </label>
        </div>

        <div class="flex items-center gap-3">
          <button class="btn btn-primary" :disabled="!file || uploading" @click="upload">
            {{ uploading ? '上传中…' : '上传' }}
          </button>
          <span v-if="file" class="text-xs text-base-content/60">{{ file.name }}</span>
        </div>

        <div v-if="result" role="alert" class="alert text-sm" :class="result.ok ? 'alert-success' : 'alert-error'">
          {{ result.text }}
        </div>
      </div>
    </div>
  </div>
</template>
