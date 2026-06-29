import request from './request'

export const getQuoteList = (params) => request.get('/quotes', { params })
export const getQuoteDetail = (id) => request.get(`/quotes/${id}`)
export const createQuote = (data) => request.post('/quotes', data)
export const updateQuote = (id, data) => request.put(`/quotes/${id}`, data)
export const deleteQuote = (id) => request.delete(`/quotes/${id}`)
export const confirmQuote = (id) => request.post(`/quotes/${id}/confirm`)
export const toWorkOrder = (id) => request.post(`/quotes/${id}/to-workorder`)
export const toReceive = (id) => request.post(`/quotes/${id}/to-receive`)
export const toSales = (id) => request.post(`/quotes/${id}/to-sales`)
