import request from './request'

export const getSalesList = (params) => request.get('/sales/orders', { params })
export const getSalesDetail = (id) => request.get(`/sales/orders/${id}`)
export const createSales = (data) => request.post('/sales/orders', data)
export const updateSales = (id, data) => request.put(`/sales/orders/${id}`, data)
export const deleteSales = (id) => request.delete(`/sales/orders/${id}`)
export const auditSales = (id) => request.post(`/sales/orders/${id}/audit`)

export const importSales = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/sales/orders/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const exportSales = () => request.get('/sales/orders/export', { responseType: 'blob' })

// ==================== 发票管理 ====================

/** 获取发票列表 */
export const getInvoiceList = (params) => request.get('/sales/invoices', { params })

/** 获取发票详情 */
export const getInvoiceDetail = (id) => request.get(`/sales/invoices/${id}`)

/** 创建或更新发票 */
export const saveInvoice = (data) => request.post('/sales/invoices', data)

/** 更新发票状态 */
export const updateInvoiceStatus = (id, data) => request.put(`/sales/invoices/${id}/status`, data)

/** 导出发票 */
export const exportInvoices = () => request.get('/sales/invoices/export', { responseType: 'blob' })

// ==================== 收据管理 ====================

/** 获取收据列表 */
export const getReceiptList = (params) => request.get('/sales/receipts', { params })

/** 获取收据详情 */
export const getReceiptDetail = (id) => request.get(`/sales/receipts/${id}`)

/** 开具收据 */
export const createReceipt = (data) => request.post('/sales/receipts', data)

/** 获取收据打印数据 */
export const getReceiptPrint = (id) => request.get(`/sales/receipts/${id}/print`)

/** 作废收据 */
export const voidReceipt = (id) => request.put(`/sales/receipts/${id}/void`)

/** 导出收据 */
export const exportReceipts = () => request.get('/sales/receipts/export', { responseType: 'blob' })
