<script setup>
import ChatHeader from './components/ChatHeader.vue'
import MessageList from './components/MessageList.vue'
import ChatInput from './components/ChatInput.vue'

// App 只做布局：三个组件各自从 store 取自己需要的数据
</script>

<template>
  <div class="chat-page">
    <ChatHeader />
    <MessageList />
    <ChatInput />
  </div>
</template>
