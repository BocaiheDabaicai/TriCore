import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Employee {
  id: string
  name: string
  department: string
  position: string
  email: string
}

export const useOAStore = defineStore('oa', () => {
  const employees = ref<Employee[]>([])
  const loading = ref(false)

  async function fetchEmployees() {
    loading.value = true
    try {
      const { oaAPI } = await import('@/services/api')
      const res = await oaAPI.healthCheck()
      console.log('OA health:', res)
    } finally {
      loading.value = false
    }
  }

  return { employees, loading, fetchEmployees }
})
