import request from './request'

// ==================== 费用管理 ====================
export const getExpenseList = (params) => request.get('/expense', { params })
export const getExpenseDetail = (id) => request.get(`/expense/${id}`)
export const createExpense = (data) => request.post('/expense', data)
export const updateExpense = (id, data) => request.put(`/expense/${id}`, data)
export const deleteExpense = (id) => request.delete(`/expense/${id}`)
export const confirmExpense = (id, data) => request.post(`/expense/${id}/confirm`, data)
export const getExpenseStatistics = (params) => request.get('/expense/statistics', { params })
