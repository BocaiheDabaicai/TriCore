import api from './http'

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
