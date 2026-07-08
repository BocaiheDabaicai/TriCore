<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Spin } from 'ant-design-vue'
import { salesAPI, oaAPI, inventoryAPI } from '@/services/api'

const loading = ref(true)
const stats = ref([
  { title: '销售订单', value: 0, icon: '🛒', color: '#6366f1', subtitle: '全部订单' },
  { title: '员工数量', value: 0, icon: '👥', color: '#22c55e', subtitle: '在职员工' },
  { title: '商品种类', value: 0, icon: '📦', color: '#f59e0b', subtitle: '活跃商品' },
  { title: '待处理流程', value: 0, icon: '📋', color: '#ef4444', subtitle: 'OA审批中' },
  { title: '库存预警', value: 0, icon: '⚠️', color: '#8b5cf6', subtitle: '低库存' },
  { title: '本月完成', value: 0, icon: '✅', color: '#06b6d4', subtitle: '已交付' },
])

onMounted(async () => {
  try {
    const [s, o, i] = await Promise.allSettled([salesAPI.getDashboard(), oaAPI.getDashboard(), inventoryAPI.getDashboard()])
    if (s.status === 'fulfilled') { const d = (s.value as any)?.data || s.value; stats.value[0].value = d?.total_orders ?? 0; const del = d?.orders_by_status?.find((x: any) => x.status === 'delivered'); stats.value[5].value = del?.count ?? 0 }
    if (o.status === 'fulfilled') { const d = (o.value as any)?.data || o.value; stats.value[1].value = d?.total_employees ?? 0; stats.value[3].value = d?.pending_workflows ?? 0 }
    if (i.status === 'fulfilled') { const d = (i.value as any)?.data || i.value; stats.value[2].value = d?.total_products ?? 0; stats.value[4].value = d?.low_stock_count ?? 0 }
  } finally { loading.value = false }
})
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-2 gradient-text">工作台</h2>
    <p class="text-sm mb-6" :style="{ color: 'var(--text-muted)' }">TriCore 三核管理系统 — 核心业务概览</p>
    <Spin :spinning="loading">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div v-for="item in stats" :key="item.title" class="glass-card p-5 group cursor-default">
          <div class="flex items-center justify-between mb-3">
            <span class="text-3xl">{{ item.icon }}</span>
            <span class="text-2xl font-bold tabular-nums" :style="{ color: 'var(--text-primary)' }">{{ item.value }}</span>
          </div>
          <p class="text-sm font-medium" :style="{ color: 'var(--text-secondary)' }">{{ item.title }}</p>
          <p class="text-xs mt-0.5" :style="{ color: 'var(--text-muted)' }">{{ item.subtitle }}</p>
        </div>
      </div>
    </Spin>
    <div class="glass-card p-6">
      <h3 class="text-lg font-semibold mb-2" :style="{ color: 'var(--text-primary)' }">欢迎使用 TriCore 三核管理系统</h3>
      <p class="text-sm leading-relaxed" :style="{ color: 'var(--text-secondary)' }">
        集成 <span class="text-indigo-500">销售管理</span>、<span class="text-emerald-500">办公协同</span>、
        <span class="text-amber-500">库存管理</span> 三大核心业务模块。
      </p>
    </div>
  </div>
</template>
