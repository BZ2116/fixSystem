import { useUserStore } from '@/stores/user'

/**
 * v-permission 指令
 * 用法：
 *   v-permission="'workorder:add'"                        - 有权限则显示
 *   v-permission="['workorder:add', 'workorder:edit']"   - 有任一权限则显示
 */
const permissionDirective = {
  mounted(el, binding) {
    checkPermission(el, binding)
  },
  updated(el, binding) {
    checkPermission(el, binding)
  }
}

function checkPermission(el, binding) {
  const { value } = binding
  if (!value) return

  const userStore = useUserStore()
  const hasPermission = userStore.hasPermission(value)

  if (!hasPermission) {
    // 移除元素
    if (el.parentNode) {
      el.parentNode.removeChild(el)
    }
  }
}

export default permissionDirective
