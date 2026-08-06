import { defineStore } from 'pinia'
import { ref } from 'vue'
import { salesAPI } from '@/services/sales'

export const useSalesStore = defineStore('sales', () => {
  const orders = ref<any[]>([])
  const products = ref<any[]>([])
  const dashboard = ref<any>(null)
  const loading = ref(false)

  async function fetchOrders() {
    loading.value = true
    try {
      const res: any = await salesAPI.listOrders({ per_page: 50 })
      orders.value = res?.data?.data || res?.data || []
    } finally { loading.value = false }
  }

  async function fetchProducts() {
    const res: any = await salesAPI.listProducts({ per_page: 100 })
    products.value = res?.data?.data || res?.data || []
  }

  async function fetchDashboard() {
    const res: any = await salesAPI.getDashboard()
    dashboard.value = res?.data || res
  }

  return { orders, products, dashboard, loading, fetchOrders, fetchProducts, fetchDashboard }
})
