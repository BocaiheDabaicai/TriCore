import { createRouter, createWebHistory } from 'vue-router'

// 扁平路由 + 懒加载（和管理端同一套写法）
const routes = [
  { path: '/', name: 'console', component: () => import('../views/ConsoleView.vue'), meta: { title: '执行台' } },
  { path: '/shots', name: 'shots', component: () => import('../views/ShotsView.vue'), meta: { title: '截图资料库' } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} · 办公自动化操作台` : '办公自动化操作台'
})

export default router
