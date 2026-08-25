import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.message || error.message || '请求失败'
    console.error('API Error:', msg)
    return Promise.reject(error)
  },
)

// ═══════════════════════════════════════════════════════════
// Sales — 销售模块
// ═══════════════════════════════════════════════════════════

export const salesAPI = {
  // Auth
  login: (data: { username: string; password: string }) =>
    api.post('/sales/auth/login', data),

  // Users
  listUsers: (params?: { role?: string; page?: number; per_page?: number }) =>
    api.get('/sales/users', { params }),
  getUser: (id: string) => api.get(`/sales/users/${id}`),
  createUser: (data: Record<string, unknown>) => api.post('/sales/users', data),
  updateUser: (id: string, data: Record<string, unknown>) => api.put(`/sales/users/${id}`, data),

  // Products
  listProducts: (params?: { category?: string; page?: number; per_page?: number }) =>
    api.get('/sales/products', { params }),
  getProduct: (id: string) => api.get(`/sales/products/${id}`),
  createProduct: (data: Record<string, unknown>) => api.post('/sales/products', data),
  updateProduct: (id: string, data: Record<string, unknown>) => api.put(`/sales/products/${id}`, data),

  // Orders
  listOrders: (params?: { status?: string; customer_id?: string; page?: number; per_page?: number }) =>
    api.get('/sales/orders', { params }),
  getOrder: (id: string) => api.get(`/sales/orders/${id}`),
  createOrder: (data: Record<string, unknown>) => api.post('/sales/orders', data),
  updateOrderStatus: (id: string, status: string) =>
    api.patch(`/sales/orders/${id}/status`, { status }),

  // Bundles
  listBundles: (params?: { page?: number; per_page?: number }) =>
    api.get('/sales/bundles', { params }),
  getBundle: (id: string) => api.get(`/sales/bundles/${id}`),
  createBundle: (data: Record<string, unknown>) => api.post('/sales/bundles', data),

  // Returns
  listReturns: (params?: { page?: number; per_page?: number }) =>
    api.get('/sales/returns', { params }),
  getReturn: (id: string) => api.get(`/sales/returns/${id}`),
  createReturn: (data: Record<string, unknown>) => api.post('/sales/returns', data),
  updateReturnStatus: (id: string, status: string) =>
    api.patch(`/sales/returns/${id}/status`, { status }),

  // Dashboard
  getDashboard: () => api.get('/sales/dashboard'),
}

// ═══════════════════════════════════════════════════════════
// OA — 办公模块
// ═══════════════════════════════════════════════════════════

export const oaAPI = {
  // Employees
  listEmployees: (params?: { department?: string; status?: string; page?: number; per_page?: number }) =>
    api.get('/oa/employees', { params }),
  getEmployee: (id: string) => api.get(`/oa/employees/${id}`),
  createEmployee: (data: Record<string, unknown>) => api.post('/oa/employees', data),
  updateEmployee: (id: string, data: Record<string, unknown>) => api.put(`/oa/employees/${id}`, data),

  // Workflows
  listWorkflows: (params?: { status?: string; creator_id?: string; page?: number; per_page?: number }) =>
    api.get('/oa/workflows', { params }),
  getWorkflow: (id: string) => api.get(`/oa/workflows/${id}`),
  createWorkflow: (data: Record<string, unknown>) => api.post('/oa/workflows', data),
  updateWorkflow: (id: string, data: Record<string, unknown>) => api.put(`/oa/workflows/${id}`, data),
  submitWorkflow: (id: string) => api.post(`/oa/workflows/${id}/submit`),
  getSteps: (id: string) => api.get(`/oa/workflows/${id}/steps`),
  reviewStep: (wfId: string, stepId: string, data: Record<string, unknown>) =>
    api.post(`/oa/workflows/${wfId}/steps/${stepId}/review`, data),

  // Archives
  listArchives: (params?: { page?: number; per_page?: number }) =>
    api.get('/oa/archives', { params }),
  getArchive: (id: string) => api.get(`/oa/archives/${id}`),

  // Dashboard
  getDashboard: () => api.get('/oa/dashboard'),
}

// ═══════════════════════════════════════════════════════════
// Inventory — 库存模块
// ═══════════════════════════════════════════════════════════

export const inventoryAPI = {
  // Warehouses
  listWarehouses: () => api.get('/inventory/warehouses'),
  getWarehouse: (id: string) => api.get(`/inventory/warehouses/${id}`),
  createWarehouse: (data: Record<string, unknown>) => api.post('/inventory/warehouses', data),
  updateWarehouse: (id: string, data: Record<string, unknown>) => api.put(`/inventory/warehouses/${id}`, data),

  // Stock In
  listStockIn: (params?: { status?: string; warehouse_id?: string; page?: number; per_page?: number }) =>
    api.get('/inventory/stock-in', { params }),
  getStockIn: (id: string) => api.get(`/inventory/stock-in/${id}`),
  createStockIn: (data: Record<string, unknown>) => api.post('/inventory/stock-in', data),
  verifyStockIn: (id: string, data: Record<string, unknown>) => api.put(`/inventory/stock-in/${id}/verify`, data),
  completeStockIn: (id: string) => api.put(`/inventory/stock-in/${id}/complete`),

  // Stock Out
  listStockOut: (params?: { status?: string; warehouse_id?: string; page?: number; per_page?: number }) =>
    api.get('/inventory/stock-out', { params }),
  getStockOut: (id: string) => api.get(`/inventory/stock-out/${id}`),
  createStockOut: (data: Record<string, unknown>) => api.post('/inventory/stock-out', data),
  shipStockOut: (id: string, data: Record<string, unknown>) => api.put(`/inventory/stock-out/${id}/ship`, data),
  deliverStockOut: (id: string) => api.put(`/inventory/stock-out/${id}/deliver`),

  // Issues
  listIssues: (params?: { status?: string; severity?: string; page?: number; per_page?: number }) =>
    api.get('/inventory/issues', { params }),
  getIssue: (id: string) => api.get(`/inventory/issues/${id}`),
  createIssue: (data: Record<string, unknown>) => api.post('/inventory/issues', data),
  updateIssue: (id: string, data: Record<string, unknown>) => api.put(`/inventory/issues/${id}`, data),
  resolveIssue: (id: string, data: { resolution: string }) => api.put(`/inventory/issues/${id}/resolve`, data),

  // Products
  listProducts: () => api.get('/inventory/products'),

  // Dashboard
  getDashboard: () => api.get('/inventory/dashboard'),
}

export default api
