import request from './request'

// ==================== 工资发放 ====================
export const getSalaryList = (params) => request.get('/salary', { params })
export const getSalaryDetail = (id) => request.get(`/salary/${id}`)
export const createSalary = (data) => request.post('/salary', data)
export const updateSalary = (id, data) => request.put(`/salary/${id}`, data)
export const deleteSalary = (id) => request.delete(`/salary/${id}`)
export const paySalary = (id, data) => request.post(`/salary/${id}/pay`, data)
export const getSalaryStatistics = (params) => request.get('/salary/statistics', { params })
