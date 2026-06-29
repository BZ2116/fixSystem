import request from './request'

export const getCustomerList = (params) => {
  return request.get('/customers', { params })
}

export const createCustomer = (data) => {
  return request.post('/customers', data)
}

export const updateCustomer = (id, data) => {
  return request.put(`/customers/${id}`, data)
}

export const deleteCustomer = (id) => {
  return request.delete(`/customers/${id}`)
}

export const batchDeleteCustomers = (ids) => {
  return request.post('/customers/batch-delete', { ids })
}

export const getCustomerDetail = (id) => {
  return request.get(`/customers/${id}`)
}

export const importCustomers = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/customers/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const exportCustomers = () => request.get('/customers/export', { responseType: 'blob' })
