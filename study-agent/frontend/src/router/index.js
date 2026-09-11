import { createRouter, createWebHistory } from 'vue-router'

// 路由 = 页面地图；懒加载让每个页面单独打包
const routes = [
  { path: '/', name: 'study', component: () => import('../views/StudyView.vue'), meta: { title: '研读' } },
  { path: '/review', name: 'review', component: () => import('../views/ReviewView.vue'), meta: { title: '回顾' } },
  { path: '/review/:id', name: 'review-detail', component: () => import('../views/ReviewDetailView.vue'), meta: { title: '笔记详情' } },
  { path: '/sources', name: 'sources', component: () => import('../views/SourcesView.vue'), meta: { title: '寻文' } },
  { path: '/edit/:id', name: 'study-edit', component: () => import('../views/StudyView.vue'), meta: { title: '修改笔记' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 切页时同步浏览器标签页标题
router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} · 研读库` : '研读库'
})

export default router
