import request from './request'

// ==================== 对账管理 ====================
// 客户对账
export const getCustomerReconciliation = (params) => request.get('/reconciliation/customer', { params })
export const getCustomerReconciliationList = (params) => request.get('/reconciliation/customers', { params })

// 供应商对账
export const getSupplierReconciliation = (params) => request.get('/reconciliation/supplier', { params })
export const getSupplierReconciliationList = (params) => request.get('/reconciliation/suppliers', { params })

// 账户对账
export const getAccountReconciliation = (params) => request.get('/reconciliation/account', { params })
export const getAccountReconciliationList = (params) => request.get('/reconciliation/accounts', { params })
