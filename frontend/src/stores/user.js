import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const permissions = ref([])
  const menus = ref([])

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const realName = computed(() => userInfo.value?.real_name || '')
  const roleCode = computed(() => userInfo.value?.role_code || '')
  const isAdmin = computed(() => {
    return roleCode.value === 'admin' || permissions.value.includes('*')
  })

  // Actions
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    userInfo.value = null
    permissions.value = []
    menus.value = []
    localStorage.removeItem('token')
  }

  const login = async (credentials) => {
    const res = await loginApi(credentials)
    if (res.code === 200) {
      setToken(res.data.token)
      // 注意：后端 auth.py 登录响应字段是 userInfo（不是 user）
      userInfo.value = res.data.userInfo
      // 保存登录返回的权限
      if (res.data.userInfo?.permissions) {
        permissions.value = res.data.userInfo.permissions
      }
      return res
    }
    throw new Error(res.message)
  }

  const fetchUserInfo = async () => {
    try {
      const res = await getUserInfo()
      if (res.code === 200) {
        userInfo.value = res.data
        // 获取权限和菜单
        if (res.data.permissions) {
          permissions.value = res.data.permissions
        }
        if (res.data.menus) {
          menus.value = res.data.menus
        }
        return res.data
      }
    } catch (error) {
      clearToken()
      throw error
    }
  }

  const logout = () => {
    clearToken()
  }

  /**
   * 检查是否拥有某个权限
   * @param {string|Array} code - 权限code，字符串或数组（数组表示任一匹配即可）
   * @returns {boolean}
   */
  const hasPermission = (code) => {
    // 超级管理员拥有所有权限
    if (isAdmin.value) return true
    if (!code) return true

    if (Array.isArray(code)) {
      return code.some(c => permissions.value.includes(c))
    }
    return permissions.value.includes(code)
  }

  return {
    token,
    userInfo,
    permissions,
    menus,
    isLoggedIn,
    username,
    realName,
    roleCode,
    isAdmin,
    login,
    fetchUserInfo,
    logout,
    setToken,
    clearToken,
    hasPermission
  }
})
