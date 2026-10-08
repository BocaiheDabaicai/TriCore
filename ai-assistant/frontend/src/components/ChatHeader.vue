<script setup>
import { ref, onMounted } from 'vue'
import { getStatus } from '../api/chat'
import { useChatStore } from '../stores/chat'

const chat = useChatStore()
const status = ref('正在连接服务…')

onMounted(async () => {
  try {
    const data = await getStatus()   // 响应拦截器已剥掉包装，data 直接是返回体
    status.value = `调度服务已连接 · kb-agent：${data.kb_agent_url}`
  } catch {
    status.value = '调度服务未连接'
  }
})
</script>

<template>
  <header class="chat-header">
    <h1>企业AI助手</h1>
    <span class="subtitle">{{ status }}</span>
    <button v-if="chat.messages.length" class="btn-new" :disabled="chat.loading" @click="chat.newSession()">
      新对话
    </button>
  </header>
</template>
