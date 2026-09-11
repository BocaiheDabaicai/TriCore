<script setup>
import { AlertCircle, CheckCircle2 } from 'lucide-vue-next'
import { useToastStore } from '../stores/toast'

// 轻提示的统一出口：挂在 App.vue 上，页面怎么切都不影响它
const toast = useToastStore()
</script>

<template>
  <div class="toast toast-top toast-center z-[1000] pointer-events-none">
    <TransitionGroup
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="opacity-0"
    >
      <div
        v-for="t in toast.items"
        :key="t.id"
        class="alert shadow-md pointer-events-auto"
        :class="t.type === 'error' ? 'alert-error alert-soft' : 'alert-success alert-soft'"
      >
        <CheckCircle2 v-if="t.type !== 'error'" class="w-4 h-4" />
        <AlertCircle v-else class="w-4 h-4" />
        <span class="text-sm">{{ t.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>
