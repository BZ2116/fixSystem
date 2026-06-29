import request from './request'

// 获取用户列表
export function getUserList(params) {
  return request.get('/users', { params })
}

// 获取用户详情
export function getUserDetail(id) {
  return request.get(`/users/${id}`)
}

// 创建用户
export function createUser(data) {
  return request.post('/users', data)
}

// 更新用户
export function updateUser(id, data) {
  return request.put(`/users/${id}`, data)
}

// 删除用户
export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}
