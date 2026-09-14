<script setup>
import { ref } from 'vue'
import { getOverview } from '../../api/admin'
import { listKnowledge, listMissed } from '../../api/kb'
import { listReadings, listSources } from '../../api/study'
import { DATASTORES } from '../../data/datastores'
import { usePolling } from '../../composables/usePolling'

// 数据视图：各服务的数据库结构与实时数据量（挂载时先拉一次，之后每 5 秒跟着刷新）
defineProps({
  nameMap: { type: Object, required: true },
})

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

usePolling(loadCounts)
</script>

<template>
  <div class="card bg-base-100 shadow">
    <div class="card-body space-y-5">
      <div v-for="d in DATASTORES" :key="d.name" class="rounded-2xl border border-base-300 p-4">
        <div class="flex flex-wrap items-center gap-2">
          <span class="font-mono text-sm font-medium">{{ d.name }}</span>
          <span class="badge badge-sm badge-ghost">{{ d.type }}</span>
          <span class="text-xs text-base-content/45">归属：{{ nameMap[d.ownerKey] ?? d.ownerKey }}</span>
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
</template>
