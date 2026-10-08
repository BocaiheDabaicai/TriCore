import { onMounted, onUnmounted } from 'vue'

// 定时轮询：挂载时先立刻执行一次，再按间隔重复；卸载时自动清理
// 注意：只能在组件的 setup 顶层同步调用（内部用了 onMounted/onUnmounted）
export function usePolling(fn, interval = 5000) {
  let timer = null

  onMounted(async () => {
    await fn()
    timer = setInterval(fn, interval)
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })
}
