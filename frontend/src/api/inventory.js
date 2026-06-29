import request from './request'

export const getStockList = (params) => request.get('/inventory/stock', { params })
export const getInList = (params) => request.get('/inventory/in', { params })
export const getInDetail = (id) => request.get(`/inventory/in/${id}`)
export const createIn = (data) => request.post('/inventory/in', data)
export const auditIn = (id) => request.post(`/inventory/in/${id}/audit`)
export const getOutList = (params) => request.get('/inventory/out', { params })
export const createOut = (data) => request.post('/inventory/out', data)
export const auditOut = (id) => request.post(`/inventory/out/${id}/audit`)
export const getCheckList = (params) => request.get('/inventory/check', { params })
export const getCheckDetail = (id) => request.get(`/inventory/check/${id}`)
export const updateCheck = (id, data) => request.put(`/inventory/check/${id}`, data)
export const auditCheck = (id) => request.post(`/inventory/check/${id}/audit`)
export const getCheckItems = (id) => request.get(`/inventory/check/${id}/items`)

// ==================== 仓库管理 ====================
export const getWarehouseList = (params) => request.get('/warehouses', { params })
export const createWarehouse = (data) => request.post('/warehouses', data)
export const updateWarehouse = (id, data) => request.put(`/warehouses/${id}`, data)
export const deleteWarehouse = (id) => request.delete(`/warehouses/${id}`)
export const updateWarehouseStatus = (id, data) => request.put(`/warehouses/${id}/status`, data)

// ==================== 库存变动明细 ====================
export const getInventoryLogs = (params) => request.get('/inventory/logs', { params })
export const exportInventoryLogs = () => request.get('/inventory/logs/export', { responseType: 'blob' })

// ==================== 调拨管理 ====================
export const getTransferList = (params) => request.get('/transfer/orders', { params })
export const getTransferDetail = (id) => request.get(`/transfer/orders/${id}`)
export const createTransfer = (data) => request.post('/transfer/orders', data)
export const updateTransfer = (id, data) => request.put(`/transfer/orders/${id}`, data)
export const auditTransfer = (id) => request.post(`/transfer/orders/${id}/audit`)
export const deleteTransfer = (id) => request.delete(`/transfer/orders/${id}`)
export const exportTransfer = () => request.get('/transfer/orders/export', { responseType: 'blob' })

// ==================== 成本调价 ====================
export const getCostAdjustList = (params) => request.get('/cost-adjusts', { params })
export const getCostAdjustDetail = (id) => request.get(`/cost-adjusts/${id}`)
export const createCostAdjust = (data) => request.post('/cost-adjusts', data)
export const auditCostAdjust = (id) => request.post(`/cost-adjusts/${id}/audit`)
export const deleteCostAdjust = (id) => request.delete(`/cost-adjusts/${id}`)
export const exportCostAdjust = () => request.get('/cost-adjusts/export', { responseType: 'blob' })

// ==================== 库存查询增强 ====================
export const exportInventoryStock = (params) => request.get('/inventory/stock/export', { params, responseType: 'blob' })
