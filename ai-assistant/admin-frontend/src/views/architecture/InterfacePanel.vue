<script setup>
import { ArrowRight } from 'lucide-vue-next'
import { INTERFACE_GROUPS } from '../../data/interfaces'
import { METHOD_META } from '../../utils/meta'

// 接口视图：按「调用方 → 被调方」分组的接口清单，点任一接口看作用与链路
defineProps({
  nameMap: { type: Object, required: true },
})
const emit = defineEmits(['select-api'])
</script>

<template>
  <div class="card bg-base-100 shadow">
    <div class="card-body space-y-7">
      <section v-for="(g, gi) in INTERFACE_GROUPS" :key="gi">
        <div class="flex flex-wrap items-center gap-2 mb-3">
          <span class="text-sm font-medium">{{ nameMap[g.fromKey] ?? g.fromKey }}</span>
          <ArrowRight class="w-4 h-4 text-base-content/40" />
          <span class="text-sm font-medium">{{ g.toKey ? (nameMap[g.toKey] ?? g.toKey) : g.toLabel }}</span>
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
            @click="emit('select-api', g, api)"
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
</template>
