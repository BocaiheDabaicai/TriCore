<script setup>
import { computed, onMounted, ref } from 'vue'
import { ExternalLink } from 'lucide-vue-next'
import { listSources } from '../api/sources'

// 寻文：按类型汇总文献站点，点击卡片新窗口打开网站去找论文
const items = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    items.value = (await listSources()).data
  } finally {
    loading.value = false
  }
})

// 类型分组的泛读视角提示（来自 paper.md 记录 0003）
const GROUP_HINT = {
  'AI·计算机': '泛读视角：技术能用在什么管理场景？',
  'Web3·区块链': '泛读视角：治理机制 / 激励机制 / 信任机制',
}

// 按类型分组（保持数据里的类型出现顺序）
const groups = computed(() => {
  const map = new Map()
  for (const s of items.value) {
    if (!map.has(s.type)) map.set(s.type, [])
    map.get(s.type).push(s)
  }
  return [...map.entries()].map(([type, list]) => ({ type, list }))
})
</script>

<template>
  <div class="p-6">
    <div class="max-w-5xl mx-auto">
      <h1 class="text-2xl font-bold mb-1">寻文</h1>
      <p class="text-sm text-base-content/60 mb-6">按类型汇总的文献站点——点击卡片到对应网站去找论文</p>

      <div v-if="loading" class="flex justify-center py-20">
        <span class="loading loading-spinner"></span>
      </div>

      <div v-else-if="!items.length" class="text-center text-base-content/40 py-20">
        还没有收录站点
      </div>

      <div v-else class="flex flex-col gap-8">
        <section v-for="g in groups" :key="g.type">
          <div class="mb-3">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium">{{ g.type }}</span>
              <span class="text-xs text-base-content/40 tabular-nums">{{ g.list.length }}</span>
            </div>
            <div v-if="GROUP_HINT[g.type]" class="text-xs text-base-content/40 mt-0.5">
              {{ GROUP_HINT[g.type] }}
            </div>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <a
              v-for="s in g.list"
              :key="s.id"
              :href="s.url"
              target="_blank"
              rel="noopener"
              class="card bg-base-100 shadow hover:shadow-md transition-shadow"
            >
              <div class="card-body py-3.5 px-4 gap-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="font-medium truncate">{{ s.name }}</span>
                  <ExternalLink class="w-3.5 h-3.5 shrink-0 text-base-content/30" />
                </div>
                <div class="text-xs text-base-content/50 truncate">{{ s.note }}</div>
              </div>
            </a>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
