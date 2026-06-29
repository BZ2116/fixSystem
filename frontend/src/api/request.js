import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { translateError } from '@/utils/errorMessages'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    // 如果是blob响应（文件下载），直接返回response
    if (response.config.responseType === 'blob') {
      return response
    }
    
    const res = response.data
    
    // 如果响应code不是200，显示错误信息
    if (res.code !== 200) {
      // 统一转换为中文错误消息
      const cnMessage = translateError(res.message, res.code)
      ElMessage.error(cnMessage)
      
      // 401未授权，清除token并跳转登录页
      if (res.code === 401) {
        const userStore = useUserStore()
        userStore.logout()
        window.location.href = '/login'
      }
      
      return Promise.reject(new Error(cnMessage))
    }
    
    return res
  },
  (error) => {
    const status = error.response?.status
    const originalMessage = error.response?.data?.message || error.message
    // 统一转换为中文错误消息
    const cnMessage = translateError(originalMessage, status)
    ElMessage.error(cnMessage)
    
    if (status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)

export default request
