import request from './request'

/**
 * 通用批量删除API
 * @param {string} module - 模块名称（如：workorders, sales, purchases, quotes）
 * @param {number[]} ids - 要删除的ID数组
 */
export const batchDelete = (module, ids) => {
  return request.post(`/${module}/batch-delete`, { ids })
}

/**
 * 通用批量更新API
 * @param {string} module - 模块名称
 * @param {number[]} ids - 要更新的ID数组
 * @param {Object} data - 更新数据
 */
export const batchUpdate = (module, ids, data) => {
  return request.post(`/${module}/batch-update`, { ids, ...data })
}
