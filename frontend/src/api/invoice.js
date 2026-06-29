import request from './request'

export const getInvoiceList = (params) => request.get('/invoices', { params })
export const getInvoiceDetail = (id) => request.get(`/invoices/${id}`)
export const createInvoice = (data) => request.post('/invoices', data)
export const updateInvoice = (id, data) => request.put(`/invoices/${id}`, data)
export const deleteInvoice = (id) => request.delete(`/invoices/${id}`)
export const cancelInvoice = (id) => request.post(`/invoices/${id}/cancel`)
export const redFlushInvoice = (id) => request.post(`/invoices/${id}/red-flush`)
