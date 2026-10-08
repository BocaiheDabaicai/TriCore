<script setup>
import { Camera, PlayCircle } from 'lucide-vue-next'
import { useRoute } from 'vue-router'

// 菜单扁平数组：加一项就加一行（图标直接用 lucide 组件）
const MENUS = [
  { path: '/', label: '执行台', icon: PlayCircle },
  { path: '/shots', label: '截图资料库', icon: Camera },
]

const route = useRoute()
</script>

<template>
  <aside class="w-52 shrink-0 bg-base-100 border-r border-base-300 flex flex-col">
    <div class="px-4 py-5 border-b border-base-300">
      <div class="text-base font-semibold">办公自动化操作台</div>
      <div class="text-xs text-base-content/50 mt-1">AI + RPA · 单元验证</div>
    </div>
    <nav class="p-3 space-y-1">
      <router-link
        v-for="menu in MENUS"
        :key="menu.path"
        :to="menu.path"
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-base-200"
        :class="route.path === menu.path ? 'bg-primary/10 text-primary font-medium' : 'text-base-content/80'"
      >
        <component :is="menu.icon" :size="16" />
        {{ menu.label }}
      </router-link>
    </nav>
    <div class="mt-auto p-4 text-xs text-base-content/40 leading-relaxed">
      后端 rpa-agent :8004<br />
      浏览器会话保存在本机
    </div>
  </aside>
</template>
