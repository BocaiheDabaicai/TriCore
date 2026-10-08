<script setup>
import { useChatStore } from '../stores/chat'

const chat = useChatStore()

async function send() {
  const q = chat.draft.trim()
  if (!q || chat.loading) return
  chat.draft = ''
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
    <div class="scope-bar">
      <button class="scope-btn" :class="{ active: chat.selectedIds.length }" @click="chat.togglePanel()">
        指定文档{{ chat.selectedIds.length ? ` · ${chat.selectedIds.length} 篇` : '' }}
      </button>
      <button v-if="chat.selectedIds.length" class="scope-clear" @click="chat.clearSelection()">清除，恢复全库问答</button>
    </div>
    <div class="input-row">
      <textarea
        v-model="chat.draft"
        rows="2"
        placeholder="提问…（Enter 发送，Shift+Enter 换行）"
        @keydown="onKeydown"
      ></textarea>
      <button :disabled="chat.loading" @click="send">{{ chat.loading ? '回答中…' : '发送' }}</button>
    </div>
  </footer>
</template>
