import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(error)
    }
    const msg = error.response?.data?.message || error.message || '请求失败'
    console.error('API Error:', msg)
    return Promise.reject(error)
  },
)

export const authAPI = {
  login: (employee_no: string, password: string) =>
    api.post('/auth/login', { employee_no, password }),
  me: () => api.get('/auth/me'),
}

export const salesAPI = {
  login: (data: { username: string; password: string }) =>
    api.post('/sales/auth/login', data),
  listUsers: (params?: Record<string, unknown>) => api.get('/sales/users', { params }),
  getUser: (id: string) => api.get(`/sales/users/${id}`),
  createUser: (data: Record<string, unknown>) => api.post('/sales/users', data),
  updateUser: (id: string, data: Record<string, unknown>) => api.put(`/sales/users/${id}`, data),
  listProducts: (params?: Record<string, unknown>) => api.get('/sales/products', { params }),
  getProduct: (id: string) => api.get(`/sales/products/${id}`),
  createProduct: (data: Record<string, unknown>) => api.post('/sales/products', data),
  updateProduct: (id: string, data: Record<string, unknown>) => api.put(`/sales/products/${id}`, data),
  listOrders: (params?: Record<string, unknown>) => api.get('/sales/orders', { params }),
  getOrder: (id: string) => api.get(`/sales/orders/${id}`),
  createOrder: (data: Record<string, unknown>) => api.post('/sales/orders', data),
  updateOrder: (id: string, data: Record<string, unknown>) => api.put(`/sales/orders/${id}`, data),
  updateOrderStatus: (id: string, data: Record<string, unknown>) => api.patch(`/sales/orders/${id}/status`, data),
  listBundles: (params?: Record<string, unknown>) => api.get('/sales/bundles', { params }),
  getBundle: (id: string) => api.get(`/sales/bundles/${id}`),
  createBundle: (data: Record<string, unknown>) => api.post('/sales/bundles', data),
  listReturns: (params?: Record<string, unknown>) => api.get('/sales/returns', { params }),
  getReturn: (id: string) => api.get(`/sales/returns/${id}`),
  createReturn: (data: Record<string, unknown>) => api.post('/sales/returns', data),
  updateReturnStatus: (id: string, status: string) => api.patch(`/sales/returns/${id}/status`, { status }),
  getDashboard: () => api.get('/sales/dashboard'),
  // Categories
  listCategories: () => api.get('/sales/categories'),
  getCategory: (id: string) => api.get(`/sales/categories/${id}`),
  createCategory: (data: Record<string, unknown>) => api.post('/sales/categories', data),
  updateCategory: (id: string, data: Record<string, unknown>) => api.put(`/sales/categories/${id}`, data),
  deleteCategory: (id: string) => api.delete(`/sales/categories/${id}`),
}

export const oaAPI = {
  listEmployees: (params?: Record<string, unknown>) => api.get('/oa/employees', { params }),
  getEmployee: (id: string) => api.get(`/oa/employees/${id}`),
  createEmployee: (data: Record<string, unknown>) => api.post('/oa/employees', data),
  updateEmployee: (id: string, data: Record<string, unknown>) => api.put(`/oa/employees/${id}`, data),
  deleteEmployee: (id: string) => api.delete(`/oa/employees/${id}`),
  listWorkflows: (params?: Record<string, unknown>) => api.get('/oa/workflows', { params }),
  getWorkflow: (id: string) => api.get(`/oa/workflows/${id}`),
  createWorkflow: (data: Record<string, unknown>) => api.post('/oa/workflows', data),
  updateWorkflow: (id: string, data: Record<string, unknown>) => api.put(`/oa/workflows/${id}`, data),
  deleteWorkflow: (id: string) => api.delete(`/oa/workflows/${id}`),
  submitWorkflow: (id: string) => api.post(`/oa/workflows/${id}/submit`),
  getSteps: (id: string) => api.get(`/oa/workflows/${id}/steps`),
  reviewStep: (wfId: string, stepId: string, data: Record<string, unknown>) =>
    api.post(`/oa/workflows/${wfId}/steps/${stepId}/review`, data),
  listArchives: (params?: Record<string, unknown>) => api.get('/oa/archives', { params }),
  getArchive: (id: string) => api.get(`/oa/archives/${id}`),
  getDashboard: () => api.get('/oa/dashboard'),
}

