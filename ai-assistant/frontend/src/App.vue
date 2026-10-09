<script setup>
import SessionList from './components/SessionList.vue'
import ChatHeader from './components/ChatHeader.vue'
import MessageList from './components/MessageList.vue'
import ChatInput from './components/ChatInput.vue'
import DocPanel from './components/DocPanel.vue'
import { useChatStore } from './stores/chat'

const chat = useChatStore()

// App 只做布局：三个组件各自从 store 取自己需要的数据
// 三栏 = 对话记录（260px 固定）+ 指定文档面板（展开时挤窄聊天列）+ 聊天区铺满剩余
</script>

<template>
  <div class="chat-page">
    <SessionList />
    <DocPanel />
    <div class="chat-main">
      <ChatHeader />
      <MessageList />
      <ChatInput />
    </div>
  </div>
</template>
