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
    <div class="input-row">
      <!-- 输入框容器：textarea + 底部一行小胶囊（作用域类控件都放这里，不另占行高） -->
      <div class="input-box">
        <textarea
          v-model="chat.draft"
          rows="2"
          placeholder="提问…（Enter 发送，Shift+Enter 换行）"
          @keydown="onKeydown"
        ></textarea>

        <div class="scope-chips">
          <!-- 已勾选：整颗高亮胶囊（点文字开合面板，点 ✕ 清除恢复全库） -->
          <div v-if="chat.selectedIds.length" class="scope-chip active">
            <button class="chip-toggle" @click="chat.togglePanel()">
              指定文档 · {{ chat.selectedIds.length }} 篇
            </button>
            <button class="chip-clear" title="清除，恢复全库问答" @click="chat.clearSelection()">✕</button>
          </div>
          <!-- 未勾选：灰色小胶囊，点开面板 -->
          <button v-else class="scope-chip" @click="chat.togglePanel()">指定文档</button>
        </div>
      </div>

      <button class="send-btn" :disabled="chat.loading" @click="send">{{ chat.loading ? '回答中…' : '发送' }}</button>
    </div>
  </footer>
</template>
