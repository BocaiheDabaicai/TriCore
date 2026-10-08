<script setup>
import { onMounted, ref } from 'vue'
import { clearMissed, createKnowledge, deleteMissed, draftSupplement, listMissed } from '../../api/kb'
import { useConfirmStore } from '../../stores/confirm'
import { useToastStore } from '../../stores/toast'
import { errText } from '../../utils/error'
import { KIND_LABELS } from '../../utils/meta'
import PageHeader from '../../components/PageHeader.vue'

// 未命中问题页：知识库答不上的问题清单（按被问次数排序）——知识库建设的输入
// 闭环：点「补充」→ AI 起草骨架（只搭框架，不编造具体规定）→ 人工填写 → 入库 → 自动删掉这条未命中
const items = ref([])
const loading = ref(false)
const error = ref('')

const confirmDialog = useConfirmStore()
const toast = useToastStore()

// 补充弹窗状态
const target = ref(null)          // 正在补充的未命中记录
const drafting = ref(false)       // AI 起草中
const draftFailed = ref(false)    // 起草失败（表单留空，可一键重试）
const saving = ref(false)
const modalError = ref('')
const form = ref({ title: '', kind: 'document', category: '', keywords: '', content: '' })

const KIND_OPTIONS = Object.entries(KIND_LABELS).map(([value, label]) => ({ value, label }))

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
  const ok = await confirmDialog.confirm({
    title: '删除这条未命中记录？',
    message: `「${item.question}」\n一般是对应知识已补充入库后才删除。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  try {
    await deleteMissed(item.id)
    toast.success('已删除')
    load()
  } catch (e) {
    toast.error('删除失败：' + errText(e))
  }
}

async function clearAll() {
  if (!items.value.length) return
  const n = items.value.length
  const ok = await confirmDialog.confirm({
    title: `清空全部 ${n} 条未命中记录？`,
    message: '清空后不可恢复。',
    confirmText: '清空',
    danger: true,
  })
  if (!ok) return
  try {
    await clearMissed()
    toast.success(`已清空 ${n} 条记录`)
    load()
  } catch (e) {
    toast.error('清空失败：' + errText(e))
  }
}

async function openSupplement(item) {
  target.value = item
  modalError.value = ''
  draftFailed.value = false
  form.value = { title: '', kind: 'document', category: '', keywords: '', content: '' }
  drafting.value = true
  try {
    const resp = await draftSupplement(item.id)
    if (resp.data) {
      form.value = {
        title: resp.data.title || '',
        kind: resp.data.kind || 'document',
        category: resp.data.category || '',
        keywords: resp.data.keywords || '',
        content: resp.data.content || '',
      }
    } else {
      draftFailed.value = true
      modalError.value = resp.message || 'AI 起草失败，请手工填写'
    }
  } catch (e) {
    // 起草失败不阻断：留空表单让用户手工写，或点「重新起草」再试
    draftFailed.value = true
    modalError.value = 'AI 起草失败（' + errText(e) + '），请手工填写'
  } finally {
    drafting.value = false
  }
}

async function save() {
  if (!form.value.title.trim() || !form.value.content.trim()) {
    modalError.value = '标题和正文都不能为空'
    return
  }
  // 骨架里还留着占位说明没填完，入库前确认一次（避免把没写完的资料当正式制度存进去）
  if (form.value.content.includes('待补充')) {
    const ok = await confirmDialog.confirm({
      title: '正文里还有「待补充」占位',
      message: '确定直接入库？没填实的内容会被当成正式制度回答给员工。',
      confirmText: '直接入库',
      danger: true,
    })
    if (!ok) return
  }

  saving.value = true
  modalError.value = ''
  try {
    const created = await createKnowledge({
      title: form.value.title.trim(),
      category: form.value.category.trim() || '未分类',
      kind: form.value.kind,
      content: form.value.content.trim(),
      keywords: form.value.keywords.trim() || null,
    })
    if (!created.data) {
      modalError.value = created.message || '入库失败'
      return
    }
    // 知识已入库 → 删掉这条未命中（失败也不回滚：记录多留一条，人工删即可）
    await deleteMissed(target.value.id)
    const title = created.data.title
    target.value = null
    toast.success(`「${title}」已入库，对应的未命中记录已删除`)
    load()
  } catch (e) {
    modalError.value = '保存失败：' + errText(e)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="p-6 space-y-6">
    <PageHeader title="未命中问题" desc="用户问什么没答上，就是该往知识库补什么——点「补充」由 AI 起草骨架，人工填完后入库" />

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
                <td class="space-x-2">
                  <button class="btn btn-primary btn-outline btn-xs" @click="openSupplement(item)">补充</button>
                  <button class="btn btn-error btn-outline btn-xs" @click="remove(item)">删除</button>
                </td>
              </tr>
              <!-- 首次加载显示骨架（与「暂无」区分开，避免被误读成真没有） -->
              <template v-if="loading && !items.length">
                <tr v-for="i in 4" :key="'sk' + i">
                  <td><div class="skeleton h-4 w-72 max-w-full"></div></td>
                  <td><div class="skeleton h-4 w-12"></div></td>
                  <td><div class="skeleton h-4 w-28"></div></td>
                  <td><div class="skeleton h-4 w-20"></div></td>
                </tr>
              </template>
              <tr v-if="!items.length && !loading">
                <td colspan="4" class="text-center text-base-content/40 py-12">暂无未命中问题</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 补充知识弹窗：AI 起草只搭骨架，正文要点由人工填实 -->
    <dialog class="modal" :class="target && 'modal-open'">
      <div class="modal-box max-w-2xl">
        <h3 class="font-bold text-lg mb-1">补充知识</h3>
        <p class="text-xs text-base-content/60 mb-3">
          未命中问题：<span class="text-base-content/80">{{ target?.question }}</span>
        </p>

        <div v-if="drafting" class="flex items-center gap-2 py-10 text-sm text-base-content/70">
          <span class="loading loading-spinner loading-sm"></span>
          AI 正在起草骨架（只列要点、不编造具体规定）…
        </div>

        <template v-else>
          <div class="grid grid-cols-2 gap-3">
            <label class="form-control col-span-2">
              <span class="label-text text-xs mb-1">标题</span>
              <input v-model="form.title" class="input input-bordered input-sm w-full" placeholder="制度 / 文档标题" />
            </label>
            <label class="form-control">
              <span class="label-text text-xs mb-1">知识类型</span>
              <select v-model="form.kind" class="select select-bordered select-sm w-full">
                <option v-for="k in KIND_OPTIONS" :key="k.value" :value="k.value">{{ k.label }}</option>
              </select>
            </label>
            <label class="form-control">
              <span class="label-text text-xs mb-1">业务分类</span>
              <input v-model="form.category" class="input input-bordered input-sm w-full" placeholder="如：人力、财务" />
            </label>
            <label class="form-control col-span-2">
              <span class="label-text text-xs mb-1">关键词（顿号分隔，宽度查询的目录索引）</span>
              <input v-model="form.keywords" class="input input-bordered input-sm w-full" placeholder="如：住宿、申请、押金" />
            </label>
            <label class="form-control col-span-2">
              <span class="label-text text-xs mb-1">正文（【待补充】处请填实后再入库）</span>
              <textarea v-model="form.content" rows="12" class="textarea textarea-bordered w-full text-sm leading-relaxed"></textarea>
            </label>
          </div>
          <p class="text-xs text-base-content/50 mt-2">
            AI 不知道公司的真实规定，骨架里的数字、标准、流程都需要人工填实——写错的资料会被当成正式制度回答给员工。
          </p>
        </template>

        <div v-if="modalError" role="alert" class="alert alert-warning text-sm mt-3">{{ modalError }}</div>

        <div class="modal-action">
          <button v-if="draftFailed && !drafting" class="btn btn-outline btn-sm" @click="openSupplement(target)">重新起草</button>
          <button class="btn btn-sm" @click="target = null">取消</button>
          <button class="btn btn-primary btn-sm" :disabled="drafting || saving" @click="save">
            {{ saving ? '保存中…' : '保存并入库' }}
          </button>
        </div>
      </div>
    </dialog>
  </div>
</template>
