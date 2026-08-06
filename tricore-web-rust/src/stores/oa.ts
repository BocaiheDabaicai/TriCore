import { defineStore } from 'pinia'
import { ref } from 'vue'
import { oaAPI } from '@/services/oa'

export const useOAStore = defineStore('oa', () => {
  const employees = ref<any[]>([])
  const workflows = ref<any[]>([])
  const loading = ref(false)

  async function fetchEmployees() {
    loading.value = true
    try {
      const res: any = await oaAPI.listEmployees({ per_page: 100 })
      employees.value = res?.data?.data || res?.data || []
    } finally { loading.value = false }
  }

  async function fetchWorkflows() {
    const res: any = await oaAPI.listWorkflows({ per_page: 50 })
    workflows.value = res?.data?.data || res?.data || []
  }

  return { employees, workflows, loading, fetchEmployees, fetchWorkflows }
})
