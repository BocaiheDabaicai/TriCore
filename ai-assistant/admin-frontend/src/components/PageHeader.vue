<script setup>
// 页头：标题 + 说明；右侧操作区用 actions 具名插槽（不传就只渲染标题区）
defineProps({
  title: { type: String, required: true },
  desc: { type: String, default: '' },
})
</script>

<template>
  <div :class="$slots.actions ? 'flex items-end justify-between gap-4' : ''">
    <div>
      <h1 class="text-2xl font-bold">{{ title }}</h1>
      <p class="text-sm text-base-content/60 mt-1">{{ desc }}</p>
    </div>
    <div v-if="$slots.actions" class="flex gap-2 shrink-0">
      <slot name="actions" />
    </div>
  </div>
</template>
