import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface SalesOrder {
  id: string
  orderNo: string
  customerName: string
  amount: number
  status: string
}

export const useSalesStore = defineStore('sales', () => {
  const orders = ref<SalesOrder[]>([])
  const loading = ref(false)

  async function fetchOrders() {
    loading.value = true
    try {
      const { salesAPI } = await import('@/services/api')
      const res = await salesAPI.healthCheck()
      console.log('Sales health:', res)
    } finally {
      loading.value = false
    }
  }

  return { orders, loading, fetchOrders }
})
