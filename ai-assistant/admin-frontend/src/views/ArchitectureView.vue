<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ArrowRight, ExternalLink, X } from 'lucide-vue-next'
import { getServices } from '../api/services'
import { getOverview } from '../api/admin'
import { listKnowledge, listMissed } from '../api/kb'
import { listReadings, listSources } from '../api/study'
import { CANVAS, CARD_W, CARD_H, GUARD_FRAME, ZONES, NODES, EDGES, JUNCTIONS } from '../data/architecture'
import { INTERFACE_GROUPS } from '../data/interfaces'
import { DATASTORES } from '../data/datastores'
import { AI_USAGES, AI_GUIDE } from '../data/aimodels'

// 架构图页：四种视角——
//   总体：卡片 = 服务（实时状态来自 manager），线 = 调用，大框 = manager 守护，虚线 = 规划
//   接口：按「调用方 → 被调方」分组的接口清单，点开看作用与链路
//   数据：各服务的数据库结构 + 实时数据量
//   AI：哪里用了 AI、用的什么模型、去哪里改
const services = ref([])
const managerDown = ref(false)
const selected = ref(null)      // 右滑详情里的节点
const view = ref('overall')     // overall 总体 / interface 接口 / data 数据 / ai AI
const selectedApi = ref(null)   // 右滑详情里的接口
let timer = null

async function refresh() {
  try {
    services.value = (await getServices()).services
    managerDown.value = false
  } catch {
    managerDown.value = true
  }
  if (view.value === 'data') loadCounts()
}

// ---- 数据视图：实时数据量 ----
const counts = ref({})   // { calls, knowledge, missed, readings, sources, attachments }

async function loadCounts() {
  const c = {}
  // 逐项容错：某个服务没起时该项留空（页面显示"—"），不影响其它
  try { c.calls = (await getOverview()).stats?.total_calls } catch { /* 调度器未起 */ }
  try {
    const k = await listKnowledge()
    c.knowledge = Array.isArray(k.data) ? k.data.length : k.total
  } catch { /* 知识库未起 */ }
  try {
    const m = await listMissed()
    c.missed = Array.isArray(m.data) ? m.data.length : m.total
  } catch { /* 知识库未起 */ }
  try {
    const r = await listReadings()
    c.readings = r.total
    c.attachments = (r.data || []).filter((x) => x.attachment).length
  } catch { /* 研读后端未起 */ }
  try { c.sources = (await listSources()).total } catch { /* 研读后端未起 */ }
  counts.value = c
}

watch(view, (v) => {
  if (v === 'data') loadCounts()
})

// 漂移检测：services.json（实时清单）与本地画法（NODES）名单对不上时，顶部提示去同步
const drift = computed(() => {
  if (!services.value.length) return null   // manager 未连接时不做判断
  const onDiagram = new Set(NODES.filter((n) => !n.planned && !n.unmanaged).map((n) => n.key))
  const inConfig = new Set(services.value.map((s) => s.name))
  const missingOnDiagram = services.value.filter((s) => !onDiagram.has(s.name)).map((s) => s.name)
  const missingInConfig = [...onDiagram].filter((k) => !inConfig.has(k))
  if (!missingOnDiagram.length && !missingInConfig.length) return null
  return { missingOnDiagram, missingInConfig }
})
onMounted(() => {
  refresh()
  timer = setInterval(refresh, 5000)
})
onUnmounted(() => clearInterval(timer))

const STATUS_META = {
  running: { dot: 'bg-success', text: '运行中', badge: 'badge-success' },
  starting: { dot: 'bg-warning', text: '启动中', badge: 'badge-warning' },
  stopped: { dot: 'bg-base-content/30', text: '已停止', badge: 'badge-ghost' },
  error: { dot: 'bg-error', text: '异常', badge: 'badge-error' },
  unknown: { dot: 'bg-base-content/20', text: '未知', badge: 'badge-ghost' },
  planned: { dot: 'bg-base-content/20', text: '规划中', badge: 'badge-ghost' },
}

// 合并：配置里的画法/说明 + manager 的实时数据
const nodes = computed(() =>
  NODES.map((n) => {
    const live = services.value.find((s) => s.name === n.key)
    return {
      ...n,
      cnName: n.cnName ?? live?.cn_name ?? n.key,
      sub: n.sub ?? (live ? `${n.key} · ${live.port}` : n.key),
      status: n.planned ? 'planned' : n.unmanaged ? 'running' : (live?.status ?? 'unknown'),
      enterUrl: live?.enter_url ?? '',
    }
  }),
)

