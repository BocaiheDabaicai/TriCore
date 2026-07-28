<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Spin, Tag } from 'ant-design-vue'
import {
  ShoppingCartOutlined, TeamOutlined, AppstoreOutlined,
  FileTextOutlined, AlertOutlined, CheckCircleOutlined,
  AuditOutlined, DatabaseOutlined, SettingOutlined,
  RobotOutlined, ArrowUpOutlined, RightOutlined,
} from '@ant-design/icons-vue'
import { salesAPI, oaAPI, inventoryAPI, regulationsAPI } from '@/services/api'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'

const router = useRouter()
const loading = ref(true)

// ── Theme ──
const getIsDark = () => (localStorage.getItem('theme') || 'dark') === 'dark'
const isDark = ref(getIsDark())

// Watch theme toggle from MainLayout
const themeObserver = new MutationObserver(() => { isDark.value = getIsDark() })
onMounted(() => {
  const el = document.documentElement
  if (el) themeObserver.observe(el, { attributes: true, attributeFilter: ['data-theme'] })
})
onUnmounted(() => themeObserver.disconnect())

watch(isDark, () => {
  orderChart?.dispose()
  inventoryChart?.dispose()
  orderChart = null
  inventoryChart = null
  initCharts()
})

// ── Stats ──
const stats = ref([
  { title: '销售订单', value: 0, icon: ShoppingCartOutlined, color: '#6c5ce7', bg: 'rgba(108,92,231,0.1)', trend: '+12%' },
  { title: '在职员工', value: 0, icon: TeamOutlined, color: '#00b894', bg: 'rgba(0,184,148,0.1)', trend: '+3%' },
  { title: '商品种类', value: 0, icon: AppstoreOutlined, color: '#fdcb6e', bg: 'rgba(253,203,110,0.15)', trend: '活跃' },
  { title: '待审流程', value: 0, icon: FileTextOutlined, color: '#e17055', bg: 'rgba(225,112,85,0.1)', trend: '处理中' },
  { title: '库存预警', value: 0, icon: AlertOutlined, color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', trend: '需关注' },
  { title: '规章制度', value: 0, icon: CheckCircleOutlined, color: '#74b9ff', bg: 'rgba(116,185,255,0.1)', trend: '文件数' },
])
const extraInfo = ref({ total_revenue: '0', total_stock_in: 0, total_stock_out: 0, open_issues: 0 })

// ── Charts ──
const orderChartEl = ref<HTMLElement | null>(null)
const inventoryChartEl = ref<HTMLElement | null>(null)
let orderChart: echarts.ECharts | null = null
let inventoryChart: echarts.ECharts | null = null

const orderStatusData = ref<any[]>([])
const productData = ref<any[]>([])

const chartTextColor = () => isDark.value ? '#9498b0' : '#666'
const chartGridColor = () => isDark.value ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)'

const initCharts = async () => {
  await nextTick()
  const t = chartTextColor()
  const g = chartGridColor()
  if (orderChartEl.value) {
    orderChart = echarts.init(orderChartEl.value, isDark.value ? 'dark' : undefined)
    orderChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 单 ({d}%)' },
      legend: { bottom: 0, textStyle: { color: t, fontSize: 11 } },
      series: [{
        type: 'pie', radius: ['55%', '78%'], center: ['50%', '45%'],
        avoidLabelOverlap: false, padAngle: 2, itemStyle: { borderRadius: 6, borderColor: 'transparent', borderWidth: 3 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data: orderStatusData.value,
      }],
      color: ['#6c5ce7', '#74b9ff', '#00b894', '#fdcb6e', '#e17055', '#a78bfa'],
    })
  }
  if (inventoryChartEl.value) {
    inventoryChart = echarts.init(inventoryChartEl.value, isDark.value ? 'dark' : undefined)
    const names = productData.value.slice(0, 8).map((p: any) => p.name)
    const values = productData.value.slice(0, 8).map((p: any) => p.quantity)
    const dangerColor = isDark.value ? '#e17055' : '#d63031'
    const warnColor = isDark.value ? '#fdcb6e' : '#e17055'
    const okColor = isDark.value ? '#00b894' : '#00b894'
    const colors = values.map((v: number) => v < 50 ? dangerColor : v < 200 ? warnColor : okColor)
    inventoryChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 8, right: 20, top: 10, bottom: 24 },
      xAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, splitLine: { lineStyle: { color: g } } },
      yAxis: { type: 'category', data: names.reverse(), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: t, fontSize: 11, width: 80, overflow: 'truncate' } },
      series: [{
        type: 'bar', data: values.reverse().map((v, i) => ({ value: v, itemStyle: { color: colors.reverse()[i], borderRadius: [0, 4, 4, 0] } })),
        barWidth: 14, label: { show: true, position: 'right', color: t, fontSize: 11, formatter: '{c}' },
      }],
    })
  }
}

