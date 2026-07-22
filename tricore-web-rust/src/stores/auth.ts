import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)

  const isLoggedIn = computed(() => !!token.value)
  const currentUser = computed(() => user.value)

  async function login(employee_no: string, password: string) {
    const res: any = await authAPI.login(employee_no, password)
    const data = res?.data || res
    token.value = data.token
    user.value = data.user
    localStorage.setItem('token', data.token)
    return data
  }

  async function fetchCurrentUser() {
    if (!token.value) return
    try {
      const res: any = await authAPI.me()
      user.value = res?.data || res
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isLoggedIn, currentUser, login, fetchCurrentUser, logout }
})
