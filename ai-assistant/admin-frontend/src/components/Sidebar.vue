<script setup>
import { useRoute } from 'vue-router'
import { LayoutDashboard, Upload, LibraryBig, Inbox, Server, Network } from 'lucide-vue-next'

// 侧边栏菜单配置（扁平数组，type 区分导航项/分组标题）
// 以后接入新 Agent（doc-review 等）的管理页时，往这里加几行即可
const MENUS = [
  { type: 'link', path: '/', label: '总览', icon: LayoutDashboard },
  { type: 'title', label: '运维（manager）' },
  { type: 'link', path: '/services', label: '服务管理', icon: Server },
  { type: 'link', path: '/architecture', label: '架构图', icon: Network },
  { type: 'title', label: '知识库（kb-agent）' },
  { type: 'link', path: '/kb/upload', label: '上传知识', icon: Upload },
  { type: 'link', path: '/kb/list', label: '知识列表', icon: LibraryBig },
  { type: 'link', path: '/kb/missed', label: '未命中问题', icon: Inbox },
]

const route = useRoute()
</script>

<template>
  <aside class="w-60 shrink-0 bg-base-100 border-r border-base-300 flex flex-col">
    <div class="h-16 flex items-center gap-2 px-5 border-b border-base-300">
      <span class="text-lg font-bold">企业AI助手</span>
      <span class="badge badge-sm badge-primary">管理端</span>
    </div>

    <!-- daisyUI menu：菜单项直接放 router-link，点击即路由跳转 -->
    <ul class="menu w-full flex-1 px-3 py-4 gap-1">
      <template v-for="(menu, i) in MENUS" :key="i">
        <li v-if="menu.type === 'title'" class="menu-title">{{ menu.label }}</li>
        <li v-else>
          <router-link :to="menu.path" :class="{ 'menu-active': route.path === menu.path }">
            <component :is="menu.icon" :size="16" />
            {{ menu.label }}
          </router-link>
        </li>
      </template>
    </ul>
  </aside>
</template>
