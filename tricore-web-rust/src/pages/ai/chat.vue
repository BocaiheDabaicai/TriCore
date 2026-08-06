<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Input, message, Spin } from 'ant-design-vue'
import { SendOutlined, RobotOutlined, UserOutlined, DeleteOutlined, ArrowLeftOutlined } from '@ant-design/icons-vue'
import { aiAPI } from '@/services/ai'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

const router = useRouter()

type ReasonStep = { type: string; tool: string; args: Record<string, unknown>; result: string }
type Msg = { role: 'user' | 'assistant'; content: string; reasoning?: ReasonStep[] }

const messages = ref<Msg[]>([])
const inputText = ref('')
const sending = ref(false)
const initLoading = ref(true)
const chatBody = ref<HTMLElement | null>(null)

const renderMarkdown = (text: string) => {
  try { return marked.parse(text) as string } catch { return text.replace(/\n/g, '<br>') }
}

const toolLabel = (name: string) => {
  const map: Record<string, string> = {
    list_tables: '列出数据表', describe_table: '查看表结构', run_query: '执行查询',
    list_apis: '列出 API', call_api: '调用 API',
  }
  return map[name] || name
}

onMounted(async () => {
  try {
    const res: any = await aiAPI.getConfig()
    if (!res?.data?.api_key) {
      messages.value.push({ role: 'assistant', content: '请先在「AI配置」中设置 API Key 后再使用 AI 对话。' })
    } else {
      messages.value.push({ role: 'assistant', content: '你好！我是 TriCore AI 助手。\n\n我可以帮你查询订单、库存、审批流程、员工信息、规章制度文件，以及系统概览。也可以帮你创建订单、调整库存、管理员工等操作。请直接告诉我你想了解什么或完成什么任务？' })
    }
  } catch {
    messages.value.push({ role: 'assistant', content: '请先在「AI配置」中设置 API Key。' })
  } finally {
    initLoading.value = false
  }
})

const scrollBottom = async () => { await nextTick(); if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight }

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value) return
  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  const msgIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', reasoning: [] })
  await scrollBottom()
  sending.value = true

  const apiMessages = messages.value.filter(m => m.content).map(m => ({ role: m.role, content: m.content }))
  aiAPI.chatStream(apiMessages,
    (evt) => {
      if (evt.type === 'thinking') {
        messages.value[msgIdx].reasoning!.push({ type: 'tool_call', tool: evt.tool!, args: evt.args!, result: evt.result! })
        scrollBottom()
      } else if (evt.type === 'message') {
        messages.value[msgIdx].content = evt.content!
        scrollBottom()
      }
    },
    (errMsg) => {
      messages.value[msgIdx].content = '❌ ' + errMsg
      sending.value = false
    },
    () => {
      if (!messages.value[msgIdx].reasoning?.length) delete messages.value[msgIdx].reasoning
      sending.value = false
      scrollBottom()
    }
  )
}

const handleClear = () => {
  messages.value = [{ role: 'assistant', content: '对话已清空。有什么可以帮你的？' }]
}
</script>

