import api from './http'

export const regulationsAPI = {
  // Categories
  listCategories: (params?: { name?: string }) =>
    api.get('/regulations/categories', { params }),
  createCategory: (data: { name: string }) =>
    api.post('/regulations/categories', data),
  deleteCategory: (id: string) =>
    api.delete(`/regulations/categories/${id}`),
  // Files
  listFiles: (params?: { title?: string; category_id?: string; page?: number; per_page?: number }) =>
    api.get('/regulations/files', { params }),
  getFile: (id: string) =>
    api.get(`/regulations/files/${id}`),
  uploadFile: (formData: FormData) =>
    api.post('/regulations/files', formData, {
      headers: { 'Content-Type': undefined as any },
    }),
  updateFile: (id: string, data: Record<string, unknown>) =>
    api.put(`/regulations/files/${id}`, data),
  deleteFile: (id: string) =>
    api.delete(`/regulations/files/${id}`),
  downloadUrl: (id: string) => `/api/regulations/files/${id}/download`,
}
