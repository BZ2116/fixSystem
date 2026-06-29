import request from './request'

// ==================== 资产类型 ====================
export const getAssetTypeList = () => request.get('/asset/types')

// ==================== 资产管理 ====================
export const getAssetList = (params) => request.get('/assets', { params })
export const getAssetDetail = (id) => request.get(`/assets/${id}`)
export const createAsset = (data) => request.post('/assets', data)
export const updateAsset = (id, data) => request.put(`/assets/${id}`, data)
export const deleteAsset = (id) => request.delete(`/assets/${id}`)
export const scrapAsset = (id) => request.post(`/assets/${id}/scrap`)
export const importAssets = (data) => request.post('/assets/import', data)
export const exportAssets = (params) => request.get('/assets/export', { params, responseType: 'blob' })
export const getAssetsByCustomer = (customerId) => request.get('/assets/by-customer', { params: { customer_id: customerId } })

// ==================== 销售模块资产关联 ====================
export const createSalesOrderAssets = (orderId, data) => request.post(`/sales/orders/${orderId}/assets`, data)
export const getSalesOrderAssets = (orderId) => request.get(`/sales/orders/${orderId}/assets`)
export const unbindReturnAssets = (returnId) => request.post(`/sales/returns/${returnId}/unbind-assets`)
