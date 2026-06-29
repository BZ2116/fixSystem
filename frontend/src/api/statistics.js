import request from './request'

// ==================== 业绩统计 ====================
export const getRevenueStatistics = (params) => request.get('/statistics/revenue', { params })
export const getEmployeeStatistics = (params) => request.get('/statistics/employee', { params })
export const getCustomerStatistics = (params) => request.get('/statistics/customer', { params })
export const getProductStatistics = (params) => request.get('/statistics/product', { params })
export const getDashboardData = () => request.get('/statistics/dashboard')
