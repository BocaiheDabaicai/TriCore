<script setup>
import { LANG_META } from '../utils/reading'

// 语言切换小标：圆角方块显示当前语言（Cn/En），点击即在中英之间切换
// sm 小方块（详情页行内）；lg 与输入框同高（研读页标题行）
const SIZE_CLS = { sm: 'w-6 h-6 text-[10px]', lg: 'w-10 h-10 text-xs' }
defineProps({
  value: { type: String, default: 'zh' },
  size: { type: String, default: 'sm' },
})
const emit = defineEmits(['change'])
</script>

<template>
  <button
    type="button"
    class="shrink-0 rounded-md border flex items-center justify-center font-semibold cursor-pointer select-none transition-colors"
    :class="[SIZE_CLS[size], LANG_META[value]?.circle]"
    :title="value === 'zh' ? '中文文献 · 点击切为英文' : '英文文献 · 点击切为中文'"
    @click="emit('change', value === 'zh' ? 'en' : 'zh')"
  >
    {{ LANG_META[value]?.text }}
  </button>
</template>