const resizeCharts = () => { orderChart?.resize(); inventoryChart?.resize() }

const statusLabels: Record<string, string> = { pending: '待处理', confirmed: '已确认', processing: '处理中', shipped: '已发货', delivered: '已交付', cancelled: '已取消' }
const statusColors: Record<string, string> = { pending: '#6c5ce7', confirmed: '#74b9ff', processing: '#fdcb6e', shipped: '#00b894', delivered: '#00b894', cancelled: '#e17055' }

onMounted(async () => {
  try {
    const [s, o, i, r] = await Promise.allSettled([
      salesAPI.getDashboard(), oaAPI.getDashboard(), inventoryAPI.getDashboard(),
      regulationsAPI.listFiles({ per_page: 1 }).catch(() => ({ data: { total: 0 } })),
    ])
    if (s.status === 'fulfilled') {
      const d = (s.value as any)?.data || s.value
      stats.value[0].value = d?.total_orders ?? 0
      orderStatusData.value = (d?.orders_by_status || []).map((x: any) => ({
        name: statusLabels[x.status] || x.status, value: Number(x.count), itemStyle: { color: statusColors[x.status] || '#6c5ce7' }
      }))
    }
    if (o.status === 'fulfilled') {
      const d = (o.value as any)?.data || o.value
      stats.value[1].value = d?.total_employees ?? 0
      stats.value[3].value = d?.pending_workflows ?? 0
    }
    if (i.status === 'fulfilled') {
      const d = (i.value as any)?.data || i.value
      stats.value[2].value = d?.total_products ?? 0
      stats.value[4].value = d?.low_stock_count ?? 0
      extraInfo.value.total_stock_in = d?.total_stock_in ?? 0
      extraInfo.value.total_stock_out = d?.total_stock_out ?? 0
      extraInfo.value.open_issues = d?.open_issues ?? 0
    }
    // Load products for inventory chart
    try {
      const res: any = await inventoryAPI.listProducts()
      productData.value = res?.data || []
    } catch { /* ignore */ }
    // Load reg files count
    if (r.status === 'fulfilled') {
      const d = (r.value as any)?.data
      stats.value[5].value = d?.total ?? d?.length ?? d?.data?.length ?? 0
      stats.value[5].title = '规章制度'
    }
    await initCharts()
  } finally { loading.value = false }
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  orderChart?.dispose()
  inventoryChart?.dispose()
})

