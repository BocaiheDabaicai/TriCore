<script setup>
import { X } from 'lucide-vue-next'
import { METHOD_META } from '../../utils/meta'

// 抽屉内容 · 接口详情：方法 / 路径 / 作用 / 所属链路
defineProps({
  api: { type: Object, required: true },
  nameMap: { type: Object, required: true },
})
const emit = defineEmits(['close'])
</script>

<template>
  <div>
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <div class="text-base font-bold">接口详情</div>
        <div class="text-xs text-base-content/50 mt-0.5">
          {{ nameMap[api.from] ?? api.from }} → {{ api.to ? (nameMap[api.to] ?? api.to) : api.toLabel }}
        </div>
      </div>
      <button class="btn btn-ghost btn-sm btn-circle" @click="emit('close')">
        <X class="w-4 h-4" />
      </button>
    </div>

    <div class="mt-3 flex items-center gap-2">
      <span class="badge badge-sm" :class="METHOD_META[api.method] || 'badge-ghost'">
        {{ api.method }}
      </span>
    </div>
    <div class="font-mono text-xs break-all mt-2 text-base-content/70">{{ api.path }}</div>

    <div class="mt-5 space-y-4 text-sm">
      <div>
        <div class="text-xs text-base-content/40 mb-1">作用</div>
        <p>{{ api.detail }}</p>
      </div>
      <div v-if="api.note">
        <div class="text-xs text-base-content/40 mb-1">所属链路</div>
        <p>{{ api.note }}</p>
      </div>
    </div>
  </div>
</template>
