<script setup>
import { computed, ref } from 'vue'
import { Star } from 'lucide-vue-next'

// 星级显示：5 星 + 半星（每半星 1 分，10 分制）
// interactive：可交互（悬停预览、点左半/右半选分、再点同一颗 = 取消），变化时 emit('change', 分数)
// 只读时纯展示（回顾列表用）
const props = defineProps({
  value: { type: Number, default: 0 },
  interactive: { type: Boolean, default: false },
  size: { type: String, default: 'md' },   // md 详情页 / sm 列表
  showScore: { type: Boolean, default: true },
})

const emit = defineEmits(['change'])

const hover = ref(0)
// 展示用分数：交互时悬停预览，否则就是传入值
const shown = computed(() => (props.interactive && hover.value ? hover.value : props.value))

const starClass = computed(() => (props.size === 'sm' ? 'w-4 h-4' : 'w-5 h-5'))

// 第 i 颗星（1-5）的实心占比：满 2 分、半颗 1 分
function fill(i) {
  if (shown.value >= i * 2) return 100
  if (shown.value === i * 2 - 1) return 50
  return 0
}

// 由鼠标位置算分：左半 = 单数分，右半 = 双数分
function valueFromEvent(i, e) {
  const rect = e.currentTarget.getBoundingClientRect()
  return (i - 1) * 2 + (e.clientX - rect.left < rect.width / 2 ? 1 : 2)
}

function onMove(i, e) {
  if (props.interactive) hover.value = valueFromEvent(i, e)
}

function onClick(i, e) {
  if (!props.interactive) return
  const v = valueFromEvent(i, e)
  emit('change', v === props.value ? 0 : v)   // 再点同一颗 = 取消打分
}
</script>

<template>
  <div
    class="flex items-center"
    :title="interactive ? '点击打分，再点同一颗取消（左半 / 右半各 1 分）' : `${shown} / 10`"
    @mouseleave="hover = 0"
  >
    <component
      :is="interactive ? 'button' : 'span'"
      v-for="i in 5"
      :key="i"
      :type="interactive ? 'button' : null"
      class="relative"
      :class="[starClass, interactive ? 'cursor-pointer' : '']"
      @mousemove="onMove(i, $event)"
      @click="onClick(i, $event)"
    >
      <Star :class="starClass" class="text-base-content/25" />
      <!-- 实心层盖在空星上，按占比裁切宽度实现半星 -->
      <div class="absolute inset-0 overflow-hidden transition-[width] duration-100" :style="{ width: fill(i) + '%' }">
        <Star :class="starClass" class="fill-amber-400 text-amber-400" />
      </div>
    </component>
    <span
      v-if="showScore"
      class="ml-1.5 tabular-nums"
      :class="[size === 'sm' ? 'text-xs' : 'text-sm', shown ? 'text-base-content/70' : 'text-base-content/30']"
    >
      {{ shown }} / 10
    </span>
  </div>
</template>
