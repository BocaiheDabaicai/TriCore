import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Product {
  id: string
  sku: string
  name: string
  quantity: number
  price: number
}

export const useInventoryStore = defineStore('inventory', () => {
  const products = ref<Product[]>([])
  const loading = ref(false)

  async function fetchProducts() {
    loading.value = true
    try {
      const { inventoryAPI } = await import('@/services/api')
      const res = await inventoryAPI.healthCheck()
      console.log('Inventory health:', res)
    } finally {
      loading.value = false
    }
  }

  return { products, loading, fetchProducts }
})
