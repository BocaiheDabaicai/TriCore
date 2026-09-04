<script setup>
import Sidebar from './components/Sidebar.vue'

// App 只做整体布局：左侧固定侧边栏 + 右侧路由出口（页面内容由当前路由的视图组件填充）
</script>

<template>
  <div class="flex h-screen bg-base-200">
    <Sidebar />
    <main class="flex-1 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>