<template>
  <div class="ai-chat-fullscreen">
    <!-- Top bar -->
    <div class="chat-topbar">
      <div class="flex items-center gap-2">
        <Button type="text" size="small" @click="router.push('/dashboard')">
          <ArrowLeftOutlined />
        </Button>
        <RobotOutlined :style="{ color: 'var(--accent)', fontSize: '18px' }" />
        <span class="font-semibold text-sm">AI 助手</span>
        <span class="text-xs px-1.5 py-0.5 rounded-md" :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">TriCore</span>
      </div>
      <Button type="text" size="small" @click="handleClear" :disabled="sending">
        <DeleteOutlined /> 清空对话
      </Button>
    </div>

    <!-- Body -->
    <div class="chat-main">
      <div v-if="initLoading" class="flex items-center justify-center" style="flex:1">
        <Spin :spinning="true" />
      </div>
      <template v-else>
        <!-- Messages -->
        <div ref="chatBody" class="chat-messages">
          <div v-for="(m, i) in messages" :key="i" class="flex gap-3 mb-4" :class="m.role === 'user' ? 'justify-end' : ''">
            <div v-if="m.role === 'assistant'"
              class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1"
              :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">
              <RobotOutlined :style="{ fontSize: '14px' }" />
            </div>
            <div class="flex flex-col gap-2" :style="{ maxWidth: m.role === 'user' ? '65%' : '80%' }">
              <div v-if="m.role === 'user'" class="chat-bubble user"
                :style="{ background: 'var(--accent)', color: '#fff', maxWidth: '100%' }">{{ m.content }}</div>
              <template v-else>
                <div v-if="m.reasoning && m.reasoning.length > 0" class="reasoning-block">
                  <div class="text-xs font-medium mb-2" :style="{ color: 'var(--text-muted)' }">分析过程（{{ m.reasoning.length }} 步）</div>
                  <div class="space-y-2">
                    <div v-for="(step, si) in m.reasoning" :key="si" class="reason-step">
                      <div class="reason-step-header">
                        <span class="reason-step-tool">{{ toolLabel(step.tool) }}</span>
                        <span class="reason-step-args" v-if="step.tool === 'run_query'">SQL: {{ (step.args?.sql as string || '').substring(0, 60) }}{{ (step.args?.sql as string || '').length > 60 ? '...' : '' }}</span>
                        <span class="reason-step-args" v-else-if="step.tool === 'call_api'">{{ step.args?.method }} {{ step.args?.path }}</span>
                      </div>
                      <div class="reason-step-body markdown-body" v-html="renderMarkdown(step.result)" />
                    </div>
                  </div>
                </div>
                <div class="chat-bubble assistant markdown-body"
                  :style="{ background: 'var(--input-bg)', color: 'var(--text-primary)' }"
                  v-html="renderMarkdown(m.content)" />
              </template>
            </div>
            <div v-if="m.role === 'user'"
              class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1"
              :style="{ background: 'var(--accent)', color: '#fff' }">
              <UserOutlined :style="{ fontSize: '14px' }" />
            </div>
          </div>
          <div v-if="sending" class="text-sm px-2 py-4 flex items-center gap-2" :style="{ color: 'var(--text-muted)' }">
            <span class="typing-dot" />
            <span class="typing-dot" :style="{ animationDelay: '0.2s' }" />
            <span class="typing-dot" :style="{ animationDelay: '0.4s' }" />
            分析中...
          </div>
        </div>

        <!-- Input -->
        <div class="chat-input-bar">
          <div class="flex gap-2 max-w-3xl mx-auto">
            <Input.TextArea v-model:value="inputText" :rows="1"
              placeholder="输入问题，Enter 发送，Shift+Enter 换行..."
              :disabled="sending"
              :auto-size="{ minRows: 1, maxRows: 4 }"
              @pressEnter="(e: KeyboardEvent) => { if (!e.shiftKey) { e.preventDefault(); handleSend() } }"
              class="flex-1" />
            <Button type="primary" @click="handleSend" :loading="sending">
              <SendOutlined /> 发送
            </Button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.ai-chat-fullscreen {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  z-index: 10;
}
.chat-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-card);
  backdrop-filter: blur(12px);
}
.chat-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}
.chat-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 20px;
}
.chat-input-bar {
  flex-shrink: 0;
  padding: 12px 20px 16px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-card);
}
.chat-bubble {
  padding: 10px 16px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  user-select: text;
  word-break: break-word;
}
.chat-bubble.user { border-bottom-right-radius: 6px; }
.chat-bubble.assistant { border-bottom-left-radius: 6px; }
.reasoning-block {
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px 12px;
  background: rgba(0,0,0,0.02);
}
.reason-step {
  border-left: 2px solid var(--accent);
  padding: 6px 10px;
  margin-left: 4px;
  border-radius: 0 6px 6px 0;
  background: rgba(0,0,0,0.03);
}
.reason-step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}
.reason-step-tool { font-size: 12px; font-weight: 600; color: var(--accent); }
.reason-step-args {
  font-size: 11px;
  color: var(--text-muted);
  font-family: ui-monospace, monospace;
}
.reason-step-body {
  font-size: 12px;
  opacity: 0.85;
  max-height: 200px;
  overflow-y: auto;
}
.reason-step-body :deep(p) { margin: 3px 0; font-size: 12px; }
.reason-step-body :deep(table) { font-size: 11px; }

.markdown-body :deep(p) { margin: 0 0 8px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin: 6px 0; padding-left: 20px; }
.markdown-body :deep(li) { margin-bottom: 3px; }
.markdown-body :deep(strong) { font-weight: 700; }
.markdown-body :deep(code) { background: rgba(0,0,0,0.08); padding: 2px 6px; border-radius: 4px; font-family: ui-monospace, monospace; font-size: 13px; }
.markdown-body :deep(pre) { background: rgba(0,0,0,0.06); padding: 10px 14px; border-radius: 8px; overflow-x: auto; margin: 8px 0; }
.markdown-body :deep(pre code) { background: none; padding: 0; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { font-weight: 700; margin: 12px 0 6px; }
.markdown-body :deep(h1) { font-size: 17px; }
.markdown-body :deep(h2) { font-size: 16px; }
.markdown-body :deep(h3) { font-size: 15px; }
.markdown-body :deep(blockquote) { border-left: 3px solid var(--accent); margin: 8px 0; padding-left: 12px; opacity: 0.85; }
.markdown-body :deep(table) { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid var(--border-subtle); padding: 6px 10px; text-align: left; }
.markdown-body :deep(th) { background: rgba(0,0,0,0.04); font-weight: 600; }
.markdown-body :deep(hr) { border: none; border-top: 1px solid var(--border-subtle); margin: 12px 0; }

.typing-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: dot-bounce 1.4s ease-in-out infinite both;
}
@keyframes dot-bounce {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
</style>
