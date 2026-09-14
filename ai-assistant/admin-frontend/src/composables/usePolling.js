import { onMounted, onUnmounted } from 'vue'

// 轮询：挂载时先执行一次 fn，之后每 interval 毫秒执行一次；组件卸载自动停止
// 注意：只能在组件 setup 顶层同步调用（内部依赖 onMounted / onUnmounted）
export function usePolling(fn, interval = 5000) {
  let timer = null
  onMounted(() => {
    fn()
    timer = setInterval(fn, interval)
  })
  onUnmounted(() => clearInterval(timer))
}
