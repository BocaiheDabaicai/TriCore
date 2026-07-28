<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { Button, Input, Spin, message } from 'ant-design-vue'
import { SendOutlined, RobotOutlined, UserOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { aiAPI } from '@/services/api'

type Message = { role: 'user' | 'assistant'; content: string }

const messages = ref<Message[]>([])
const inputText = ref('')
const sending = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
const configReady = ref(false)

onMounted(async () => {
  try {
    const res: any = await aiAPI.getConfig()
    if (res?.data?.api_key) {
      configReady.value = true
      messages.value = [{
        role: 'assistant',
        content: '你好！我是 TriCore AI 助手。我可以帮你：\n\n• 查询和分析销售订单\n• 查看库存状况和预警\n• 了解审批流程进度\n• 查询员工和规章制度文件\n• 获取系统概览统计\n\n请直接告诉我你想了解什么？',
      }]
    }
  } catch { /* config not set up */ }
})

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value) return
  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  await scrollToBottom()

  sending.value = true
  try {
    const apiMessages = messages.value.map(m => ({ role: m.role, content: m.content }))
    const res: any = await aiAPI.chat(apiMessages)
    const reply = res?.data?.message
    if (reply) {
      messages.value.push({ role: 'assistant', content: reply.content })
    }
  } catch (err: any) {
    const errMsg = err?.response?.data?.message || '对话失败，请检查 AI 配置'
    messages.value.push({ role: 'assistant', content: `❌ ${errMsg}` })
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

const handleClear = () => {
  messages.value = [{
    role: 'assistant',
    content: '对话已清空。有什么可以帮你的？',
  }]
}
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">AI 对话</h2>
      <p>智能问答 · 数据查询 · 业务分析</p>
    </div>

    <div class="glass-card" style="display:flex; flex-direction:column; height: calc(100vh - 200px)">
      <!-- Header bar -->
      <div class="flex items-center justify-between p-4 border-b" :style="{ borderColor: 'var(--border-subtle)' }">
        <div class="flex items-center gap-2">
          <RobotOutlined :style="{ color: 'var(--accent)', fontSize: '18px' }" />
          <span class="font-semibold" :style="{ color: 'var(--text-primary)' }">TriCore AI 助手</span>
          <span class="text-xs px-2 py-0.5 rounded" :style="{ color: 'var(--accent)', background: 'var(--accent-soft)' }">Function Calling</span>
        </div>
        <Button size="small" @click="handleClear" :disabled="sending"><DeleteOutlined /> 清空对话</Button>
      </div>

      <!-- Messages area -->
      <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-3">
        <!-- Not configured -->
        <div v-if="!configReady" class="text-center py-12">
          <RobotOutlined :style="{ color: 'var(--text-muted)', fontSize: '48px' }" />
          <p class="mt-4 mb-2 font-semibold" :style="{ color: 'var(--text-primary)' }">AI 助手尚未配置</p>
          <p class="text-sm mb-4" :style="{ color: 'var(--text-muted)' }">请先在「AI 配置」页面设置 API Key 和模型</p>
        </div>

        <!-- Messages -->
        <div v-for="(m, i) in messages" :key="i" class="flex gap-3" :class="m.role === 'user' ? 'justify-end' : ''">
          <!-- Avatar -->
          <div v-if="m.role === 'assistant'" class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">
            <RobotOutlined />
          </div>

          <!-- Bubble -->
          <div class="max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed"
            :style="{
              background: m.role === 'user' ? 'var(--accent)' : 'var(--input-bg)',
              color: m.role === 'user' ? '#fff' : 'var(--text-primary)',
              borderRadius: m.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            }"
            style="white-space: pre-wrap"
          >{{ m.content }}</div>

          <!-- User avatar -->
          <div v-if="m.role === 'user'" class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            :style="{ background: 'var(--accent)', color: '#fff' }">
            <UserOutlined />
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="sending" class="flex gap-3">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">
            <RobotOutlined />
          </div>
          <div class="px-4 py-3 rounded-xl" :style="{ background: 'var(--input-bg)' }">
            <span :style="{ color: 'var(--text-muted)' }">思考中...</span>
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="p-4 border-t" :style="{ borderColor: 'var(--border-subtle)' }">
        <div class="flex gap-2">
          <Input.TextArea
            v-model:value="inputText"
            :rows="2"
            placeholder="输入你的问题，例如：最近有哪些待处理的订单？库存有什么预警？"
            :disabled="!configReady || sending"
            @pressEnter="(e: KeyboardEvent) => { if (!e.shiftKey) { e.preventDefault(); handleSend() } }"
            class="flex-1"
          />
          <Button type="primary" size="large" @click="handleSend" :loading="sending" :disabled="!configReady">
            <SendOutlined />
          </Button>
        </div>
        <p class="text-xs mt-1" :style="{ color: 'var(--text-muted)' }">Enter 发送 · Shift+Enter 换行</p>
      </div>
    </div>
  </div>
</template>
