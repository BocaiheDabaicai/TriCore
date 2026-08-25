import api from './http'

export const authAPI = {
  login: (employee_no: string, password: string) =>
    api.post('/auth/login', { employee_no, password }),
  me: () => api.get('/auth/me'),
}
