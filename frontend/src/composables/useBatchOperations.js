import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 通用批量操作组合式函数
 * @param {Object} options
 * @param {Function} options.deleteApi - 批量删除API函数
 * @param {Function} options.refreshFn - 刷新数据函数
 * @param {String} options.moduleName - 模块名称（用于提示）
 * @param {String} options.idField - ID字段名（默认'id'）
 * @param {Function} options.beforeDelete - 删除前校验函数（可选）
 */
export function useBatchOperations(options) {
  const {
    deleteApi,
    refreshFn,
    moduleName = '数据',
    idField = 'id',
    beforeDelete = null
  } = options

  const selectedItems = ref([])

  const handleSelectionChange = (selection) => {
    selectedItems.value = selection
  }

  const handleBatchDelete = async () => {
    if (selectedItems.value.length === 0) {
      ElMessage.warning(`请先选择要删除的${moduleName}`)
      return
    }

    // 删除前校验
    if (beforeDelete) {
      const checkResult = beforeDelete(selectedItems.value)
      if (checkResult !== true) {
        ElMessage.warning(checkResult)
        return
      }
    }

    try {
      await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedItems.value.length} 个${moduleName}吗？`,
        '批量删除',
        { type: 'warning' }
      )

      const ids = selectedItems.value.map(item => item[idField])
      const res = await deleteApi(ids)

      if (res.code === 200) {
        ElMessage.success('批量删除成功')
        selectedItems.value = []
        if (refreshFn) refreshFn()
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('批量删除失败:', error)
        ElMessage.error(error.message || '批量删除失败')
      }
    }
  }

  return {
    selectedItems,
    handleSelectionChange,
    handleBatchDelete
  }
}
