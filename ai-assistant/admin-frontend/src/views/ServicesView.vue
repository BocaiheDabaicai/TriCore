<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { getLogs, getServices, restartService, startAll, startService, stopAll, stopService } from '../api/services'

// 服务管理页：状态来自 manager（8002，经 /ops 代理直连）
const services = ref([])
const error = ref('')
const busy = ref('')        // 正在操作的服务名（按钮 loading）
const logTarget = ref(null) // 日志弹窗显示的服务名
const logContent = ref('')

let timer = null

const STATUS_META = {
  running: { badge: 'badge-success', text: '运行中' },
  starting: { badge: 'badge-warning', text: '启动中' },
  stopped: { badge: 'badge-ghost', text: '已停止' },
  error: { badge: 'badge-error', text: '异常' },
}

async function refresh() {
  try {
    services.value = (await getServices()).services
    error.value = ''
  } catch (e) {
    error.value = 'manager（8002）未连接，请先启动 manager 服务'
  }
}

async function operate(name, action) {
  busy.value = name
  try {
    await action(name)
  } catch (e) {
    error.value = e.response?.data?.detail || `${name} 操作失败`
  } finally {
    busy.value = ''
    await refresh()
  }
}

async function runAll(action) {
  try {
    await action()
  } catch (e) {
    error.value = e.response?.data?.detail || '操作失败'
  } finally {
    await refresh()
  }
}

async function openLogs(name) {
  logTarget.value = name
  logContent.value = ''
  const res = await getLogs(name)
  logContent.value = res.lines.join('\n') || '（暂无日志）'
}

function fmtUptime(seconds) {
  if (seconds == null) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h) return `${h} 小时 ${m} 分`
  if (m) return `${m} 分 ${s} 秒`
  return `${s} 秒`
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 5000)   // 与 manager 探活周期一致
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-end justify-between">
      <div>
        <h1 class="text-2xl font-bold">服务管理</h1>
        <p class="text-sm text-base-content/60 mt-1">各 Agent 服务的启动、停止与运行状态（manager 8002）</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-outline" @click="refresh()">刷新</button>
        <button class="btn btn-sm btn-primary" @click="runAll(startAll)">全部启动</button>
        <button class="btn btn-sm btn-outline btn-error" @click="runAll(stopAll)">全部停止</button>
      </div>
    </div>

    <div v-if="error" role="alert" class="alert alert-warning">
      <button class="btn btn-xs btn-ghost" @click="error = ''">✕</button>
      <span>{{ error }}</span>
    </div>

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>服务</th>
                <th>端口</th>
                <th>状态</th>
                <th>PID</th>
                <th>运行时长</th>
                <th>自动重启次数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in services" :key="s.name">
                <td class="font-medium">{{ s.name }}</td>
                <td class="font-mono text-xs">{{ s.port }}</td>
                <td>
                  <span class="badge badge-sm" :class="STATUS_META[s.status]?.badge">
                    {{ STATUS_META[s.status]?.text }}
                  </span>
                </td>
                <td class="font-mono text-xs">{{ s.pid ?? '—' }}</td>
                <td class="text-xs">{{ fmtUptime(s.uptime_seconds) }}</td>
                <td class="text-xs">{{ s.restarts }}</td>
                <td>
                  <div class="flex gap-1">
                    <button
                      class="btn btn-xs"
                      :disabled="busy === s.name || s.status === 'running' || s.status === 'starting'"
                      @click="operate(s.name, startService)"
                    >
                      <span v-if="busy === s.name" class="loading loading-spinner loading-xs"></span>
                      启动
                    </button>
                    <button
                      class="btn btn-xs"
                      :disabled="busy === s.name || s.status === 'stopped'"
                      @click="operate(s.name, stopService)"
                    >
                      停止
                    </button>
                    <button class="btn btn-xs" :disabled="busy === s.name" @click="operate(s.name, restartService)">
                      重启
                    </button>
                    <button class="btn btn-xs btn-ghost" @click="openLogs(s.name)">日志</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!services.length">
                <td colspan="7" class="text-center text-base-content/40 py-8">manager 未返回服务列表</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 日志弹窗 -->
    <dialog :class="['modal', logTarget && 'modal-open']">
      <div class="modal-box max-w-3xl">
        <h3 class="font-bold text-lg mb-3">{{ logTarget }} · 运行日志</h3>
        <pre class="bg-base-200 rounded-box p-4 text-xs max-h-[60vh] overflow-auto whitespace-pre-wrap">{{ logContent }}</pre>
        <div class="modal-action">
          <button class="btn btn-sm" @click="logTarget = null">关闭</button>
        </div>
      </div>
    </dialog>
  </div>
</template>