function rectStyle(r) {
  return { left: `${r.x}px`, top: `${r.y}px`, width: `${r.w}px`, height: `${r.h}px` }
}

// 连线路径：默认"右中点 → 左中点"的直角折线（H-V-H）；points 可自定义拐点
function edgePath(e) {
  if (e.points) return `M ${e.points.map((p) => p.join(' ')).join(' L ')}`
  const a = nodes.value.find((n) => n.key === e.from)
  const b = nodes.value.find((n) => n.key === e.to)
  const x1 = a.x + CARD_W
  const y1 = a.y + CARD_H / 2
  const x2 = b.x
  const y2 = b.y + CARD_H / 2
  if (Math.abs(y1 - y2) < 1) return `M ${x1} ${y1} H ${x2}`
  const mx = (x1 + x2) / 2
  return `M ${x1} ${y1} H ${mx} V ${y2} H ${x2}`
}

function cardClass(n) {
  if (n.planned) return 'border-dashed border-base-content/25 bg-base-100/40 text-base-content/50 hover:border-base-content/50'
  if (n.unmanaged) return 'border-primary/40 bg-primary/5 hover:border-primary/70'
  return 'border-base-300 bg-base-100 hover:border-primary/60'
}

// 接口视图：方法徽章配色（组合方法/协议用默认 ghost）
const METHOD_META = {
  GET: 'badge-info',
  POST: 'badge-success',
  PUT: 'badge-warning',
  DELETE: 'badge-error',
}

function nameOf(key) {
  return nodes.value.find((n) => n.key === key)?.cnName ?? key
}

function openNode(n) {
  selectedApi.value = null
  selected.value = n
}

function openApi(group, item) {
  selected.value = null
  selectedApi.value = {
    ...item,
    from: group.fromKey,
    to: group.toKey,
    toLabel: group.toLabel,
    note: group.note,
    planned: group.planned,
  }
}
</script>

