import request from './request'

export const getSupplierList = (params) => request.get('/suppliers', { params })
export const getSupplierDetail = (id) => request.get(`/suppliers/${id}`)
export const createSupplier = (data) => request.post('/suppliers', data)
export const updateSupplier = (id, data) => request.put(`/suppliers/${id}`, data)
export const deleteSupplier = (id) => request.delete(`/suppliers/${id}`)
export const batchDeleteSuppliers = (ids) => request.post('/suppliers/batch-delete', { ids })

export const importSuppliers = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/suppliers/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const exportSuppliers = () => request.get('/suppliers/export', { responseType: 'blob' })
