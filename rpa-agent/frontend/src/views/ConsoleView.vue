<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  CheckCircle2, Circle, Loader2, MinusCircle, Play, Power, RefreshCw, XCircle,
} from 'lucide-vue-next'

import PageHeader from '../components/PageHeader.vue'
import { usePolling } from '../composables/usePolling'
import { errText } from '../utils/error'
import {
  cancelRun, closeBrowser, getBrowser, getRecentRuns, getRun, getUnits,
  killOrphans, openBrowser, runUnit, shotUrl, verifyUnit,
} from '../api/rpa'

// ---- 文案映射（状态 → 徽章样式 / 图标） ----
const RUN_STATUS = {
  queued: { text: '排队中', cls: 'badge-warning' },
  running: { text: '执行中', cls: 'badge-info' },
  success: { text: '成功', cls: 'badge-success' },
  failed: { text: '失败', cls: 'badge-error' },
  canceled: { text: '已取消', cls: 'badge-ghost' },
  interrupted: { text: '被打断', cls: 'badge-warning' },
}
const ENV_LABELS = { kingdee: '金蝶', oa: 'OA', local: '本地' }
const STEP_ICON = { success: CheckCircle2, failed: XCircle, running: Loader2, pending: Circle, skipped: MinusCircle }
const STEP_CLS = {
  success: 'text-success', failed: 'text-error', running: 'text-info',
  pending: 'text-base-content/30', skipped: 'text-base-content/30',
}

// ---- 状态 ----
const browser = ref(null)
const units = ref([])
const error = ref('')        // 操作触发的错误：下一次操作或刷新时清掉
const pollError = ref('')    // 轮询失败：恢复正常就自动消失（后端重启期间会闪一下，不该常驻）
const busy = ref('')                 // 正在执行的操作名（按钮转圈/禁用）
const selectedKey = ref('')
const inputText = ref('')
const run = ref(null)                // 当前展示的运行详情
const shotPreview = ref('')          // 弹窗里看的大图 URL
let fastTimer = null

const selectedUnit = computed(() => units.value.find((u) => u.key === selectedKey.value) || null)
const running = computed(() => !!run.value && ['queued', 'running'].includes(run.value.status))

// ---- 数据加载 ----
async function loadBrowser() {
  try {
    browser.value = (await getBrowser()).data
    pollError.value = ''
  } catch (e) {
    browser.value = null
    pollError.value = '连不上后端（rpa-agent:8004），' + errText(e)
  }
}

async function loadUnits() {
  try {
    units.value = (await getUnits()).data
    pollError.value = ''
  } catch (e) {
    pollError.value = '单元清单加载失败：' + errText(e)
  }
}

usePolling(async () => {
  await Promise.all([loadBrowser(), loadUnits()])
}, 5000)

// ---- 运行详情的快轮询（跑的时候 1 秒一问，结束就停） ----
function stopFastPoll() {
  if (fastTimer) {
    clearInterval(fastTimer)
    fastTimer = null
  }
}

function startFastPoll() {
  stopFastPoll()
  fastTimer = setInterval(async () => {
    try {
      const detail = (await getRun(run.value.id)).data
      run.value = detail
      if (!['queued', 'running'].includes(detail.status)) {
        stopFastPoll()
        await loadUnits()   // 结束时刷新清单里的"最近运行"
      }
    } catch (e) {
      stopFastPoll()
      error.value = '读取运行进度失败：' + errText(e)
    }
  }, 1000)
}

async function attachRun(runId) {
  run.value = (await getRun(runId)).data
  selectedKey.value = run.value.unit_key
  const unit = units.value.find((u) => u.key === run.value.unit_key)
  if (unit) inputText.value = JSON.stringify(run.value.inputs, null, 2)
  if (['queued', 'running'].includes(run.value.status)) startFastPoll()
}

onMounted(async () => {
  await loadUnits()
  // 页面刷新时可能有一个正在跑的运行，自动接上，别让它默默在后台跑
  try {
    const recent = (await getRecentRuns(1)).data
    if (recent.length && ['queued', 'running'].includes(recent[0].status)) await attachRun(recent[0].id)
  } catch (e) { /* 后端没起来就算了 */ }
})

onUnmounted(stopFastPoll)

// ---- 交互 ----
function templateOf(unit) {
  const obj = {}
  for (const f of unit.inputs) obj[f.key] = f.example || ''
  return obj
}

function selectUnit(unit) {
  selectedKey.value = unit.key
  inputText.value = JSON.stringify(templateOf(unit), null, 2)
  run.value = null
  stopFastPoll()
}

async function doOpen(url = '') {
  busy.value = 'browser'
  error.value = ''
  try {
    await openBrowser(url)
    await loadBrowser()
  } catch (e) {
    error.value = errText(e, '打开浏览器失败')
  } finally {
    busy.value = ''
  }
}

async function doClose() {
  busy.value = 'browser'
  try {
    await closeBrowser()
    await loadBrowser()
  } catch (e) {
    error.value = errText(e, '关闭浏览器失败')
  } finally {
    busy.value = ''
  }
}

