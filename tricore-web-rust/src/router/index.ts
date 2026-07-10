import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const MasterDataPage = () => import('@/pages/master-data/index.vue')

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
        {
          path: 'master-data/customers',
          name: 'MdCustomers',
          component: MasterDataPage,
          meta: { title: '客户管理' },
        },
        {
          path: 'master-data/departments',
          name: 'MdDepartments',
          component: MasterDataPage,
          meta: { title: '部门管理' },
        },
        {
          path: 'master-data/positions',
          name: 'MdPositions',
          component: MasterDataPage,
          meta: { title: '职位管理' },
        },
        {
          path: 'master-data/vehicles',
          name: 'MdVehicles',
          component: MasterDataPage,
          meta: { title: '车辆管理' },
        },
      ],
    },
  ],
})

export default router