export const inventoryAPI = {
  listWarehouses: () => api.get('/inventory/warehouses'),
  getWarehouse: (id: string) => api.get(`/inventory/warehouses/${id}`),
  createWarehouse: (data: Record<string, unknown>) => api.post('/inventory/warehouses', data),
  updateWarehouse: (id: string, data: Record<string, unknown>) => api.put(`/inventory/warehouses/${id}`, data),
  deleteWarehouse: (id: string) => api.delete(`/inventory/warehouses/${id}`),
  listStockIn: (params?: Record<string, unknown>) => api.get('/inventory/stock-in', { params }),
  getStockIn: (id: string) => api.get(`/inventory/stock-in/${id}`),
  createStockIn: (data: Record<string, unknown>) => api.post('/inventory/stock-in', data),
  verifyStockIn: (id: string, data: Record<string, unknown>) => api.put(`/inventory/stock-in/${id}/verify`, data),
  completeStockIn: (id: string) => api.put(`/inventory/stock-in/${id}/complete`),
  listStockOut: (params?: Record<string, unknown>) => api.get('/inventory/stock-out', { params }),
  getStockOut: (id: string) => api.get(`/inventory/stock-out/${id}`),
  createStockOut: (data: Record<string, unknown>) => api.post('/inventory/stock-out', data),
  shipStockOut: (id: string, data: Record<string, unknown>) => api.put(`/inventory/stock-out/${id}/ship`, data),
  deliverStockOut: (id: string) => api.put(`/inventory/stock-out/${id}/deliver`),
  listIssues: (params?: Record<string, unknown>) => api.get('/inventory/issues', { params }),
  getIssue: (id: string) => api.get(`/inventory/issues/${id}`),
  createIssue: (data: Record<string, unknown>) => api.post('/inventory/issues', data),
  updateIssue: (id: string, data: Record<string, unknown>) => api.put(`/inventory/issues/${id}`, data),
  resolveIssue: (id: string, data: { resolution: string }) => api.put(`/inventory/issues/${id}/resolve`, data),
  listProducts: () => api.get('/inventory/products'),
  getDashboard: () => api.get('/inventory/dashboard'),
}

export const masterDataAPI = {
  // Customers
  listCustomers: () => api.get('/master-data/customers'),
  getCustomer: (id: string) => api.get(`/master-data/customers/${id}`),
  createCustomer: (data: Record<string, unknown>) => api.post('/master-data/customers', data),
  updateCustomer: (id: string, data: Record<string, unknown>) => api.put(`/master-data/customers/${id}`, data),
  deleteCustomer: (id: string) => api.delete(`/master-data/customers/${id}`),
  // Departments
  listDepartments: () => api.get('/master-data/departments'),
  getDepartment: (id: string) => api.get(`/master-data/departments/${id}`),
  createDepartment: (data: Record<string, unknown>) => api.post('/master-data/departments', data),
  updateDepartment: (id: string, data: Record<string, unknown>) => api.put(`/master-data/departments/${id}`, data),
  deleteDepartment: (id: string) => api.delete(`/master-data/departments/${id}`),
  // Positions
  listPositions: () => api.get('/master-data/positions'),
  getPosition: (id: string) => api.get(`/master-data/positions/${id}`),
  createPosition: (data: Record<string, unknown>) => api.post('/master-data/positions', data),
  updatePosition: (id: string, data: Record<string, unknown>) => api.put(`/master-data/positions/${id}`, data),
  deletePosition: (id: string) => api.delete(`/master-data/positions/${id}`),
  // Vehicles
  listVehicles: () => api.get('/master-data/vehicles'),
  getVehicle: (id: string) => api.get(`/master-data/vehicles/${id}`),
  createVehicle: (data: Record<string, unknown>) => api.post('/master-data/vehicles', data),
  updateVehicle: (id: string, data: Record<string, unknown>) => api.put(`/master-data/vehicles/${id}`, data),
  deleteVehicle: (id: string) => api.delete(`/master-data/vehicles/${id}`),
}

export default api
