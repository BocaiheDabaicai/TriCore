<script setup>
import { ref, watch } from 'vue'
import MessageBubble from './MessageBubble.vue'
import { useChatStore } from '../stores/chat'

// 消息列表直接用 store 取数据，不再从 App 传 props
const chat = useChatStore()
const listEl = ref(null)

// 消息内容变化就滚到底部；flush: 'post' 等 DOM 更新完再滚，否则滚的是旧高度
watch(
  () => chat.messages.map((m) => m.content).join('') + chat.messages.length,
  () => {
    listEl.value && (listEl.value.scrollTop = listEl.value.scrollHeight)
  },
  { flush: 'post' },
)
</script>

<template>
  <div ref="listEl" class="chat-list">
    <MessageBubble v-for="(m, i) in chat.messages" :key="i" :message="m" />
  </div>
</template>
