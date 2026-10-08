<script setup>
defineProps({
  title: { type: String, required: true },
  desc: { type: String, default: '' },
})
</script>

<template>
  <div class="flex items-start justify-between gap-4">
    <div>
      <h1 class="text-xl font-semibold">{{ title }}</h1>
      <p v-if="desc" class="text-sm text-base-content/50 mt-1">{{ desc }}</p>
    </div>
    <div class="shrink-0">
      <slot name="actions" />
    </div>
  </div>
</template>
