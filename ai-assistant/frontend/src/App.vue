<script setup>
import ChatHeader from './components/ChatHeader.vue'
import MessageList from './components/MessageList.vue'
import ChatInput from './components/ChatInput.vue'
import DocPanel from './components/DocPanel.vue'
import { useChatStore } from './stores/chat'

const chat = useChatStore()

// App 只做布局：三个组件各自从 store 取自己需要的数据
// 左侧「指定文档」面板常挂载、收起时宽度 0；外层卡片配合它的展开一起变宽（见 style.css）
</script>

<template>
  <div class="chat-page" :class="{ 'panel-open': chat.panelOpen }">
    <DocPanel />
    <div class="chat-main">
      <ChatHeader />
      <MessageList />
      <ChatInput />
    </div>
  </div>
</template>
