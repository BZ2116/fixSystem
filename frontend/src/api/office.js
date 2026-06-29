import request from './request'

export const getOffices = () => request.get('/offices')
export const createOffice = (data) => request.post('/offices', data)
export const updateOffice = (id, data) => request.put(`/offices/${id}`, data)
export const deleteOffice = (id) => request.delete(`/offices/${id}`)
