<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { Button, Input, message } from 'ant-design-vue'
import { SendOutlined, RobotOutlined, UserOutlined, DeleteOutlined, CloseOutlined, MessageOutlined, ExpandOutlined, CompressOutlined } from '@ant-design/icons-vue'
import { aiAPI } from '@/services/api'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

type Msg = { role: 'user' | 'assistant'; content: string }

const open = ref(false)
const expanded = ref(false)
const messages = ref<Msg[]>([])
const inputText = ref('')
const sending = ref(false)
const chatBody = ref<HTMLElement | null>(null)

const panelStyle = computed(() => expanded.value
  ? { width: '720px', height: '680px', bottom: '48px', right: '48px' }
  : { width: '440px', height: '520px', bottom: '92px', right: '28px' }
)

const renderMarkdown = (text: string) => {
  try {
    return marked.parse(text) as string
  } catch {
    return text.replace(/\n/g, '<br>')
  }
}

const toggle = async () => {
  open.value = !open.value
  if (open.value && messages.value.length === 0) {
    try {
      const res: any = await aiAPI.getConfig()
      if (!res?.data?.api_key) {
        messages.value.push({ role: 'assistant', content: '请先在「AI配置」中设置 API Key。' })
      } else {
        messages.value.push({ role: 'assistant', content: '你好！我是 TriCore AI 助手。\n\n我可以帮你查询订单、库存、审批流程、员工信息、规章制度文件，以及系统概览。请直接告诉我你想了解什么？' })
      }
    } catch {
      messages.value.push({ role: 'assistant', content: '请先在「AI配置」中设置 API Key。' })
    }
  }
  await nextTick()
  scrollBottom()
}

const scrollBottom = async () => {
  await nextTick()
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value) return
  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  await scrollBottom()
  sending.value = true
  try {
    const apiMessages = messages.value.map(m => ({ role: m.role, content: m.content }))
    const res: any = await aiAPI.chat(apiMessages)
    const reply = res?.data?.message
    if (reply) messages.value.push({ role: 'assistant', content: reply.content })
  } catch (err: any) {
    messages.value.push({ role: 'assistant', content: '❌ ' + (err?.response?.data?.message || '对话失败') })
  } finally {
    sending.value = false
    await scrollBottom()
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
  <!-- Floating button -->
  <div class="fixed-float-btn">
    <Button
      type="primary"
      shape="circle"
      size="large"
      @click="toggle"
      :style="{ width: '52px', height: '52px', boxShadow: '0 4px 20px rgba(99,102,241,0.4)' }"
    >
      <template #icon><MessageOutlined :style="{ fontSize: '22px' }" /></template>
    </Button>
  </div>

  <!-- Chat panel -->
  <Transition name="slide-up">
    <div v-if="open" class="chat-panel" :style="panelStyle">
      <!-- Header -->
      <div class="chat-header">
        <div class="flex items-center gap-2">
          <RobotOutlined :style="{ color: 'var(--accent)' }" />
          <span class="font-semibold text-sm" :style="{ color: 'var(--text-primary)' }">AI 助手</span>
        </div>
        <div class="flex items-center gap-1">
          <Button type="text" size="small" @click="expanded = !expanded">
            <CompressOutlined v-if="expanded" />
            <ExpandOutlined v-else />
          </Button>
          <Button type="text" size="small" @click="handleClear" :disabled="sending"><DeleteOutlined /></Button>
          <Button type="text" size="small" @click="open = false"><CloseOutlined /></Button>
        </div>
      </div>

      <!-- Messages -->
      <div ref="chatBody" class="chat-body">
        <div v-for="(m, i) in messages" :key="i" class="flex gap-2 mb-3" :class="m.role === 'user' ? 'justify-end' : ''">
          <div v-if="m.role === 'assistant'"
            class="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
            :style="{ background: 'var(--accent-soft)', color: 'var(--accent)', fontSize: '12px' }">
            <RobotOutlined />
          </div>
          <div v-if="m.role === 'user'" class="chat-bubble user"
            :style="{ background: 'var(--accent)', color: '#fff' }">{{ m.content }}</div>
          <div v-else class="chat-bubble assistant markdown-body"
            :style="{ background: 'var(--input-bg)', color: 'var(--text-primary)' }"
            v-html="renderMarkdown(m.content)" />
          <div v-if="m.role === 'user'"
            class="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
            :style="{ background: 'var(--accent)', color: '#fff', fontSize: '12px' }">
            <UserOutlined />
          </div>
        </div>
        <div v-if="sending" class="text-xs px-2" :style="{ color: 'var(--text-muted)' }">思考中...</div>
      </div>

      <!-- Input -->
      <div class="chat-footer">
        <div class="flex gap-2">
          <Input.TextArea
            v-model:value="inputText"
            :rows="1"
            placeholder="输入问题..."
            :disabled="sending"
            :auto-size="{ minRows: 1, maxRows: 3 }"
            @pressEnter="(e: KeyboardEvent) => { if (!e.shiftKey) { e.preventDefault(); handleSend() } }"
            class="flex-1"
          />
          <Button type="primary" size="small" @click="handleSend" :loading="sending"><SendOutlined /></Button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fixed-float-btn {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 999;
}
.chat-panel {
  position: fixed;
  z-index: 998;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  background: var(--bg-card);
  backdrop-filter: blur(12px);
  box-shadow: var(--shadow-modal);
  user-select: text;
}
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.chat-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 14px;
}
.chat-footer {
  padding: 10px 14px;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.chat-bubble {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  user-select: text;
  word-break: break-word;
}
.chat-bubble.user {
  border-bottom-right-radius: 4px;
}
.chat-bubble.assistant {
  border-bottom-left-radius: 4px;
}
/* Markdown body */
.markdown-body :deep(p) { margin: 0 0 6px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin: 4px 0; padding-left: 18px; }
.markdown-body :deep(li) { margin-bottom: 2px; }
.markdown-body :deep(strong) { font-weight: 700; }
.markdown-body :deep(code) {
  background: rgba(0,0,0,0.08);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
.markdown-body :deep(pre) {
  background: rgba(0,0,0,0.06);
  padding: 8px 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 6px 0;
}
.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) {
  font-weight: 700;
  margin: 8px 0 4px;
}
.markdown-body :deep(h1) { font-size: 15px; }
.markdown-body :deep(h2) { font-size: 14px; }
.markdown-body :deep(h3) { font-size: 13px; }
.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--accent);
  margin: 6px 0;
  padding-left: 10px;
  opacity: 0.8;
}
.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 6px 0;
  font-size: 12px;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid var(--border-subtle);
  padding: 4px 8px;
  text-align: left;
}
.markdown-body :deep(th) { background: rgba(0,0,0,0.04); font-weight: 600; }
.markdown-body :deep(hr) { border: none; border-top: 1px solid var(--border-subtle); margin: 8px 0; }

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(16px);
}
</style>