const modules = [
  { key: '/sales', icon: ShoppingCartOutlined, color: '#6c5ce7', label: '销售管理', desc: '订单 · 商品 · 分类 · 退单' },
  { key: '/oa', icon: AuditOutlined, color: '#00b894', label: '办公协同', desc: '审批流程 · 员工管理' },
  { key: '/inventory', icon: DatabaseOutlined, color: '#fdcb6e', label: '库存管理', desc: '入库 · 出库 · 盘点 · 问题' },
  { key: '/master-data/customers', icon: SettingOutlined, color: '#74b9ff', label: '基础数据', desc: '客户 · 部门 · 车辆 · 仓库' },
  { key: '/regulations', icon: FileTextOutlined, color: '#a78bfa', label: '规章制度', desc: '文件 · 分类 · 归档' },
  { key: '/ai/config', icon: RobotOutlined, color: '#e17055', label: 'AI 助手', desc: '配置 · 智能问答' },
]
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">工作台</h2>
      <p>TriCore 三核管理系统 — 核心业务概览</p>
    </div>

    <Spin :spinning="loading">
      <!-- ═══ Stat Cards ═══ -->
      <div class="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-5">
        <div v-for="item in stats" :key="item.title" class="glass-card p-5 stat-card">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-xs font-medium mb-2" :style="{ color: 'var(--text-muted)', letterSpacing: '0.5px' }">{{ item.title }}</p>
              <p class="text-2xl font-bold tracking-tight" :style="{ color: 'var(--text-primary)' }">{{ typeof item.value === 'number' ? item.value.toLocaleString() : item.value }}</p>
            </div>
            <div class="stat-icon-circle" :style="{ background: item.bg, color: item.color }">
              <component :is="item.icon" />
            </div>
          </div>
          <div class="flex items-center gap-1.5 mt-3 pt-3 border-t" :style="{ borderColor: 'var(--border-subtle)' }">
            <div class="w-1.5 h-1.5 rounded-full" :style="{ background: item.color }"></div>
            <span class="text-xs" :style="{ color: 'var(--text-muted)' }">{{ item.trend }}</span>
          </div>
        </div>
      </div>

      <!-- ═══ Charts Row ═══ -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
        <div class="glass-card p-5">
          <h3 class="text-sm font-semibold mb-1" :style="{ color: 'var(--text-primary)' }">订单状态分布</h3>
          <p class="text-xs mb-3" :style="{ color: 'var(--text-muted)' }">各状态订单数量占比</p>
          <div ref="orderChartEl" class="w-full" style="height: 260px"></div>
        </div>
        <div class="glass-card p-5">
          <h3 class="text-sm font-semibold mb-1" :style="{ color: 'var(--text-primary)' }">商品库存水平</h3>
          <p class="text-xs mb-3" :style="{ color: 'var(--text-muted)' }">活跃商品库存数量（红: &lt;50 ⚠）</p>
          <div v-if="productData.length === 0" class="flex items-center justify-center text-xs" :style="{ height: '260px', color: 'var(--text-muted)' }">暂无商品数据</div>
          <div v-else ref="inventoryChartEl" class="w-full" style="height: 260px"></div>
        </div>
      </div>

      <!-- ═══ Extra Info Bar ═══ -->
      <div class="glass-card p-4 mb-5">
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div>
            <p class="text-xs mb-1" style="color:var(--text-muted)">本月入库</p>
            <p class="text-lg font-bold" style="color:#00b894">{{ extraInfo.total_stock_in }}</p>
          </div>
          <div>
            <p class="text-xs mb-1" style="color:var(--text-muted)">本月出库</p>
            <p class="text-lg font-bold" style="color:#e17055">{{ extraInfo.total_stock_out }}</p>
          </div>
          <div>
            <p class="text-xs mb-1" style="color:var(--text-muted)">待解决问题</p>
            <p class="text-lg font-bold" :style="{ color: extraInfo.open_issues > 0 ? '#e17055' : 'var(--text-primary)' }">{{ extraInfo.open_issues }}</p>
          </div>
          <div>
            <p class="text-xs mb-1" style="color:var(--text-muted)">系统状态</p>
            <Tag color="green">运行正常</Tag>
          </div>
        </div>
      </div>

      <!-- ═══ Module Quick Access ═══ -->
      <div class="glass-card p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-sm font-semibold" :style="{ color: 'var(--text-primary)' }">功能模块</h3>
            <p class="text-xs" :style="{ color: 'var(--text-muted)' }">快速进入各业务系统</p>
          </div>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div v-for="mod in modules" :key="mod.label"
            class="module-card p-4 rounded-xl border cursor-pointer transition-all"
            :style="{ background: 'var(--input-bg)', borderColor: 'var(--border-subtle)' }"
            @click="router.push(mod.key)">
            <div class="w-9 h-9 rounded-lg flex items-center justify-center mb-3 transition-transform"
              :style="{ background: `${mod.color}18`, color: mod.color }">
              <component :is="mod.icon" :style="{ fontSize: '18px' }" />
            </div>
            <p class="text-sm font-semibold mb-0.5" :style="{ color: 'var(--text-primary)' }">{{ mod.label }}</p>
            <p class="text-xs leading-relaxed" :style="{ color: 'var(--text-muted)' }">{{ mod.desc }}</p>
          </div>
        </div>
      </div>
    </Spin>
  </div>
</template>

<style scoped>
.stat-card {
  transition: all 0.25s ease;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}
.module-card {
  transition: all 0.25s ease;
}
.module-card:hover {
  border-color: var(--accent) !important;
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}
.module-card:hover :deep(div:first-child) {
  transform: scale(1.08);
}
</style>
