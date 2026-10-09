<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useChatStore } from '../stores/chat'

// 左侧「对话记录」栏：本机全部会话（点击切换、行内删除）
const chat = useChatStore()

// 一问一答进行中 / 打开中 / 删除中：整列禁点（防止切换把流式回答与落库搅乱）
const busy = computed(() => chat.loading || !!chat.convOpeningId || !!chat.deletingId)

// 行内二次确认：点 ✕ 变红「确认删」，再点才真删；点别处或 2 秒后复原（零弹窗）
const confirmingId = ref(null)
let confirmTimer = null

function askDelete(id) {
  if (busy.value) return
  confirmingId.value = id
  clearTimeout(confirmTimer)
  confirmTimer = setTimeout(() => (confirmingId.value = null), 2000)
}

function doDelete(id) {
  clearTimeout(confirmTimer)
  confirmingId.value = null
  chat.removeConversation(id)
}

function onAnyClick() {
  confirmingId.value = null   // 点别处复原（删除按钮自己的点击已 stop，不会走到这）
}

onMounted(() => {
  chat.loadConversations()
  document.addEventListener('click', onAnyClick)
})
onBeforeUnmount(() => document.removeEventListener('click', onAnyClick))

// 列表时间：今天只显示时分，今年显示月日+时分，更早带年份
function fmtTime(s) {
  if (!s) return ''
  const d = new Date(s)
  const now = new Date()
  const p = (n) => String(n).padStart(2, '0')
  const hm = `${p(d.getHours())}:${p(d.getMinutes())}`
  if (d.toDateString() === now.toDateString()) return hm
  const md = `${p(d.getMonth() + 1)}-${p(d.getDate())}`
  if (d.getFullYear() === now.getFullYear()) return `${md} ${hm}`
  return `${d.getFullYear()}-${md} ${hm}`
}
</script>

<template>
  <aside class="session-list" :class="{ busy }">
    <div class="session-list-head">
      <span>对话记录</span>
    </div>

    <!-- 新建入口：常驻在标题下方（列表长了也第一眼可见），提问进行中禁用 -->
    <button class="btn-new-session" :disabled="chat.loading" @click="chat.newSession()">新对话</button>

    <p v-if="chat.convError" class="err">{{ chat.convError }}</p>
    <p v-else-if="chat.convLoading" class="hint">加载中…</p>
    <p v-else-if="!chat.conversations.length" class="hint">暂无对话记录</p>

    <div class="session-items">
      <div
        v-for="c in chat.conversations"
        :key="c.session_id"
        class="session-item"
        :class="{ active: c.session_id === chat.sessionId }"
        @click="chat.openConversation(c.session_id)"
      >
        <div class="s-main">
          <div class="s-title">{{ c.title || '新对话' }}</div>
          <div class="s-time">{{ fmtTime(c.updated_at) }}</div>
        </div>
        <button
          class="s-del"
          :class="{ confirming: confirmingId === c.session_id }"
          :disabled="busy"
          :title="confirmingId === c.session_id ? '再点一次确认删除' : '删除这个对话'"
          @click.stop="confirmingId === c.session_id ? doDelete(c.session_id) : askDelete(c.session_id)"
        >
          {{ confirmingId === c.session_id ? '确认删' : '✕' }}
        </button>
      </div>
    </div>
  </aside>
</template>
