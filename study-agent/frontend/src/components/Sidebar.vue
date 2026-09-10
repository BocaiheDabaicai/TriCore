<script setup>
import { useRoute } from 'vue-router'
import { BookOpen, LibraryBig, PenLine } from 'lucide-vue-next'

// 研读库侧栏：收起是一条 48px 的"图标轨道"（图标常驻可见），鼠标悬停滑出导航文字
const route = useRoute()

const LINKS = [
  { to: '/', label: '研读', icon: PenLine },
  { to: '/review', label: '回顾', icon: LibraryBig },
]

// 高亮当前页：'/' 要精确匹配，其它按前缀（这样 /review/3 详情页也能让"回顾"保持高亮）
const isActive = (to) => (to === '/' ? route.path === '/' : route.path.startsWith(to))
</script>

<template>
  <!-- 容器：w-12（48px 图标轨道）→ hover 展到 w-52 -->
  <div
    class="fixed left-0 top-0 z-50 h-full w-12 hover:w-52 group
           bg-base-200 shadow-xl rounded-r-2xl overflow-hidden
           transition-all duration-300 ease-out"
  >
    <!-- 内容固定 13rem 宽：收起时只露出左侧 48px 的图标列 -->
    <div class="w-52 h-full flex flex-col py-3">
      <!-- 顶部 logo：图标与下方导航图标同一列对齐 -->
      <div class="flex items-center gap-3 px-3.5 py-2 mb-2">
        <BookOpen class="w-5 h-5 shrink-0 text-primary" />
        <span class="font-bold whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          研读库
        </span>
      </div>

      <nav class="flex flex-col gap-1 px-2">
        <router-link
          v-for="l in LINKS"
          :key="l.to"
          :to="l.to"
          class="flex items-center gap-3 px-1.5 py-2.5 rounded-xl transition-colors"
          :class="isActive(l.to) ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-base-300'"
        >
          <component :is="l.icon" class="w-5 h-5 shrink-0" />
          <span class="whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            {{ l.label }}
          </span>
        </router-link>
      </nav>
    </div>
  </div>
</template>
