/**
 * 批量操作通用工具函数
 * 提供批量操作的前置校验、数据处理、错误处理等通用逻辑
 */
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

/**
 * 检查选中项是否为空
 * @param {Array} selection - 选中的数据
 * @returns {boolean}
 */
export function checkSelectionEmpty(selection) {
  if (!selection || selection.length === 0) {
    ElMessage.warning('请先勾选要操作的数据')
    return true
  }
  return false
}

/**
 * 检查是否有业务记录（用于删除/编辑拦截）
 * @param {Array} selection - 选中的数据
 * @param {string} checkField - 检查字段名（如 has_business_record）
 * @param {string} actionName - 操作名称（如删除、修改）
 * @returns {boolean} - true表示有业务记录，需要拦截
 */
export function checkBusinessRecord(selection, checkField = 'has_business_record', actionName = '操作') {
  const hasRecord = selection.filter(item => item[checkField] === true || item[checkField] === 1)
  if (hasRecord.length > 0) {
    const names = hasRecord.slice(0, 3).map(item => item.product_name || item.name || '未命名').join('、')
    const more = hasRecord.length > 3 ? `等${hasRecord.length}条数据` : ''
    ElMessage.error(`该商品已存在业务记录，不允许批量${actionName}：${names}${more}`)
    return true
  }
  return false
}

/**
 * 批量操作确认对话框
 * @param {string} title - 标题
 * @param {string} message - 提示内容
 * @param {string} type - 类型（warning/error/info）
 * @returns {Promise<boolean>}
 */
export async function batchConfirm(title, message, type = 'warning') {
  try {
    await ElMessageBox.confirm(message, title, { type })
    return true
  } catch {
    return false
  }
}

/**
 * 执行批量API请求
 * @param {string} url - API地址
 * @param {Object} data - 请求数据（包含ids和更新字段）
 * @param {string} successMsg - 成功提示
 * @returns {Promise<Object>}
 */
export async function executeBatchApi(url, data, successMsg = '操作成功') {
  try {
    const res = await request.post(url, data)
    if (res.code === 200) {
      ElMessage.success(successMsg)
      return { success: true, data: res.data }
    } else {
      ElMessage.error(res.message || '操作失败')
      return { success: false, message: res.message }
    }
  } catch (error) {
    const errorMsg = error.response?.data?.message || error.message || '操作失败'
    ElMessage.error(errorMsg)
    return { success: false, message: errorMsg }
  }
}

/**
 * 批量操作完整流程封装
 * @param {Object} options - 配置选项
 * @returns {Promise<boolean>}
 */
export async function batchOperation(options) {
  const {
    selection,              // 选中的数据
    checkEmpty = true,      // 是否检查空选择
    checkBusiness = false,  // 是否检查业务记录
    businessField = 'has_business_record',
    confirmTitle = '确认操作',
    confirmMessage = '确定执行批量操作吗？',
    confirmType = 'warning',
    apiUrl,                 // API地址
    apiData,                // API数据
    successMessage = '操作成功'
  } = options

  // 1. 检查是否选择了数据
  if (checkEmpty && checkSelectionEmpty(selection)) {
    return false
  }

  // 2. 检查业务记录
  if (checkBusiness && checkBusinessRecord(selection, businessField, confirmTitle.replace('确认', ''))) {
    return false
  }

  // 3. 确认对话框
  const confirmed = await batchConfirm(confirmTitle, confirmMessage, confirmType)
  if (!confirmed) return false

  // 4. 执行API请求
  const result = await executeBatchApi(apiUrl, apiData, successMessage)
  return result.success
}

/**
 * 构建批量操作的数据
 * @param {Array} selection - 选中的数据
 * @param {Object} updateData - 要更新的字段
 * @returns {Object}
 */
export function buildBatchData(selection, updateData) {
  return {
    ids: selection.map(item => item.id),
    ...updateData
  }
}

/**
 * 批量修改分类
 * @param {Array} selection - 选中的商品
 * @param {number} categoryId - 新分类ID
 * @param {string} categoryName - 新分类名称
 */
export async function batchUpdateCategory(selection, categoryId, categoryName) {
  return batchOperation({
    selection,
    confirmTitle: '批量修改分类',
    confirmMessage: `确定将选中的${selection.length}个商品分类修改为"${categoryName}"吗？`,
    apiUrl: '/products/batch-update-category',
    apiData: buildBatchData(selection, { category_id: categoryId, category_name: categoryName }),
    successMessage: '批量修改分类成功'
  })
}

/**
 * 批量修改价格
 * @param {Array} selection - 选中的商品
 * @param {Object} priceData - 价格数据
 */
export async function batchUpdatePrice(selection, priceData) {
  return batchOperation({
    selection,
    confirmTitle: '批量修改价格',
    confirmMessage: `确定批量修改选中的${selection.length}个商品价格吗？留空的字段将保持原值不变。`,
    apiUrl: '/products/batch-update-price',
    apiData: buildBatchData(selection, priceData),
    successMessage: '批量修改价格成功'
  })
}

/**
 * 批量设置库存预警
 * @param {Array} selection - 选中的商品
 * @param {number} minStock - 最低库存
 * @param {number} maxStock - 最高库存
 */
export async function batchUpdateStockWarning(selection, minStock, maxStock) {
  return batchOperation({
    selection,
    confirmTitle: '批量设置库存预警',
    confirmMessage: `确定为选中的${selection.length}个商品设置库存预警吗？`,
    apiUrl: '/products/batch-update-stock-warning',
    apiData: buildBatchData(selection, { min_stock: minStock, max_stock: maxStock }),
    successMessage: '批量设置库存预警成功'
  })
}

/**
 * 批量修改排序
 * @param {Array} selection - 选中的商品
 * @param {number} sortOrder - 排序值
 */
export async function batchUpdateSort(selection, sortOrder) {
  return batchOperation({
    selection,
    confirmTitle: '批量修改排序',
    confirmMessage: `确定将选中的${selection.length}个商品排序值修改为${sortOrder}吗？`,
    apiUrl: '/products/batch-update-sort',
    apiData: buildBatchData(selection, { sort_order: sortOrder }),
    successMessage: '批量修改排序成功'
  })
}

/**
 * 批量禁用
 * @param {Array} selection - 选中的商品
 */
export async function batchDisable(selection) {
  return batchOperation({
    selection,
    confirmTitle: '批量禁用',
    confirmMessage: `确定禁用选中的${selection.length}个商品吗？禁用后商品将不可使用。`,
    confirmType: 'warning',
    apiUrl: '/products/batch-disable',
    apiData: buildBatchData(selection, { status: 0 }),
    successMessage: '批量禁用成功'
  })
}

/**
 * 批量启用
 * @param {Array} selection - 选中的商品
 */
export async function batchEnable(selection) {
  return batchOperation({
    selection,
    confirmTitle: '批量启用',
    confirmMessage: `确定启用选中的${selection.length}个商品吗？`,
    confirmType: 'info',
    apiUrl: '/products/batch-enable',
    apiData: buildBatchData(selection, { status: 1 }),
    successMessage: '批量启用成功'
  })
}

/**
 * 批量删除
 * @param {Array} selection - 选中的商品
 */
export async function batchDelete(selection) {
  return batchOperation({
    selection,
    checkBusiness: true,
    businessField: 'has_business_record',
    confirmTitle: '批量删除',
    confirmMessage: `确定删除选中的${selection.length}个商品吗？此操作不可恢复！`,
    confirmType: 'error',
    apiUrl: '/products/batch-delete',
    apiData: buildBatchData(selection, {}),
    successMessage: '批量删除成功'
  })
}
