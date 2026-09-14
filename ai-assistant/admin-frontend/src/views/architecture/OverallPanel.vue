<script setup>
import { CANVAS, CARD_W, CARD_H, GUARD_FRAME, ZONES, EDGES, JUNCTIONS } from '../../data/architecture'
import { cardClass, edgePath, rectStyle } from '../../utils/architecture'
import { STATUS_META } from '../../utils/meta'

// 总体视图：结构关系——卡片 = 服务（实时状态来自 manager），线 = 调用，大框 = manager 守护，虚线 = 规划
defineProps({
  nodes: { type: Array, required: true },
})
const emit = defineEmits(['select-node'])
</script>

<template>
  <div class="card bg-base-100 shadow">
    <div class="card-body">
      <div class="overflow-auto">
        <div class="relative" :style="{ width: CANVAS.w + 'px', height: CANVAS.h + 'px' }">
          <!-- 业务分区（浅色底） -->
          <div
            v-for="z in ZONES"
            :key="z.label"
            class="absolute rounded-2xl bg-base-200/50 border border-base-300"
            :style="rectStyle(z)"
          >
            <div class="absolute top-2 left-3 text-xs text-base-content/50">{{ z.label }}</div>
          </div>

          <!-- 大虚线框：manager 守护的全部进程（manager 卡片挂在框外下边缘） -->
          <div class="absolute rounded-3xl border-2 border-dashed border-base-content/20" :style="rectStyle(GUARD_FRAME)">
            <div class="absolute -top-2.5 left-4 px-2 text-xs text-base-content/40 bg-base-100 rounded">
              {{ GUARD_FRAME.label }}
            </div>
          </div>

          <!-- 连线层（SVG 在最底层之上、卡片之下） -->
          <svg class="absolute inset-0 pointer-events-none" :width="CANVAS.w" :height="CANVAS.h">
            <path
              v-for="(e, i) in EDGES"
              :key="i"
              :d="edgePath(e, nodes)"
              fill="none"
              stroke="currentColor"
              class="text-base-content/30"
              stroke-width="1.5"
              :stroke-dasharray="e.dashed ? '6 5' : ''"
            />
            <!-- 汇流点：多条线的汇集处 -->
            <circle
              v-for="(j, i) in JUNCTIONS"
              :key="'j' + i"
              :cx="j.x"
              :cy="j.y"
              r="4"
              fill="currentColor"
              class="text-base-content/40"
            />
          </svg>

          <!-- 节点卡片 -->
          <button
            v-for="n in nodes"
            :key="n.key"
            class="absolute rounded-xl border shadow-sm text-left px-3 py-2 transition-shadow hover:shadow-md"
            :class="cardClass(n)"
            :style="{ left: n.x + 'px', top: n.y + 'px', width: CARD_W + 'px', height: CARD_H + 'px' }"
            @click="emit('select-node', n)"
          >
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full shrink-0" :class="STATUS_META[n.status]?.dot"></span>
              <span class="text-sm font-medium truncate">{{ n.cnName }}</span>
            </div>
            <div class="text-[11px] text-base-content/45 truncate">{{ n.sub }}</div>
          </button>
        </div>
      </div>

      <!-- 图例 -->
      <div class="flex flex-wrap items-center gap-5 mt-2 text-xs text-base-content/50">
        <span class="flex items-center gap-2"><svg width="34" height="8"><line x1="0" y1="4" x2="34" y2="4" stroke="currentColor" stroke-width="1.5" /></svg>调用</span>
        <span class="flex items-center gap-2"><svg width="34" height="8"><line x1="0" y1="4" x2="34" y2="4" stroke="currentColor" stroke-width="1.5" stroke-dasharray="6 5" /></svg>规划 / 未接入</span>
        <span class="flex items-center gap-2"><svg width="10" height="8"><circle cx="5" cy="4" r="3.5" fill="currentColor" /></svg>汇流点</span>
        <span class="flex items-center gap-2">
          <span class="inline-block w-8 h-4 rounded border-2 border-dashed border-base-content/30"></span>manager 守护范围
        </span>
        <span class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-success"></span>运行中</span>
        <span class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-error"></span>异常</span>
        <span class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-base-content/30"></span>停止 / 未知</span>
      </div>
    </div>
  </div>
</template>
