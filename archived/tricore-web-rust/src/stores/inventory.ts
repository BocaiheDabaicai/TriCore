import { defineStore } from 'pinia'
import { ref } from 'vue'
import { inventoryAPI } from '@/services/inventory'

export const useInventoryStore = defineStore('inventory', () => {
  const products = ref<any[]>([])
  const stockIn = ref<any[]>([])
  const stockOut = ref<any[]>([])
  const issues = ref<any[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const [p, si, so, iss]: any[] = await Promise.all([
        inventoryAPI.listProducts(),
        inventoryAPI.listStockIn({ per_page: 50 }),
        inventoryAPI.listStockOut({ per_page: 50 }),
        inventoryAPI.listIssues({ per_page: 50 }),
      ])
      products.value = p?.data || []
      stockIn.value = si?.data?.data || si?.data || []
      stockOut.value = so?.data?.data || so?.data || []
      issues.value = iss?.data?.data || iss?.data || []
    } finally { loading.value = false }
  }

  return { products, stockIn, stockOut, issues, loading, fetchAll }
})
