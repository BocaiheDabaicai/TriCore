import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/pages/dashboard/index.vue'),
          meta: { title: '工作台' },
        },
        {
          path: 'sales',
          name: 'Sales',
          component: () => import('@/pages/sales/index.vue'),
          meta: { title: '销售管理' },
        },
        {
          path: 'oa',
          name: 'OA',
          component: () => import('@/pages/oa/index.vue'),
          meta: { title: '办公协同' },
        },
        {
          path: 'inventory',
          name: 'Inventory',
          component: () => import('@/pages/inventory/index.vue'),
          meta: { title: '库存管理' },
        },
      ],
    },
  ],
})

export default router
