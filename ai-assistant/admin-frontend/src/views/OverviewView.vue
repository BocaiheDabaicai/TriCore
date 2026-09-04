<script setup>
import { computed, onMounted, ref } from 'vue'
import { getCalls, getOverview } from '../api/admin'

// 总览页：各 Agent 在线状态 + 调度器调用统计（数据来自 ai-assistant 的 calls 表）
const overview = ref(null)
const calls = ref([])
const error = ref('')

const SOURCE_LABELS = { knowledge: 'kb-agent', general: '兜底对话', none: '未配置 LLM' }
const STATUS_META = {
  online: { badge: 'badge-success', text: '在线' },
  offline: { badge: 'badge-error', text: '离线' },
  planning: { badge: 'badge-ghost', text: '规划中' },
}

// 知识问答成功率 = 由 kb-agent 真正接住的 / 意图为知识问答的
const successRate = computed(() => {
  const s = overview.value?.stats
  if (!s || !s.knowledge_calls) return '—'
  return ((s.success_calls / s.knowledge_calls) * 100).toFixed(1) + '%'
})

function fmtDuration(ms) {
  return ms >= 1000 ? (ms / 1000).toFixed(1) + ' s' : ms + ' ms'
}

onMounted(async () => {
  try {
    overview.value = await getOverview()
    calls.value = (await getCalls(20)).data
  } catch (e) {
    error.value = '调度服务未连接，请先启动 ai-assistant（8001）'
  }
})
</script>

<template>
  <div class="p-6 space-y-6">
    <div>
      <h1 class="text-2xl font-bold">总览</h1>
      <p class="text-sm text-base-content/60 mt-1">各 Agent 在线状态与调度调用统计</p>
    </div>

    <div v-if="error" role="alert" class="alert alert-warning">{{ error }}</div>

    <template v-if="overview">
      <!-- 调用统计 -->
      <div class="stats stats-vertical lg:stats-horizontal shadow w-full bg-base-100">
        <div class="stat">
          <div class="stat-title">总调用次数</div>
          <div class="stat-value text-2xl">{{ overview.stats.total_calls }}</div>
        </div>
        <div class="stat">
          <div class="stat-title">知识问答成功率</div>
          <div class="stat-value text-2xl">{{ successRate }}</div>
          <div class="stat-desc text-xs">kb-agent 接住 / 知识类问题</div>
        </div>
        <div class="stat">
          <div class="stat-title">降级次数</div>
          <div class="stat-value text-2xl">{{ overview.stats.degraded_calls }}</div>
          <div class="stat-desc text-xs">想走 Agent 但不可用，兜底回答</div>
        </div>
        <div class="stat">
          <div class="stat-title">平均耗时</div>
          <div class="stat-value text-2xl">
            {{ overview.stats.avg_duration_ms }}<span class="text-sm font-normal"> ms</span>
          </div>
        </div>
      </div>

      <!-- Agent 在线状态 -->
      <div class="card bg-base-100 shadow">
        <div class="card-body">
          <h2 class="card-title text-base">Agent 状态</h2>
          <div class="grid grid-cols-2 xl:grid-cols-4 gap-4">
            <div v-for="a in overview.agents" :key="a.name" class="rounded-box border border-base-300 p-4">
              <div class="flex items-center justify-between gap-2">
                <span class="font-mono text-sm">{{ a.name }}</span>
                <span class="badge badge-sm" :class="STATUS_META[a.status]?.badge">{{ STATUS_META[a.status]?.text }}</span>
              </div>
              <p class="text-xs text-base-content/60 mt-2">{{ a.duty }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近调用记录 -->
      <div class="card bg-base-100 shadow">
        <div class="card-body">
          <h2 class="card-title text-base">最近调用记录</h2>
          <div class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>问题</th>
                  <th>意图</th>
                  <th>实际回答</th>
                  <th>耗时</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in calls" :key="c.id">
                  <td class="whitespace-nowrap text-xs">{{ c.created_at }}</td>
                  <td class="max-w-64 truncate" :title="c.question">{{ c.question }}</td>
                  <td class="text-xs">{{ c.intent_agent }}</td>
                  <td class="text-xs">{{ SOURCE_LABELS[c.answer_source] || c.answer_source }}</td>
                  <td class="text-xs">{{ fmtDuration(c.duration_ms) }}</td>
                  <td><span v-if="c.degraded" class="badge badge-warning badge-xs">降级</span></td>
                </tr>
                <tr v-if="!calls.length">
                  <td colspan="6" class="text-center text-base-content/40 py-8">暂无调用记录</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