async function doKill() {
  busy.value = 'browser'
  try {
    const res = await killOrphans()
    error.value = ''
    await loadBrowser()
    if (res.data) browser.value = res.data
  } catch (e) {
    error.value = errText(e, '清理残留进程失败')
  } finally {
    busy.value = ''
  }
}

async function doRun() {
  let inputs
  try {
    inputs = JSON.parse(inputText.value || '{}')
  } catch (e) {
    error.value = '输入不是合法 JSON：' + e.message
    return
  }
  busy.value = 'run'
  error.value = ''
  try {
    const res = await runUnit(selectedKey.value, inputs)
    await attachRun(res.data.run_id)
  } catch (e) {
    error.value = errText(e, '启动运行失败')
  } finally {
    busy.value = ''
  }
}

async function doCancel() {
  try {
    await cancelRun(run.value.id)
  } catch (e) {
    error.value = errText(e, '取消失败')
  }
}

async function doVerify() {
  if (!selectedUnit.value) return
  const next = !selectedUnit.value.verified
  try {
    await verifyUnit(selectedUnit.value.key, next)
    await loadUnits()
  } catch (e) {
    error.value = errText(e, '标记失败')
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <PageHeader title="执行台" desc="浏览器状态 → 选单元 → 填输入 → 运行 → 逐步看结果（单元 = 一条业务数据 × 一个操作环节）">
      <template #actions>
        <button class="btn btn-ghost btn-sm" @click="loadBrowser(), loadUnits()">
          <RefreshCw :size="14" />刷新
        </button>
      </template>
    </PageHeader>

    <div v-if="error || pollError" class="alert alert-warning">
      <span class="text-sm">{{ error || pollError }}</span>
      <button class="btn btn-xs btn-ghost" @click="error = '', (pollError = '')">✕</button>
    </div>

    <!-- 浏览器 -->
    <div class="card bg-base-100 shadow">
      <div class="card-body gap-4">
        <div class="flex items-center gap-3 flex-wrap">
          <h2 class="font-semibold">浏览器</h2>
          <span class="badge badge-sm" :class="browser?.launched ? 'badge-success' : 'badge-ghost'">
            {{ browser?.launched ? '已打开' : '未打开' }}
          </span>
          <span v-if="browser" class="badge badge-ghost badge-sm">通道 {{ browser.channel }}</span>
          <span v-if="browser?.busy" class="badge badge-warning badge-sm gap-1">
            <Loader2 :size="12" class="animate-spin" />{{ browser.current_job || '执行中' }}
          </span>
          <span v-if="browser?.busy && browser.heartbeat_ago != null" class="text-xs text-base-content/50">
            心跳 {{ browser.heartbeat_ago }} 秒前
          </span>
          <span v-if="browser?.profile_locked" class="badge badge-error badge-sm">用户目录被占用</span>
        </div>

        <p class="text-xs text-base-content/50 leading-relaxed">
          登录要过验证码，所以浏览器是<b>有界面的</b>：点「打开浏览器」后在里面人工登录一次，
          登录状态保存在本机（data/browser_profile），之后不用反复登。运行单元时你也能看着它在做什么。
        </p>

        <div v-if="browser?.last_error" class="alert alert-error py-2 text-xs">{{ browser.last_error }}</div>

        <div class="flex items-center gap-2 flex-wrap">
          <button class="btn btn-primary btn-sm" :disabled="!!busy" @click="doOpen('')">
            <Power :size="14" />打开浏览器
          </button>
          <button v-if="browser?.kingdee_url" class="btn btn-outline btn-sm" :disabled="!!busy"
                  @click="doOpen(browser.kingdee_url)">打开金蝶</button>
          <button v-if="browser?.oa_url" class="btn btn-outline btn-sm" :disabled="!!busy"
                  @click="doOpen(browser.oa_url)">打开 OA</button>
          <button class="btn btn-ghost btn-sm" :disabled="!!busy" @click="doClose">关闭浏览器</button>
          <button class="btn btn-ghost btn-sm text-warning" :disabled="!!busy" @click="doKill">
            强制结束残留进程
          </button>
        </div>
      </div>
    </div>

    <!-- 单元清单 -->
    <div class="card bg-base-100 shadow">
      <div class="card-body gap-3">
        <h2 class="font-semibold">
          单元清单
          <span class="text-xs text-base-content/50 font-normal ml-2">
            按叠加次序排；点一行选中它，然后在下面运行
          </span>
        </h2>
        <div class="overflow-x-auto">
          <table class="table table-sm">
            <thead>
              <tr>
                <th class="w-14">次序</th>
                <th>单元</th>
                <th class="w-20">环境</th>
                <th class="w-24">验证状态</th>
                <th class="w-40">最近运行</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in units" :key="u.key"
                  class="cursor-pointer hover:bg-base-200/60"
                  :class="u.key === selectedKey ? 'bg-primary/5' : ''"
                  @click="selectUnit(u)">
                <td class="text-base-content/60">{{ u.order }}</td>
                <td>
                  <div class="font-medium">{{ u.cn_name }}</div>
                  <div class="text-xs text-base-content/50">{{ u.desc }}</div>
                </td>
                <td><span class="badge badge-ghost badge-sm">{{ ENV_LABELS[u.env] || u.env }}</span></td>
                <td>
                  <span class="badge badge-sm" :class="u.verified ? 'badge-success' : 'badge-ghost'">
                    {{ u.verified ? '已跑通' : '待验证' }}
                  </span>
                </td>
                <td class="text-xs">
                  <template v-if="u.last_run">
                    <span class="badge badge-xs" :class="RUN_STATUS[u.last_run.status]?.cls">
                      {{ RUN_STATUS[u.last_run.status]?.text || u.last_run.status }}
                    </span>
                    <div class="text-base-content/40 mt-1">{{ u.last_run.created_at }}</div>
                  </template>
                  <span v-else class="text-base-content/30">还没跑过</span>
                </td>
              </tr>
              <tr v-if="!units.length">
                <td colspan="5" class="text-center text-base-content/40 py-8">暂无单元（后端没起来或 units/ 目录为空）</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 运行面板 -->
    <div v-if="selectedUnit" class="card bg-base-100 shadow">
      <div class="card-body gap-4">
        <div class="flex items-center gap-3 flex-wrap">
          <h2 class="font-semibold">运行：{{ selectedUnit.cn_name }}</h2>
          <span class="text-xs text-base-content/50">共 {{ selectedUnit.steps.length }} 步</span>
          <span class="text-xs text-base-content/40">
            步骤：{{ selectedUnit.steps.map((s) => s.cn_name).join(' → ') }}
          </span>
        </div>

        <div>
          <div class="text-sm mb-1">输入（JSON 文本框；按下面字段填）</div>
          <textarea v-model="inputText" rows="7" spellcheck="false"
                    class="textarea textarea-bordered w-full font-mono text-xs leading-relaxed"></textarea>
          <div class="text-xs text-base-content/50 mt-1 flex items-center gap-2 flex-wrap">
            <span>字段：</span>
            <span v-for="f in selectedUnit.inputs" :key="f.key">
              {{ f.label }}<span v-if="f.required" class="text-error">*</span>
            </span>
          </div>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <button class="btn btn-primary btn-sm" :disabled="running || !!busy" @click="doRun">
            <Play :size="14" />运行
          </button>
          <button v-if="running" class="btn btn-outline btn-error btn-sm" @click="doCancel">取消</button>
          <button class="btn btn-ghost btn-sm" :class="selectedUnit.verified ? 'text-success' : ''"
                  @click="doVerify">
            <CheckCircle2 :size="14" />
            {{ selectedUnit.verified ? '已标记跑通（点击取消标记）' : '标记为已跑通' }}
          </button>
          <span v-if="run" class="text-xs text-base-content/50 ml-2">
            运行 #{{ run.id }} · {{ RUN_STATUS[run.status]?.text || run.status }}
          </span>
        </div>

        <!-- 步骤 -->
        <div v-if="run" class="border border-base-300 rounded-box divide-y divide-base-200">
          <div v-for="s in run.steps" :key="s.idx"
               class="flex items-center gap-3 px-3 py-2 text-sm">
            <component :is="STEP_ICON[s.status] || Circle" :size="16"
                       :class="[STEP_CLS[s.status] || '', s.status === 'running' ? 'animate-spin' : '']" />
            <span class="w-10 text-xs text-base-content/40">{{ s.idx + 1 }}/{{ run.steps.length }}</span>
            <span :class="s.status === 'pending' ? 'text-base-content/40' : ''">{{ s.cn_name }}</span>
            <span v-if="s.duration_ms != null" class="text-xs text-base-content/40">{{ s.duration_ms }} ms</span>
            <span v-if="s.error" class="text-xs text-error truncate max-w-96">{{ s.error }}</span>
            <button v-if="s.screenshot" class="ml-auto shrink-0" @click="shotPreview = shotUrl(run.id, s.screenshot)">
              <img :src="shotUrl(run.id, s.screenshot)" alt="步骤截图"
                   class="h-10 w-16 object-cover rounded border border-base-300 hover:opacity-80" />
            </button>
          </div>
        </div>

        <div v-if="run?.error_msg" class="alert alert-error py-2 text-sm">失败原因：{{ run.error_msg }}</div>

        <!-- 日志 -->
        <div v-if="run">
          <div class="text-sm mb-1">运行日志</div>
          <pre class="bg-base-200 rounded-box p-3 text-xs max-h-56 overflow-auto whitespace-pre-wrap">{{ (run.logs || []).join('\n') || '（暂无日志）' }}</pre>
        </div>
      </div>
    </div>

    <!-- 截图大图 -->
    <dialog class="modal" :class="shotPreview && 'modal-open'">
      <div class="modal-box max-w-5xl">
        <img :src="shotPreview" alt="截图" class="w-full rounded" />
        <div class="modal-action">
          <button class="btn btn-sm" @click="shotPreview = ''">关闭</button>
        </div>
      </div>
    </dialog>
  </div>
</template>
