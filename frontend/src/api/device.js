import request from './request'

export const getDeviceList = (params) => request.get('/devices', { params })
export const getDeviceDetail = (id) => request.get(`/devices/${id}`)
export const createDevice = (data) => request.post('/devices', data)
export const updateDevice = (id, data) => request.put(`/devices/${id}`, data)
export const deleteDevice = (id) => request.delete(`/devices/${id}`)
export const getDeviceRepairHistory = (id) => request.get(`/devices/${id}/repair-history`)
export const getOwnDeviceList = (params) => request.get('/devices/own', { params })
export const createOwnDevice = (data) => request.post('/devices/own', data)
export const updateOwnDevice = (id, data) => request.put(`/devices/own/${id}`, data)
export const deleteOwnDevice = (id) => request.delete(`/devices/own/${id}`)
