<script setup>
import { ref } from 'vue'
import { Camera, Eye, RefreshCw, Trash2, Upload } from 'lucide-vue-next'

import PageHeader from '../components/PageHeader.vue'
import { usePolling } from '../composables/usePolling'
import { errText } from '../utils/error'
import { deleteShot, getShots, uploadShot } from '../api/rpa'

const shots = ref([])
const error = ref('')
const uploading = ref(false)
const preview = ref('')

async function load() {
  try {
    shots.value = (await getShots()).data
  } catch (e) {
    error.value = '截图列表加载失败：' + errText(e)
  }
}

usePolling(load, 10000)

async function onPick(e) {
  const files = [...(e.target.files || [])]
  if (!files.length) return
  uploading.value = true
  error.value = ''
  try {
    for (const file of files) await uploadShot(file)
    await load()
  } catch (err) {
    error.value = errText(err, '上传失败')
  } finally {
    uploading.value = false
    e.target.value = ''   // 清空，方便再选同一个文件
  }
}

async function remove(shot) {
  if (!confirm(`删除截图「${shot.name}」？`)) return
  try {
    await deleteShot(shot.name)
    await load()
  } catch (e) {
    error.value = errText(e, '删除失败')
  }
}

function fmtSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div class="p-6 space-y-6">
    <PageHeader title="截图资料库"
                desc="把金蝶 / OA 的页面截图传到这里——写单元的选择器时，AI 会读这些图来认清字段与按钮">
      <template #actions>
        <button class="btn btn-ghost btn-sm" @click="load"><RefreshCw :size="14" />刷新</button>
      </template>
    </PageHeader>

    <div v-if="error" class="alert alert-warning">
      <span class="text-sm">{{ error }}</span>
      <button class="btn btn-xs btn-ghost" @click="error = ''">✕</button>
    </div>

    <div class="card bg-base-100 shadow">
      <div class="card-body gap-4">
        <label class="border-2 border-dashed border-base-300 rounded-box p-6 flex flex-col items-center gap-2 cursor-pointer hover:border-primary/50">
          <Upload :size="20" class="text-base-content/40" />
          <span class="text-sm">{{ uploading ? '上传中…' : '点击选择截图（可多选）' }}</span>
          <span class="text-xs text-base-content/40">
            存在本机 rpa-agent/data/shots/ 下。命名建议带"系统-页面-序号"，例如 金蝶-供应商新增-1.png
          </span>
          <input type="file" multiple accept="image/*" class="hidden" @change="onPick" />
        </label>

        <div class="text-xs text-base-content/50">
          共 {{ shots.length }} 张。敏感信息（客户名、手机号、金额）传之前可以先打码，够 AI 认清字段结构就行。
        </div>

        <div v-if="shots.length" class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-5 gap-4">
          <div v-for="s in shots" :key="s.name" class="border border-base-300 rounded-box overflow-hidden">
            <img :src="s.url" alt="截图" class="w-full h-36 object-cover bg-base-200 cursor-pointer"
                 @click="preview = s.url" />
            <div class="p-2 space-y-1">
              <div class="text-xs truncate" :title="s.name">{{ s.name }}</div>
              <div class="text-xs text-base-content/40">{{ fmtSize(s.size) }} · {{ s.mtime.slice(5, 16) }}</div>
              <div class="flex gap-1">
                <button class="btn btn-xs btn-ghost" @click="preview = s.url"><Eye :size="12" />查看</button>
                <button class="btn btn-xs btn-ghost text-error" @click="remove(s)"><Trash2 :size="12" />删除</button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center text-base-content/40 py-10 flex flex-col items-center gap-2">
          <Camera :size="24" />
          <span class="text-sm">还没有截图</span>
        </div>
      </div>
    </div>

    <dialog class="modal" :class="preview && 'modal-open'">
      <div class="modal-box max-w-6xl">
        <img :src="preview" alt="截图" class="w-full rounded" />
        <div class="modal-action">
          <button class="btn btn-sm" @click="preview = ''">关闭</button>
        </div>
      </div>
    </dialog>
  </div>
</template>
