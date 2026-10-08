<script setup>
import { useConfirmStore } from '../stores/confirm'

// 确认弹窗的统一出口：任何页面 await confirmStore.confirm({...}) 都由这里展示
const confirm = useConfirmStore()
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': confirm.open }">
    <div class="modal-box max-w-sm">
      <h3 class="font-bold text-lg">{{ confirm.title }}</h3>
      <p v-if="confirm.message" class="py-4 text-sm text-base-content/70 whitespace-pre-line">{{ confirm.message }}</p>
      <div class="modal-action">
        <button class="btn btn-sm" @click="confirm.answer(false)">{{ confirm.cancelText }}</button>
        <button
          class="btn btn-sm"
          :class="confirm.danger ? 'btn-error' : 'btn-primary'"
          @click="confirm.answer(true)"
        >
          {{ confirm.confirmText }}
        </button>
      </div>
    </div>
  </dialog>
</template>
