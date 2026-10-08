<script setup>
import Sidebar from './components/Sidebar.vue'
import ToastHost from './components/ToastHost.vue'
import ConfirmHost from './components/ConfirmHost.vue'

// App 只做整体布局：左侧固定侧边栏 + 右侧路由出口（页面内容由当前路由的视图组件填充）
// ToastHost / ConfirmHost 挂在这里：全局提示与确认弹窗不随页面切换而消失
</script>

<template>
  <div class="flex h-screen bg-base-200">
    <Sidebar />
    <main class="flex-1 overflow-y-auto">
      <router-view />
    </main>
    <ToastHost />
    <ConfirmHost />
  </div>
</template>
