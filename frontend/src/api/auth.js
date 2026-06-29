import request from './request'

export const login = (data) => {
  return request.post('/auth/login', data)
}

export const register = (data) => {
  return request.post('/auth/register', data)
}

export const getUserInfo = () => {
  return request.get('/user/info')
}

export const logout = () => {
  return request.post('/auth/logout')
}
