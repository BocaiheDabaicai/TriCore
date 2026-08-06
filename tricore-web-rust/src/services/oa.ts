import api from './http'

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
  // Templates
  listTemplates: () => api.get('/oa/templates'),
  createTemplate: (data: Record<string, unknown>) => api.post('/oa/templates', data),
  updateTemplate: (id: string, data: Record<string, unknown>) => api.put(`/oa/templates/${id}`, data),
  deleteTemplate: (id: string) => api.delete(`/oa/templates/${id}`),
}