<template>
  <div class="p-6 space-y-4">
    <div class="flex items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold">架构图</h1>
        <p class="text-sm text-base-content/60 mt-1">
          {{ view === 'overall'
            ? '实线 = 调用 · 大框 = manager 守护 · 虚线 = 规划；点卡片看详情'
            : view === 'interface'
              ? '按「调用方 → 被调方」分组的接口清单，点任一接口看作用与链路'
              : view === 'data'
                ? '各服务的数据库结构与实时数据量（服务未启动时对应数字显示"—"）'
                : '集群里哪里用了 AI、用的什么模型、去哪里更改或新增（配置都在各服务的 .env）' }}
        </p>
      </div>
      <div class="join shrink-0">
        <button class="btn btn-sm join-item" :class="view === 'overall' ? 'btn-primary' : 'btn-ghost'" @click="view = 'overall'">
          总体
        </button>
        <button class="btn btn-sm join-item" :class="view === 'interface' ? 'btn-primary' : 'btn-ghost'" @click="view = 'interface'">
          接口
        </button>
        <button class="btn btn-sm join-item" :class="view === 'data' ? 'btn-primary' : 'btn-ghost'" @click="view = 'data'">
          数据
        </button>
        <button class="btn btn-sm join-item" :class="view === 'ai' ? 'btn-primary' : 'btn-ghost'" @click="view = 'ai'">
          AI
        </button>
      </div>
    </div>

    <div v-if="managerDown" role="alert" class="alert alert-warning">
      <span>manager（8002）未连接——状态数据不可用，当前显示静态架构</span>
    </div>

    <!-- 漂移检测：配置与画法名单不一致时提醒同步 -->
    <div v-if="drift" role="alert" class="alert alert-warning items-start">
      <div class="text-sm space-y-1">
        <div v-if="drift.missingOnDiagram.length">
          检测到未上图的服务：<span class="font-medium">{{ drift.missingOnDiagram.join('、') }}</span>
          —— 在 src/data/architecture.js 里补一条节点即可上卡片
        </div>
        <div v-if="drift.missingInConfig.length">
          架构图上有、但服务清单里对不上的：<span class="font-medium">{{ drift.missingInConfig.join('、') }}</span>
          —— 检查 manager/services.json 的 name 是否一致
        </div>
      </div>
    </div>

    <!-- 总体视图：结构关系 -->
    <div v-if="view === 'overall'" class="card bg-base-100 shadow">
      <div class="card-body">
        <div class="overflow-auto">
          <div class="relative" :style="{ width: CANVAS.w + 'px', height: CANVAS.h + 'px' }">
            <!-- 业务分区（浅色底） -->
            <div
              v-for="z in ZONES"
              :key="z.label"
              class="absolute rounded-2xl bg-base-200/50 border border-base-300"
              :style="rectStyle(z)"
            >
              <div class="absolute top-2 left-3 text-xs text-base-content/50">{{ z.label }}</div>
            </div>

            <!-- 大虚线框：manager 守护的全部进程（manager 卡片挂在框外下边缘） -->
            <div class="absolute rounded-3xl border-2 border-dashed border-base-content/20" :style="rectStyle(GUARD_FRAME)">
              <div class="absolute -top-2.5 left-4 px-2 text-xs text-base-content/40 bg-base-100 rounded">
                {{ GUARD_FRAME.label }}
              </div>
            </div>

            <!-- 连线层（SVG 在最底层之上、卡片之下） -->
            <svg class="absolute inset-0 pointer-events-none" :width="CANVAS.w" :height="CANVAS.h">
              <path
                v-for="(e, i) in EDGES"
                :key="i"
                :d="edgePath(e)"
                fill="none"
                stroke="currentColor"
                class="text-base-content/30"
                stroke-width="1.5"
                :stroke-dasharray="e.dashed ? '6 5' : ''"
              />
              <!-- 汇流点：多条线的汇集处 -->
              <circle
                v-for="(j, i) in JUNCTIONS"
                :key="'j' + i"
                :cx="j.x"
                :cy="j.y"
                r="4"
                fill="currentColor"
                class="text-base-content/40"
              />
            </svg>

            <!-- 节点卡片 -->
            <button
              v-for="n in nodes"
              :key="n.key"
              class="absolute rounded-xl border shadow-sm text-left px-3 py-2 transition-shadow hover:shadow-md"
              :class="cardClass(n)"
              :style="{ left: n.x + 'px', top: n.y + 'px', width: CARD_W + 'px', height: CARD_H + 'px' }"
              @click="openNode(n)"
            >
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full shrink-0" :class="STATUS_META[n.status]?.dot"></span>
                <span class="text-sm font-medium truncate">{{ n.cnName }}</span>
              </div>
              <div class="text-[11px] text-base-content/45 truncate">{{ n.sub }}</div>
            </button>
          </div>
        </div>

        <!-- 图例 -->
        <div class="flex flex-wrap items-center gap-5 mt-2 text-xs text-base-content/50">
          <span class="flex items-center gap-2"><svg width="34" height="8"><line x1="0" y1="4" x2="34" y2="4" stroke="currentColor" stroke-width="1.5" /></svg>调用</span>
          <span class="flex items-center gap-2"><svg width="34" height="8"><line x1="0" y1="4" x2="34" y2="4" stroke="currentColor" stroke-width="1.5" stroke-dasharray="6 5" /></svg>规划 / 未接入</span>
          <span class="flex items-center gap-2"><svg width="10" height="8"><circle cx="5" cy="4" r="3.5" fill="currentColor" /></svg>汇流点</span>
          <span class="flex items-center gap-2">
            <span class="inline-block w-8 h-4 rounded border-2 border-dashed border-base-content/30"></span>manager 守护范围
          </span>
          <span class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-success"></span>运行中</span>
          <span class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-error"></span>异常</span>
          <span class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-base-content/30"></span>停止 / 未知</span>
        </div>
      </div>
    </div>

    <!-- 接口视图：按「调用方 → 被调方」分组的接口清单 -->
    <div v-else-if="view === 'interface'" class="card bg-base-100 shadow">
      <div class="card-body space-y-7">
        <section v-for="(g, gi) in INTERFACE_GROUPS" :key="gi">
          <div class="flex flex-wrap items-center gap-2 mb-3">
            <span class="text-sm font-medium">{{ nameOf(g.fromKey) }}</span>
            <ArrowRight class="w-4 h-4 text-base-content/40" />
            <span class="text-sm font-medium">{{ g.toKey ? nameOf(g.toKey) : g.toLabel }}</span>
            <span v-if="g.note" class="text-xs text-base-content/40">· {{ g.note }}</span>
            <span class="ml-auto text-xs text-base-content/40 tabular-nums">{{ g.items.length }} 个接口</span>
          </div>
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-2">
            <button
              v-for="(api, ai) in g.items"
              :key="ai"
              class="text-left rounded-xl border px-3.5 py-2.5 transition-colors"
              :class="g.planned
                ? 'border-dashed border-base-content/25 hover:border-base-content/50'
                : 'border-base-300 hover:border-primary/60 hover:bg-primary/5'"
              @click="openApi(g, api)"
            >
              <div class="flex items-center gap-2 min-w-0">
                <span class="badge badge-sm shrink-0" :class="METHOD_META[api.method] || 'badge-ghost'">{{ api.method }}</span>
                <span class="font-mono text-xs truncate">{{ api.path }}</span>
              </div>
              <div class="text-xs text-base-content/55 mt-1.5 truncate">{{ api.desc }}</div>
            </button>
          </div>
        </section>
      </div>
    </div>

    <!-- 数据视图：各服务的数据库结构与实时数据量 -->
    <div v-else-if="view === 'data'" class="card bg-base-100 shadow">
      <div class="card-body space-y-5">
        <div v-for="d in DATASTORES" :key="d.name" class="rounded-2xl border border-base-300 p-4">
          <div class="flex flex-wrap items-center gap-2">
            <span class="font-mono text-sm font-medium">{{ d.name }}</span>
            <span class="badge badge-sm badge-ghost">{{ d.type }}</span>
            <span class="text-xs text-base-content/45">归属：{{ nameOf(d.ownerKey) }}</span>
          </div>

          <div class="mt-3 space-y-2">
            <div v-for="t in d.tables" :key="t.name" class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span class="font-mono text-xs text-base-content/70 shrink-0">{{ t.name }}</span>
              <span class="text-xs text-base-content/50 flex-1 min-w-64">{{ t.desc }}</span>
              <span
                v-if="t.live"
                class="badge badge-sm shrink-0"
                :class="counts[t.live] != null ? 'badge-primary badge-outline' : 'badge-ghost'"
              >
                {{ counts[t.live] != null ? counts[t.live] + ' 条' : '—' }}
              </span>
            </div>

            <div v-if="d.extra" class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span class="text-xs text-base-content/50 flex-1 min-w-64">{{ d.extra.text }}</span>
              <span
                class="badge badge-sm shrink-0"
                :class="counts[d.extra.live] != null ? 'badge-primary badge-outline' : 'badge-ghost'"
              >
                {{ counts[d.extra.live] != null ? counts[d.extra.live] + ' 个' : '—' }}
              </span>
            </div>
          </div>
        </div>

        <p class="text-xs text-base-content/40">
          数据量实时来自各服务接口（研读库经 /study 只读代理直连 8003）；表结构变化时同步改 src/data/datastores.js。
        </p>
      </div>
    </div>

    <!-- AI 视图：哪里用了 AI、用的什么模型、去哪里改 -->
    <div v-else class="card bg-base-100 shadow">
      <div class="card-body space-y-5">
        <div
          v-for="s in AI_USAGES"
          :key="s.ownerKey"
          class="rounded-2xl border p-4"
          :class="s.planned ? 'border-dashed border-base-content/25' : 'border-base-300'"
        >
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium">{{ nameOf(s.ownerKey) }}</span>
            <span v-if="s.planned" class="badge badge-sm badge-ghost">规划中</span>
          </div>
          <div class="mt-3 space-y-3">
            <div v-for="it in s.items" :key="it.task" class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span class="badge badge-sm badge-outline shrink-0">{{ it.task }}</span>
              <span class="text-sm shrink-0" :class="it.model === '—' ? 'text-base-content/40' : 'text-base-content/80'">
                {{ it.model }}
              </span>
              <span class="text-xs text-base-content/50 flex-1 min-w-64">{{ it.detail }}</span>
            </div>
          </div>
          <div class="text-xs text-base-content/40 mt-3">{{ s.config }}</div>
        </div>

        <!-- 更改 / 新增模型的操作指引 -->
        <div class="rounded-2xl bg-base-200/50 p-4">
          <div class="text-sm font-medium mb-3">更改 / 新增模型</div>
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-x-8 gap-y-3">
            <div v-for="g in AI_GUIDE" :key="g.title" class="text-xs leading-relaxed">
              <span class="font-medium text-base-content/70">{{ g.title }}：</span>
              <span class="text-base-content/55">{{ g.desc }}</span>
            </div>
          </div>
        </div>

        <p class="text-xs text-base-content/40">
          开发侧（不属于集群服务）：Claude Code 目前也接的 DeepSeek——通过环境变量 ANTHROPIC_BASE_URL / ANTHROPIC_MODEL 等配置，换模型改环境变量即可。
        </p>
      </div>
    </div>

    <!-- 右侧滑出详情 -->
    <Transition
      enter-active-class="transition-transform duration-300 ease-out"
      enter-from-class="translate-x-full"
      leave-active-class="transition-transform duration-200 ease-in"
      leave-to-class="translate-x-full"
    >
      <aside
        v-if="selected || selectedApi"
        class="fixed right-0 top-0 h-full w-80 bg-base-100 border-l border-base-300 shadow-2xl z-40 p-5 overflow-y-auto"
      >
        <!-- 服务卡片详情 -->
        <template v-if="selected">
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="text-lg font-bold">{{ selected.cnName }}</div>
            <div class="text-xs text-base-content/50 mt-0.5">{{ selected.sub }}</div>
          </div>
          <button class="btn btn-ghost btn-sm btn-circle" @click="selected = null; selectedApi = null">
            <X class="w-4 h-4" />
          </button>
        </div>

        <div class="mt-3">
          <span class="badge badge-sm" :class="STATUS_META[selected.status]?.badge">
            {{ STATUS_META[selected.status]?.text }}
          </span>
        </div>

        <div class="mt-5 space-y-4 text-sm">
          <div>
            <div class="text-xs text-base-content/40 mb-1">作用</div>
            <p>{{ selected.detail.role }}</p>
          </div>
          <template v-if="selected.detail.stack">
            <div>
              <div class="text-xs text-base-content/40 mb-1">技术栈</div>
              <p>{{ selected.detail.stack }}</p>
            </div>
          </template>
          <template v-if="selected.detail.db">
            <div>
              <div class="text-xs text-base-content/40 mb-1">数据库</div>
              <p>{{ selected.detail.db }}</p>
            </div>
          </template>
          <template v-if="selected.detail.deps">
            <div>
              <div class="text-xs text-base-content/40 mb-1">外部依赖</div>
              <p>{{ selected.detail.deps }}</p>
            </div>
          </template>
        </div>

        <div class="mt-6 flex gap-2">
          <a
            v-if="selected.enterUrl && selected.status === 'running'"
            class="btn btn-sm btn-primary"
            :href="selected.enterUrl"
            target="_blank"
            rel="noopener"
          >
            <ExternalLink class="w-4 h-4" />
            进入服务
          </a>
          <router-link
            v-if="!selected.planned && !selected.unmanaged"
            to="/services"
            class="btn btn-sm btn-outline"
          >
            去服务管理
          </router-link>
        </div>
        </template>

        <!-- 接口详情 -->
        <template v-else>
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="text-base font-bold">接口详情</div>
              <div class="text-xs text-base-content/50 mt-0.5">
                {{ nameOf(selectedApi.from) }} → {{ selectedApi.to ? nameOf(selectedApi.to) : selectedApi.toLabel }}
              </div>
            </div>
            <button class="btn btn-ghost btn-sm btn-circle" @click="selected = null; selectedApi = null">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="mt-3 flex items-center gap-2">
            <span class="badge badge-sm" :class="METHOD_META[selectedApi.method] || 'badge-ghost'">
              {{ selectedApi.method }}
            </span>
          </div>
          <div class="font-mono text-xs break-all mt-2 text-base-content/70">{{ selectedApi.path }}</div>

          <div class="mt-5 space-y-4 text-sm">
            <div>
              <div class="text-xs text-base-content/40 mb-1">作用</div>
              <p>{{ selectedApi.detail }}</p>
            </div>
            <div v-if="selectedApi.note">
              <div class="text-xs text-base-content/40 mb-1">所属链路</div>
              <p>{{ selectedApi.note }}</p>
            </div>
          </div>
        </template>
      </aside>
    </Transition>
  </div>
</template>
