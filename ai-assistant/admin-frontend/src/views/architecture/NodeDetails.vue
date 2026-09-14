<script setup>
import { ExternalLink, X } from 'lucide-vue-next'
import { STATUS_META } from '../../utils/meta'

// 抽屉内容 · 服务卡片详情：作用 / 技术栈 / 数据库 / 外部依赖 + 进入服务 / 去服务管理
defineProps({
  node: { type: Object, required: true },
})
const emit = defineEmits(['close'])
</script>

<template>
  <div>
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-lg font-bold">{{ node.cnName }}</div>
        <div class="text-xs text-base-content/50 mt-0.5">{{ node.sub }}</div>
      </div>
      <button class="btn btn-ghost btn-sm btn-circle" @click="emit('close')">
        <X class="w-4 h-4" />
      </button>
    </div>

    <div class="mt-3">
      <span class="badge badge-sm" :class="STATUS_META[node.status]?.badge">
        {{ STATUS_META[node.status]?.text }}
      </span>
    </div>

    <div class="mt-5 space-y-4 text-sm">
      <div>
        <div class="text-xs text-base-content/40 mb-1">作用</div>
        <p>{{ node.detail.role }}</p>
      </div>
      <template v-if="node.detail.stack">
        <div>
          <div class="text-xs text-base-content/40 mb-1">技术栈</div>
          <p>{{ node.detail.stack }}</p>
        </div>
      </template>
      <template v-if="node.detail.db">
        <div>
          <div class="text-xs text-base-content/40 mb-1">数据库</div>
          <p>{{ node.detail.db }}</p>
        </div>
      </template>
      <template v-if="node.detail.deps">
        <div>
          <div class="text-xs text-base-content/40 mb-1">外部依赖</div>
          <p>{{ node.detail.deps }}</p>
        </div>
      </template>
    </div>

    <div class="mt-6 flex gap-2">
      <a
        v-if="node.enterUrl && node.status === 'running'"
        class="btn btn-sm btn-primary"
        :href="node.enterUrl"
        target="_blank"
        rel="noopener"
      >
        <ExternalLink class="w-4 h-4" />
        进入服务
      </a>
      <router-link
        v-if="!node.planned && !node.unmanaged"
        to="/services"
        class="btn btn-sm btn-outline"
      >
        去服务管理
      </router-link>
    </div>
  </div>
</template>
