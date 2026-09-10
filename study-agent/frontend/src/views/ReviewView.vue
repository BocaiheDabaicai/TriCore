<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { AlignLeft, BookOpen, Calendar, Clock, FileText, PieChart, Search } from 'lucide-vue-next'
import { listReadings } from '../api/readings'

// 回顾页：左侧筛选栏 + 主体列表；右下角悬浮统计
const router = useRouter()

const items = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    items.value = (await listReadings()).data
  } finally {
    loading.value = false
  }
})

const MODE_META = {
  close: { text: '精读', badge: 'badge-primary' },
  skim: { text: '泛读', badge: 'badge-secondary' },
}
const STATUS_META = {
  draft: { text: '草稿', badge: 'badge-warning' },
  done: { text: '完成', badge: 'badge-success' },
}

// 筛选：关键词（标题/作者/期刊/笔记）+ 类型（精读/泛读）
const keyword = ref('')
const modeFilter = ref('all')   // all / close / skim

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return items.value.filter((r) => {
    if (modeFilter.value !== 'all' && r.mode !== modeFilter.value) return false
    if (!kw) return true
    const hay = [r.title, r.author, r.journal, r.note].join(' ').toLowerCase()
    return hay.includes(kw)
  })
})

const modeCounts = computed(() => {
  const close = items.value.filter((r) => r.mode === 'close').length
  return { all: items.value.length, close, skim: items.value.length - close }
})

function resetFilter() {
  keyword.value = ''
  modeFilter.value = 'all'
}

// 统计：从列表即时算（列表按更新时间倒序，第一条即最近）
const stats = computed(() => {
  const list = items.value
  const total = list.length
  const closeCount = list.filter((r) => r.mode === 'close').length
  const doneCount = list.filter((r) => r.status === 'done').length
  const charTotal = list.reduce((sum, r) => sum + (r.note?.length || 0), 0)

  const now = new Date()
  const ym = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

  return {
    total,
    closeCount,
    skimCount: total - closeCount,
    doneCount,
    charTotal: charTotal.toLocaleString(),
    avgChars: total ? Math.round(charTotal / total).toLocaleString() : '0',
    completionPct: total ? Math.round((doneCount / total) * 100) : 0,
    monthNew: list.filter((r) => (r.created_at || '').startsWith(ym)).length,
    lastUpdated: list[0]?.updated_at?.slice(0, 10) ?? '—',
  }
})
</script>

