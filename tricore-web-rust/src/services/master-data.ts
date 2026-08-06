import api from './http'

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
