<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { AlignLeft, BookOpen, Calendar, Clock, FileText, PieChart, Search, SlidersHorizontal } from 'lucide-vue-next'
import { listReadings } from '../api/readings'
import { MODE_META } from '../utils/reading'
import StarRating from '../components/StarRating.vue'

// 回顾页：检索行（搜索 + 高级筛选开关） + 主体列表；右下角悬浮统计
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

// 筛选组：类型（将来加「领域/标签」等筛选组时，在此追加一组配置）
const MODE_OPTIONS = [
  { value: 'all', text: '全部' },
  { value: 'close', text: '精读' },
  { value: 'skim', text: '泛读' },
]

// 筛选：关键词（标题/作者/期刊/标签/笔记）+ 类型（精读/泛读）+ 标签
const keyword = ref('')
const modeFilter = ref('all')   // all / close / skim
const tagFilter = ref('')       // '' 不限 / 具体标签

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return items.value.filter((r) => {
    if (modeFilter.value !== 'all' && r.mode !== modeFilter.value) return false
    if (tagFilter.value && r.tag !== tagFilter.value) return false
    if (!kw) return true
    const hay = [r.title, r.author, r.journal, r.tag, r.note].join(' ').toLowerCase()
    return hay.includes(kw)
  })
})

const modeCounts = computed(() => {
  const close = items.value.filter((r) => r.mode === 'close').length
  return { all: items.value.length, close, skim: items.value.length - close }
})

// 标签候选：从已有记录里收集（保持出现顺序，带条数）
const tagOptions = computed(() => {
  const m = new Map()
  for (const r of items.value) {
    if (r.tag) m.set(r.tag, (m.get(r.tag) || 0) + 1)
  }
  return [...m.entries()].map(([name, count]) => ({ name, count }))
})

function resetFilter() {
  keyword.value = ''
  modeFilter.value = 'all'
  tagFilter.value = ''
}

// 高级筛选面板开关；关闭时重置面板内的筛选——避免"看不见的筛选还在生效"
const filterOpen = ref(false)
watch(filterOpen, (open) => {
  if (!open) {
    modeFilter.value = 'all'
    tagFilter.value = ''
  }
})

const filtering = computed(() =>
  keyword.value.trim() !== '' || modeFilter.value !== 'all' || tagFilter.value !== '',
)

// 统计：从列表即时算（列表按更新时间倒序，第一条即最近）
const stats = computed(() => {
  const list = items.value
  const total = list.length
  const closeCount = list.filter((r) => r.mode === 'close').length
  const charTotal = list.reduce((sum, r) => sum + (r.note?.length || 0), 0)

  const now = new Date()
  const ym = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

  return {
    total,
    closeCount,
    skimCount: total - closeCount,
    charTotal: charTotal.toLocaleString(),
    avgChars: total ? Math.round(charTotal / total).toLocaleString() : '0',
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

      <div class="flex items-start gap-6">
        <!-- 高级筛选面板：开关打开才出现（滚动时吸顶跟随） -->
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 -translate-x-3"
          leave-active-class="transition duration-150 ease-in"
          leave-to-class="opacity-0 -translate-x-3"
        >
          <aside
            v-if="filterOpen && !loading && items.length"
            class="sticky top-6 w-72 shrink-0 rounded-2xl bg-base-200 p-4"
          >
            <div>
              <div class="text-xs text-base-content/40 mb-2 px-1">类型</div>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="opt in MODE_OPTIONS"
                  :key="opt.value"
                  class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border transition-colors"
                  :class="modeFilter === opt.value
                    ? 'bg-primary/10 text-primary border-primary/30 font-medium'
                    : 'border-base-300 text-base-content/60 hover:bg-base-300/50'"
                  @click="modeFilter = opt.value"
                >
                  {{ opt.text }}
                  <span class="tabular-nums opacity-60">{{ modeCounts[opt.value] }}</span>
                </button>
              </div>
              <div v-if="tagOptions.length" class="mt-3">
                <div class="text-xs text-base-content/40 mb-2 px-1">标签</div>
                <div class="flex flex-wrap gap-1.5">
                  <button
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border transition-colors"
                    :class="tagFilter === ''
                      ? 'bg-primary/10 text-primary border-primary/30 font-medium'
                      : 'border-base-300 text-base-content/60 hover:bg-base-300/50'"
                    @click="tagFilter = ''"
                  >
                    全部
                  </button>
                  <button
                    v-for="t in tagOptions"
                    :key="t.name"
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border transition-colors"
                    :class="tagFilter === t.name
                      ? 'bg-primary/10 text-primary border-primary/30 font-medium'
                      : 'border-base-300 text-base-content/60 hover:bg-base-300/50'"
                    @click="tagFilter = t.name"
                  >
                    {{ t.name }}
                    <span class="tabular-nums opacity-60">{{ t.count }}</span>
                  </button>
                </div>
              </div>
            </div>
          </aside>
        </Transition>

        <div class="flex-1 min-w-0">
          <!-- 检索行：搜索框 + 高级筛选开关（开关控制左侧筛选面板的显隐） -->
          <div class="flex items-center gap-3">
            <label class="input input-sm flex-1">
              <Search class="w-3.5 h-3.5 opacity-40" />
              <input v-model="keyword" class="grow" placeholder="搜索笔记…" />
            </label>

            <label
              v-if="!loading && items.length"
              class="hidden lg:flex items-center gap-2 shrink-0 cursor-pointer select-none"
            >
              <SlidersHorizontal class="w-4 h-4 text-base-content/40" />
              <span class="text-sm text-base-content/70">高级筛选</span>
              <input v-model="filterOpen" type="checkbox" class="toggle toggle-sm" />
            </label>
          </div>

          <div v-if="filtering" class="mt-2 text-xs text-base-content/40 tabular-nums">
            筛出 {{ filtered.length }}/{{ items.length }} 条
          </div>

          <div class="mt-4">
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
                      <span v-if="r.tag" class="badge badge-sm badge-outline">{{ r.tag }}</span>
                    </div>
                  </div>
                  <!-- 第二行：左边更新时间 + 小领域（没有就不显示），右边评分（没打分就不显示） -->
                  <div class="flex items-center justify-between gap-3">
                    <div class="flex items-center gap-x-2 gap-y-1 flex-wrap min-w-0 text-xs text-base-content/50">
                      <span class="shrink-0">{{ r.updated_at }} 更新</span>
                      <span
                        v-for="d in r.domains"
                        :key="d"
                        class="badge badge-xs badge-ghost text-base-content/60"
                      >
                        {{ d }}
                      </span>
                    </div>
                    <StarRating v-if="r.rating" :value="r.rating" size="sm" class="shrink-0" />
                  </div>
                </div>
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
