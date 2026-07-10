<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Spin } from 'ant-design-vue'
import {
  ShoppingCartOutlined,
  TeamOutlined,
  AppstoreOutlined,
  FileTextOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ArrowUpOutlined,
  AuditOutlined,
  DatabaseOutlined,
} from '@ant-design/icons-vue'
import { salesAPI, oaAPI, inventoryAPI } from '@/services/api'

const loading = ref(true)
const stats = ref([
  { title: '销售订单', value: 0, icon: ShoppingCartOutlined, color: '#6c5ce7', bg: 'rgba(108,92,231,0.1)', subtitle: '全部订单' },
  { title: '员工数量', value: 0, icon: TeamOutlined, color: '#00b894', bg: 'rgba(0,184,148,0.1)', subtitle: '在职员工' },
  { title: '商品种类', value: 0, icon: AppstoreOutlined, color: '#fdcb6e', bg: 'rgba(253,203,110,0.15)', subtitle: '活跃商品' },
  { title: '待处理流程', value: 0, icon: FileTextOutlined, color: '#e17055', bg: 'rgba(225,112,85,0.1)', subtitle: 'OA审批中' },
  { title: '库存预警', value: 0, icon: AlertOutlined, color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', subtitle: '低库存' },
  { title: '本月完成', value: 0, icon: CheckCircleOutlined, color: '#74b9ff', bg: 'rgba(116,185,255,0.1)', subtitle: '已交付' },
])

onMounted(async () => {
  try {
    const [s, o, i] = await Promise.allSettled([salesAPI.getDashboard(), oaAPI.getDashboard(), inventoryAPI.getDashboard()])
    if (s.status === 'fulfilled') { const d = (s.value as any)?.data || s.value; stats.value[0].value = d?.total_orders ?? 0; const del = d?.orders_by_status?.find((x: any) => x.status === 'delivered'); stats.value[5].value = del?.count ?? 0 }
    if (o.status === 'fulfilled') { const d = (o.value as any)?.data || o.value; stats.value[1].value = d?.total_employees ?? 0; stats.value[3].value = d?.pending_workflows ?? 0 }
    if (i.status === 'fulfilled') { const d = (i.value as any)?.data || i.value; stats.value[2].value = d?.total_products ?? 0; stats.value[4].value = d?.low_stock_count ?? 0 }
  } finally { loading.value = false }
})

const modules = [
  { icon: ShoppingCartOutlined, color: '#6c5ce7', bg: 'rgba(108,92,231,0.08)', label: '销售系统', desc: '订单管理 · 商品定价 · 捆绑销售 · 退单处理' },
  { icon: AuditOutlined, color: '#00b894', bg: 'rgba(0,184,148,0.08)', label: 'OA 系统', desc: '流程审批 · 员工管理 · 日程协同 · 公告通知' },
  { icon: DatabaseOutlined, color: '#fdcb6e', bg: 'rgba(253,203,110,0.12)', label: '库存系统', desc: '入库管理 · 出库追踪 · 库存盘点 · 预警通知' },
]
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">工作台</h2>
      <p>TriCore 三核管理系统 — 核心业务概览</p>
    </div>

    <Spin :spinning="loading">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-6">
        <div v-for="item in stats" :key="item.title" class="glass-card p-6">
          <div class="flex items-start gap-4">
            <div class="stat-icon-circle" :style="{ background: item.bg, color: item.color }">
              <component :is="item.icon" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-medium mb-1" :style="{ color: 'var(--text-muted)' }">{{ item.title }}</p>
              <p class="text-2xl font-bold tracking-tight" :style="{ color: 'var(--text-primary)' }">{{ item.value.toLocaleString() }}</p>
              <p class="text-xs mt-0.5 flex items-center gap-1" :style="{ color: 'var(--text-muted)' }">
                <ArrowUpOutlined :style="{ color: item.color, fontSize: '10px' }" />
                {{ item.subtitle }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Spin>

    <div class="glass-card p-7">
      <h3 class="text-lg font-bold mb-1" :style="{ color: 'var(--text-primary)' }">欢迎使用 TriCore</h3>
      <p class="text-sm leading-relaxed mb-5" :style="{ color: 'var(--text-secondary)' }">
        集成 <span style="color:#6c5ce7;font-weight:600">销售管理</span>、<span style="color:#00b894;font-weight:600">办公协同</span>、<span style="color:#fdcb6e;font-weight:600">库存管理</span> 三大核心业务模块。
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div v-for="mod in modules" :key="mod.label"
          class="p-5 rounded-xl border transition-all duration-200 hover:translate-y-[-2px]"
          :style="{ background: 'var(--input-bg)', borderColor: 'var(--border-subtle)' }">
          <div class="flex items-center gap-2 mb-2">
            <component :is="mod.icon" :style="{ color: mod.color, fontSize: '18px' }" />
            <span class="text-sm font-semibold" :style="{ color: 'var(--text-primary)' }">{{ mod.label }}</span>
          </div>
          <p class="text-xs leading-relaxed" :style="{ color: 'var(--text-muted)' }">{{ mod.desc }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
