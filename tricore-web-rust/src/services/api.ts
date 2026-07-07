import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  },
)

export const salesAPI = {
  healthCheck: () => api.get('/sales/health'),
}

export const oaAPI = {
  healthCheck: () => api.get('/oa/health'),
}

export const inventoryAPI = {
  healthCheck: () => api.get('/inventory/health'),
}

export default api
