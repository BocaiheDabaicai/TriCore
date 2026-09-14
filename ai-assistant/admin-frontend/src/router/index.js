import { createRouter, createWebHistory } from 'vue-router'

// 路由 = 页面地图：路径 ↔ 视图组件；懒加载（() => import）让每个页面单独打包，首屏只加载当前页
const routes = [
  { path: '/', name: 'overview', component: () => import('../views/OverviewView.vue'), meta: { title: '总览' } },
  { path: '/services', name: 'services', component: () => import('../views/ServicesView.vue'), meta: { title: '服务管理' } },
  { path: '/architecture', name: 'architecture', component: () => import('../views/architecture/ArchitectureView.vue'), meta: { title: '架构图' } },
  { path: '/kb/upload', name: 'kb-upload', component: () => import('../views/kb/UploadView.vue'), meta: { title: '上传知识' } },
  { path: '/kb/list', name: 'kb-list', component: () => import('../views/kb/KnowledgeListView.vue'), meta: { title: '知识列表' } },
  { path: '/kb/missed', name: 'kb-missed', component: () => import('../views/kb/MissedView.vue'), meta: { title: '未命中问题' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 切页时同步浏览器标签页标题
router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} · 企业AI助手管理端` : '企业AI助手 · 管理端'
})

export default router
