<script setup>
import { ref } from 'vue'
import { useChatStore } from '../stores/chat'

const chat = useChatStore()
const input = ref('')

async function send() {
  const q = input.value.trim()
  if (!q || chat.loading) return
  input.value = ''
  await chat.sendQuestion(q)
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}
</script>

<template>
  <footer class="chat-input">
    <textarea
      v-model="input"
      rows="2"
      placeholder="提问…（Enter 发送，Shift+Enter 换行）"
      @keydown="onKeydown"
    ></textarea>
    <button :disabled="chat.loading" @click="send">{{ chat.loading ? '回答中…' : '发送' }}</button>
  </footer>
</template>
