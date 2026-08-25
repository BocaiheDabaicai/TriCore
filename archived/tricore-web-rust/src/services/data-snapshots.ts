import api from './http'

export const snapshotAPI = {
  list: () => api.get('/data-snapshots'),
  create: (data?: { notes?: string }) => api.post('/data-snapshots', data || {}),
  restore: (id: string) => api.post(`/data-snapshots/${id}/restore`, { confirm: true }),
  delete: (id: string) => api.delete(`/data-snapshots/${id}`),
}
