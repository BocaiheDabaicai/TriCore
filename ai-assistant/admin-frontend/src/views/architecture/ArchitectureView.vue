<script setup>
import { computed, ref } from 'vue'
import { getServices } from '../../api/services'
import { NODES } from '../../data/architecture'
import { usePolling } from '../../composables/usePolling'
import PageHeader from '../../components/PageHeader.vue'
import OverallPanel from './OverallPanel.vue'
import InterfacePanel from './InterfacePanel.vue'
import DataPanel from './DataPanel.vue'
import AiPanel from './AiPanel.vue'
import NodeDetails from './NodeDetails.vue'
import ApiDetails from './ApiDetails.vue'

// 架构图页：四种视角——
//   总体：卡片 = 服务（实时状态来自 manager），线 = 调用，大框 = manager 守护，虚线 = 规划
//   接口：按「调用方 → 被调方」分组的接口清单，点开看作用与链路
//   数据：各服务的数据库结构 + 实时数据量
//   AI：哪里用了 AI、用的什么模型、去哪里改
const VIEWS = [
  { key: 'overall', label: '总体', desc: '实线 = 调用 · 大框 = manager 守护 · 虚线 = 规划；点卡片看详情' },
  { key: 'interface', label: '接口', desc: '按「调用方 → 被调方」分组的接口清单，点任一接口看作用与链路' },
  { key: 'data', label: '数据', desc: '各服务的数据库结构与实时数据量（服务未启动时对应数字显示"—"）' },
  { key: 'ai', label: 'AI', desc: '集群里哪里用了 AI、用的什么模型、去哪里更改或新增（配置都在各服务的 .env）' },
]

const services = ref([])
const managerDown = ref(false)
const selected = ref(null)      // 右滑详情里的节点
const view = ref('overall')     // overall 总体 / interface 接口 / data 数据 / ai AI
const selectedApi = ref(null)   // 右滑详情里的接口

const currentDesc = computed(() => VIEWS.find((v) => v.key === view.value).desc)

async function refresh() {
  try {
    services.value = (await getServices()).services
    managerDown.value = false
  } catch {
    managerDown.value = true
  }
}
usePolling(refresh, 5000)

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

// 节点中文名查找表（给各视图面板显示用）——必须由 computed 派生，
// 普通对象原地改不会触发子组件更新（props 只追踪这一层引用）
const nameMap = computed(() => Object.fromEntries(nodes.value.map((n) => [n.key, n.cnName])))

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

function closeDrawer() {
  selected.value = null
  selectedApi.value = null
}
</script>

<template>
  <div class="p-6 space-y-4">
    <PageHeader title="架构图" :desc="currentDesc">
      <template #actions>
        <div class="join shrink-0">
          <button
            v-for="v in VIEWS"
            :key="v.key"
            class="btn btn-sm join-item"
            :class="view === v.key ? 'btn-primary' : 'btn-ghost'"
            @click="view = v.key"
          >
            {{ v.label }}
          </button>
        </div>
      </template>
    </PageHeader>

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

    <OverallPanel v-if="view === 'overall'" :nodes="nodes" @select-node="openNode" />
    <InterfacePanel v-else-if="view === 'interface'" :name-map="nameMap" @select-api="openApi" />
    <DataPanel v-else-if="view === 'data'" :name-map="nameMap" />
    <AiPanel v-else :name-map="nameMap" />

    <!-- 右侧滑出详情：外壳留在这里，内容按选中项切换（节点详情 / 接口详情） -->
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
        <NodeDetails v-if="selected" :node="selected" @close="closeDrawer" />
        <ApiDetails v-else-if="selectedApi" :api="selectedApi" :name-map="nameMap" @close="closeDrawer" />
      </aside>
    </Transition>
  </div>
</template>
