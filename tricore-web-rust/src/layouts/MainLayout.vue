<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const isDark = ref(true)

onMounted(() => {
  const saved = localStorage.getItem('theme')
  isDark.value = saved ? saved === 'dark' : true
  applyTheme()
})

function applyTheme() {
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

function toggleTheme() {
  isDark.value = !isDark.value
  applyTheme()
}

const menuItems = [
  { key: '/dashboard', icon: () => h('span', '📊'), label: '工作台' },
  { key: '/sales',    icon: () => h('span', '🛒'), label: '销售管理' },
  { key: '/oa',       icon: () => h('span', '📋'), label: '办公协同' },
  { key: '/inventory',icon: () => h('span', '📦'), label: '库存管理' },
]

const currentLabel = () => menuItems.find(m => m.key === route.path)?.label || 'TriCore'

function onMenuClick({ key }: { key: string }) { router.push(key) }
</script>

<template>
  <a-layout has-sider :style="{ background: 'var(--bg-primary)', minHeight: '100vh' }">
    <a-layout-sider
      v-model:collapsed="collapsed" collapsible :width="220" trigger="null"
      :style="{ background: 'var(--sidebar-bg)' }"
      class="border-r" :class="'border-[var(--border-subtle)]'"
    >
      <div class="h-16 flex items-center justify-center cursor-pointer select-none" @click="collapsed = !collapsed">
        <span class="text-2xl font-bold gradient-text tracking-wider">{{ collapsed ? '三核' : 'TriCore' }}</span>
        <span v-if="!collapsed" class="text-sm ml-1 mt-1" :style="{ color: 'var(--text-muted)' }">三核</span>
      </div>
      <a-menu theme="dark" mode="inline" :selected-keys="[route.path]" :items="menuItems"
        @click="onMenuClick"
        :style="{ background: 'transparent', borderInlineEnd: 'none' }"
        class="px-3"
      />
    </a-layout-sider>
    <a-layout :style="{ background: 'transparent' }">
      <div class="h-16 flex items-center justify-between px-6 border-b" :style="{ borderColor: 'var(--border-subtle)' }">
        <span class="text-sm font-medium tracking-wide" :style="{ color: 'var(--text-secondary)' }">{{ currentLabel() }}</span>
        <button class="theme-toggle-btn" @click="toggleTheme" :title="isDark ? '亮色模式' : '暗色模式'">
          {{ isDark ? '☀️' : '🌙' }}
        </button>
      </div>
      <a-layout-content class="p-6 overflow-auto" :style="{ background: 'transparent' }">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>
