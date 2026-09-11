<script setup>
import Sidebar from './components/Sidebar.vue'
import ToastHost from './components/ToastHost.vue'

// App.vue 只负责布局：侧栏 + 页面出口 + 全局轻提示；页面从 router 进来
</script>

<template>
  <div class="min-h-screen bg-base-100">
    <Sidebar />
    <main class="pl-12">
      <router-view />
    </main>
    <ToastHost />
  </div>
</template>