<template>
  <div class="p-6">
    <div class="max-w-5xl mx-auto">
      <h1 class="text-2xl font-bold mb-1">回顾</h1>
      <p class="text-sm text-base-content/60 mb-6">写过的每一条笔记都在这里，点击查看详情</p>

      <div class="flex gap-8">
        <!-- 左侧：筛选栏（滚动时吸顶跟随，窄屏隐藏） -->
        <aside v-if="!loading && items.length" class="hidden md:block w-44 shrink-0">
          <div class="sticky top-6 flex flex-col gap-3">
            <label class="input input-sm">
              <Search class="w-3.5 h-3.5 opacity-40" />
              <input v-model="keyword" class="grow" placeholder="搜索笔记…" />
            </label>

            <nav class="flex flex-col gap-1">
              <button
                class="flex items-center px-3 py-2 rounded-xl text-sm transition-colors"
                :class="modeFilter === 'all' ? 'bg-primary/10 text-primary font-medium' : 'text-base-content/70 hover:bg-base-200'"
                @click="modeFilter = 'all'"
              >
                全部
                <span class="ml-auto text-xs opacity-50 tabular-nums">{{ modeCounts.all }}</span>
              </button>
              <button
                class="flex items-center px-3 py-2 rounded-xl text-sm transition-colors"
                :class="modeFilter === 'close' ? 'bg-primary/10 text-primary font-medium' : 'text-base-content/70 hover:bg-base-200'"
                @click="modeFilter = 'close'"
              >
                精读
                <span class="ml-auto text-xs opacity-50 tabular-nums">{{ modeCounts.close }}</span>
              </button>
              <button
                class="flex items-center px-3 py-2 rounded-xl text-sm transition-colors"
                :class="modeFilter === 'skim' ? 'bg-primary/10 text-primary font-medium' : 'text-base-content/70 hover:bg-base-200'"
                @click="modeFilter = 'skim'"
              >
                泛读
                <span class="ml-auto text-xs opacity-50 tabular-nums">{{ modeCounts.skim }}</span>
              </button>
            </nav>

            <span v-if="keyword || modeFilter !== 'all'" class="px-3 text-xs text-base-content/40 tabular-nums">
              筛出 {{ filtered.length }}/{{ items.length }} 条
            </span>
          </div>
        </aside>

        <!-- 右侧：回顾列表 -->
        <div class="flex-1 min-w-0">
          <div v-if="loading" class="flex justify-center py-20">
            <span class="loading loading-spinner"></span>
          </div>

          <div v-else-if="!items.length" class="text-center text-base-content/40 py-20">
            还没有研读记录，去「研读」页写第一条吧
          </div>

          <div v-else-if="!filtered.length" class="text-center text-base-content/40 py-16">
            没有符合筛选条件的记录
            <div class="mt-3">
              <button class="btn btn-xs btn-ghost" @click="resetFilter">清除筛选</button>
            </div>
          </div>

          <div v-else class="flex flex-col gap-3">
            <div
              v-for="r in filtered"
              :key="r.id"
              class="card bg-base-100 shadow hover:shadow-md transition-shadow cursor-pointer"
              @click="router.push(`/review/${r.id}`)"
            >
              <div class="card-body py-4">
                <div class="flex items-center justify-between gap-3">
                  <div class="font-medium truncate">{{ r.title }}</div>
                  <div class="flex gap-2 shrink-0">
                    <span class="badge badge-sm" :class="MODE_META[r.mode]?.badge">{{ MODE_META[r.mode]?.text }}</span>
                    <span class="badge badge-sm" :class="STATUS_META[r.status]?.badge">{{ STATUS_META[r.status]?.text }}</span>
                  </div>
                </div>
                <div class="text-xs text-base-content/50">{{ r.updated_at }} 更新</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右下角：悬浮统计——平时只露一个小圆点，悬停展开统计卡（窄屏隐藏） -->
    <div v-if="!loading && items.length" class="hidden lg:block fixed bottom-5 right-5 z-40 group">
      <!-- 收起态：角落小圆点提示 -->
      <div
        class="w-9 h-9 rounded-full bg-base-200 shadow-sm flex items-center justify-center
               transition-all duration-300 group-hover:opacity-0 group-hover:scale-75"
      >
        <PieChart class="w-4 h-4 text-base-content/40" />
      </div>

      <!-- 展开态：统计卡（从右下角展开；未悬停时透明且不挡点击） -->
      <div
        class="absolute bottom-0 right-0 w-56 rounded-2xl bg-base-200 p-4 shadow-md origin-bottom-right
               opacity-0 scale-95 pointer-events-none
               transition-all duration-300 group-hover:opacity-100 group-hover:scale-100 group-hover:pointer-events-auto"
      >
        <div class="text-xs text-base-content/40 mb-3">研读统计</div>

        <div class="flex flex-col gap-3 text-sm">
          <div class="flex items-center justify-between">
            <span class="flex items-center gap-1.5 text-xs text-base-content/50">
              <FileText class="w-3.5 h-3.5" />条目
            </span>
            <span class="tabular-nums font-medium">{{ stats.total }} 篇</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="flex items-center gap-1.5 text-xs text-base-content/50">
              <BookOpen class="w-3.5 h-3.5" />精读 / 泛读
            </span>
            <span class="tabular-nums font-medium">{{ stats.closeCount }} / {{ stats.skimCount }}</span>
          </div>

          <!-- 完成度：细进度条 -->
          <div>
            <div class="flex items-center justify-between text-xs text-base-content/50 mb-1">
              <span>完成 {{ stats.doneCount }}/{{ stats.total }}</span>
              <span class="tabular-nums">{{ stats.completionPct }}%</span>
            </div>
            <div class="h-1 rounded-full bg-base-300 overflow-hidden">
              <div class="h-full rounded-full bg-success/60" :style="{ width: stats.completionPct + '%' }"></div>
            </div>
          </div>

          <div class="divider my-0"></div>

          <div class="flex items-center justify-between">
            <span class="flex items-center gap-1.5 text-xs text-base-content/50">
              <AlignLeft class="w-3.5 h-3.5" />累计字数
            </span>
            <span class="tabular-nums font-medium">{{ stats.charTotal }} 字</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-base-content/40 pl-5">平均每篇</span>
            <span class="tabular-nums text-base-content/70">{{ stats.avgChars }} 字</span>
          </div>

          <div class="divider my-0"></div>

          <div class="flex items-center justify-between">
            <span class="flex items-center gap-1.5 text-xs text-base-content/50">
              <Calendar class="w-3.5 h-3.5" />本月新增
            </span>
            <span class="tabular-nums font-medium">{{ stats.monthNew }} 篇</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="flex items-center gap-1.5 text-xs text-base-content/50">
              <Clock class="w-3.5 h-3.5" />最近更新
            </span>
            <span class="tabular-nums text-base-content/70">{{ stats.lastUpdated }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
