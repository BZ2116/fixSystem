import request from './request'

export const getPurchaseList = (params) => request.get('/purchase/orders', { params })
export const getPurchaseDetail = (id) => request.get(`/purchase/orders/${id}`)
export const createPurchase = (data) => request.post('/purchase/orders', data)
export const updatePurchase = (id, data) => request.put(`/purchase/orders/${id}`, data)
export const deletePurchase = (id) => request.delete(`/purchase/orders/${id}`)
export const auditPurchase = (id) => request.post(`/purchase/orders/${id}/audit`)

export const importPurchases = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/purchase/orders/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const exportPurchases = () => request.get('/purchase/orders/export', { responseType: 'blob' })
