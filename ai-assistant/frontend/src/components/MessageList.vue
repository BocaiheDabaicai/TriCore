<script setup>
import { ref, watch } from 'vue'
import MessageBubble from './MessageBubble.vue'
import { useChatStore } from '../stores/chat'

// 消息列表直接用 store 取数据，不再从 App 传 props
const chat = useChatStore()
const listEl = ref(null)
const atBottom = ref(true)   // 是否贴着底部：贴着才自动跟滚，上翻看历史时不被拽回

// 空状态示例问题：覆盖不同问答路径（枚举 / 深度 / 汇总），点了直接问
const EXAMPLES = ['公司有哪些制度？', '宿舍的收费标准是什么？', '请假和调休有什么区别？', '差旅费用标准是多少？']

function isNearBottom(el) {
  return el.scrollHeight - el.scrollTop - el.clientHeight < 40
}

function onScroll() {
  if (listEl.value) atBottom.value = isNearBottom(listEl.value)
}

function scrollToBottom() {
  const el = listEl.value
  if (!el) return
  el.scrollTop = el.scrollHeight
  atBottom.value = true
}

// 消息变化后：自己发问（最后一条是用户消息）总是滚到底；流式回答只在贴底时跟滚。
// 不跟滚时按实际位置校准一次 atBottom —— 防止滚动事件与渲染交错时状态失真
watch(
  () => chat.messages.map((m) => m.content).join('') + chat.messages.length,
  () => {
    const el = listEl.value
    if (!el) return
    const last = chat.messages[chat.messages.length - 1]
    if (atBottom.value || last?.role === 'user') scrollToBottom()
    else atBottom.value = isNearBottom(el)
  },
  { flush: 'post' },
)
</script>

<template>
  <div class="chat-body">
    <!-- 空状态：首次进入给欢迎语和示例问题，不留白板 -->
    <div v-if="!chat.messages.length" class="chat-empty">
      <p class="empty-title">企业AI助手</p>
      <p class="empty-sub">公司制度、流程、文档都可以问我；也可以在下方「指定文档」里圈定范围再问</p>
      <div class="empty-examples">
        <button v-for="q in EXAMPLES" :key="q" @click="chat.sendQuestion(q)">{{ q }}</button>
      </div>
    </div>

    <div v-else ref="listEl" class="chat-list" @scroll.passive="onScroll">
      <MessageBubble
        v-for="(m, i) in chat.messages"
        :key="i"
        :message="m"
        :is-last="i === chat.messages.length - 1"
      />
    </div>

    <!-- 上翻看历史时才出现；点了平滑回到底部继续跟滚 -->
    <button v-if="chat.messages.length && !atBottom" class="back-bottom" @click="scrollToBottom">
      回到底部 ↓
    </button>
  </div>
</template>
