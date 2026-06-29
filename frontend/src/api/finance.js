import request from './request'

export const getAccountList = (params) => request.get('/finance/accounts', { params })
export const createAccount = (data) => request.post('/finance/accounts', data)
export const updateAccount = (id, data) => request.put(`/finance/accounts/${id}`, data)
export const deleteAccount = (id) => request.delete(`/finance/accounts/${id}`)
export const getFinanceRecords = (params) => request.get('/finance/records', { params })

// ==================== 应收账款 ====================
export const getReceivableList = (params) => request.get('/finance/receivables', { params })
export const getReceivableDetail = (id) => request.get(`/finance/receivables/${id}`)
export const receiveReceivable = (id, data) => request.post(`/finance/receivables/${id}/receive`, data)
export const exportReceivables = () => request.get('/finance/receivables/export', { responseType: 'blob' })

// ==================== 应付账款 ====================
export const getPayableList = (params) => request.get('/finance/payables', { params })
export const getPayableDetail = (id) => request.get(`/finance/payables/${id}`)
export const payPayable = (id, data) => request.post(`/finance/payables/${id}/pay`, data)
export const exportPayables = () => request.get('/finance/payables/export', { responseType: 'blob' })

// ==================== 账户管理增强 ====================
export const transferAccount = (data) => request.post('/finance/accounts/transfer', data)
export const adjustAccount = (id, data) => request.post(`/finance/accounts/${id}/adjust`, data)
export const getFinanceRecordsEnhanced = (params) => request.get('/finance/records/enhanced', { params })

// ==================== 采购发票 ====================
export const getPurchaseInvoiceList = (params) => request.get('/purchase/invoices', { params })
export const getPurchaseInvoiceDetail = (id) => request.get(`/purchase/invoices/${id}`)
export const createPurchaseInvoice = (data) => request.post('/purchase/invoices', data)
export const updatePurchaseInvoice = (id, data) => request.put(`/purchase/invoices/${id}`, data)
export const deletePurchaseInvoice = (id) => request.delete(`/purchase/invoices/${id}`)
export const certifyPurchaseInvoice = (id) => request.post(`/purchase/invoices/${id}/certify`)
export const deductPurchaseInvoice = (id) => request.post(`/purchase/invoices/${id}/deduct`)

// ==================== 应收应付增强 ====================
export const batchReceiveReceivables = (data) => request.post('/finance/receivables/batch-receive', data)
export const batchPayPayables = (data) => request.post('/finance/payables/batch-pay', data)
export const getReceivablePrintData = (id) => request.get(`/finance/receivables/${id}/print`)
export const getPayablePrintData = (id) => request.get(`/finance/payables/${id}/print`)
export const getReceivableSummary = () => request.get('/finance/receivables/summary')
export const getPayableSummary = () => request.get('/finance/payables/summary')
