import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTabsStore = defineStore('tabs', () => {
  // State
  const tabs = ref([
    { name: '首页', path: '/dashboard', closable: false }
  ])
  const activeTab = ref('/dashboard')

  // Getters
  const tabList = computed(() => tabs.value)
  const currentTab = computed(() => activeTab.value)

  // Actions
  const addTab = (route) => {
    const { path, meta } = route
    const title = meta?.title || '未命名'
    
    // 如果标签已存在，不重复添加
    const exists = tabs.value.some(tab => tab.path === path)
    if (!exists) {
      tabs.value.push({
        name: title,
        path: path,
        closable: path !== '/dashboard'
      })
    }
    activeTab.value = path
  }

  const removeTab = (targetPath) => {
    const index = tabs.value.findIndex(tab => tab.path === targetPath)
    if (index === -1) return

    tabs.value.splice(index, 1)
    
    // 如果关闭的是当前激活的标签，切换到相邻标签
    if (activeTab.value === targetPath) {
      const nextTab = tabs.value[index] || tabs.value[index - 1]
      if (nextTab) {
        activeTab.value = nextTab.path
        return nextTab.path
      }
    }
    return null
  }

  const setActiveTab = (path) => {
    activeTab.value = path
  }

  const closeOtherTabs = (path) => {
    tabs.value = tabs.value.filter(tab => tab.path === path || tab.path === '/dashboard')
    activeTab.value = path
  }

  const closeAllTabs = () => {
    tabs.value = [{ name: '首页', path: '/dashboard', closable: false }]
    activeTab.value = '/dashboard'
    return '/dashboard'
  }

  return {
    tabs,
    activeTab,
    tabList,
    currentTab,
    addTab,
    removeTab,
    setActiveTab,
    closeOtherTabs,
    closeAllTabs
  }
})
