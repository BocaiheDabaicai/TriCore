<script setup>
import { AI_USAGES, AI_GUIDE } from '../../data/aimodels'

// AI 视图：哪里用了 AI、用的什么模型、去哪里改
defineProps({
  nameMap: { type: Object, required: true },
})
</script>

<template>
  <div class="card bg-base-100 shadow">
    <div class="card-body space-y-5">
      <div
        v-for="s in AI_USAGES"
        :key="s.ownerKey"
        class="rounded-2xl border p-4"
        :class="s.planned ? 'border-dashed border-base-content/25' : 'border-base-300'"
      >
        <div class="flex items-center gap-2">
          <span class="text-sm font-medium">{{ nameMap[s.ownerKey] ?? s.ownerKey }}</span>
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
</template>
