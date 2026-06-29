/**
 * 全局校验工具 - 重名校验、必填校验、业务数据锁定
 */
import request from './request'
import { ElMessage } from 'element-plus'

// ============================================
// 重名校验
// ============================================

/**
 * 检查名称/编码是否重复
 * @param {string} model - 模型类名
 * @param {string} name - 名称值
 * @param {string} code - 编码值（可选）
 * @param {number} excludeId - 排除的ID（编辑时）
 * @returns {Promise<{duplicate: boolean, message: string}>}
 */
export async function checkDuplicate(model, name, code = null, excludeId = null) {
  try {
    const res = await request.post('/api/validators/check-duplicate', {
      model,
      name,
      code,
      exclude_id: excludeId
    })
    return { duplicate: false, message: '' }
  } catch (error) {
    if (error.response?.status === 409) {
      return { duplicate: true, message: error.response.data.message }
    }
    return { duplicate: false, message: '' }
  }
}

/**
 * 保存前重名校验（弹窗提示）
 * @param {string} model - 模型类名
 * @param {Object} data - 表单数据
 * @param {number} excludeId - 排除的ID
 * @returns {Promise<boolean>} - true表示校验通过
 */
export async function validateDuplicateBeforeSave(model, data, excludeId = null) {
  const nameField = getNameField(model)
  const codeField = getCodeField(model)
  
  const nameValue = nameField ? data[nameField] : null
  const codeValue = codeField ? data[codeField] : null
  
  if (!nameValue && !codeValue) return true
  
  const result = await checkDuplicate(model, nameValue, codeValue, excludeId)
  if (result.duplicate) {
    ElMessage.error(result.message)
    return false
  }
  return true
}

// ============================================
// 必填校验
// ============================================

/**
 * 必填字段配置（与后端保持一致）
 */
const REQUIRED_FIELDS_CONFIG = {
  'Office': ['name'],
  'SysRole': ['role_name', 'role_code'],
  'SysPermission': ['name', 'code'],
  'BaseCustomer': ['customer_name'],
  'BaseSupplier': ['supplier_name'],
  'ProductInfo': ['product_name', 'product_code'],
  'ProductCategory': ['category_name'],
  'ProductUnit': ['unit_name'],
  'WoType': ['type_name', 'type_code'],
  'WoSubType': ['sub_type_name', 'sub_type_code'],
  'Project': ['project_name'],
  'Warehouse': ['warehouse_name'],
  'Shelf': ['shelf_name'],
  'AssetType': ['type_name', 'type_code'],
  'Asset': ['asset_name'],
  'FinanceAccount': ['account_name', 'account_type'],
  'Expense': ['expense_name', 'expense_type'],
}

/**
 * 字段中文名映射
 */
const FIELD_NAME_MAP = {
  'name': '名称',
  'code': '编码',
  'role_name': '角色名称',
  'role_code': '角色编码',
  'customer_name': '客户名称',
  'customer_code': '客户编码',
  'supplier_name': '供应商名称',
  'supplier_code': '供应商编码',
  'product_name': '商品名称',
  'product_code': '商品编码',
  'category_name': '分类名称',
  'unit_name': '单位名称',
  'unit_code': '单位编码',
  'type_name': '类型名称',
  'type_code': '类型编码',
  'sub_type_name': '子类型名称',
  'sub_type_code': '子类型编码',
  'project_name': '项目名称',
  'project_code': '项目编码',
  'warehouse_name': '仓库名称',
  'warehouse_code': '仓库编码',
  'shelf_name': '货架名称',
  'shelf_code': '货架编码',
  'asset_name': '资产名称',
  'asset_no': '资产编号',
  'account_name': '账户名称',
  'account_type': '账户类型',
  'expense_name': '费用名称',
  'expense_type': '费用类型',
}

/**
 * 检查必填字段
 * @param {string} model - 模型类名
 * @param {Object} data - 表单数据
 * @returns {boolean} - true表示校验通过
 */
export function validateRequiredFields(model, data) {
  const requiredFields = REQUIRED_FIELDS_CONFIG[model] || []
  const missingFields = []
  
  for (const field of requiredFields) {
    const value = data[field]
    if (!value || String(value).trim() === '') {
      const fieldName = FIELD_NAME_MAP[field] || field
      missingFields.push(fieldName)
    }
  }
  
  if (missingFields.length > 0) {
    ElMessage.error(`以下字段为必填项，请补全内容：${missingFields.join('、')}`)
    return false
  }
  
  return true
}

// ============================================
// 业务数据锁定检查
// ============================================

/**
 * 业务单据类模型列表
 */
const BUSINESS_DOCUMENT_MODELS = [
  'WorkOrder', 'WorkOrderPart', 'WorkOrderQuoteItem',
  'DeviceReceiveOrder', 'ReceiveOrder', 'DispatchRecord',
  'InventoryIn', 'InventoryOut', 'InventoryCheck',
  'TransferOrder', 'AssembleOrder', 'CostAdjust',
  'PreOrder', 'ReturnOrder', 'QuoteOrder',
  'PurchaseOrder', 'SalesOrder', 'FinanceRecord',
  'FinanceReceivable', 'FinancePayable', 'FinanceInvoice',
  'PurchaseInvoice', 'SalesInvoice', 'SalesReceipt', 'Salary'
]

/**
 * 检查业务数据是否已锁定
 * @param {string} model - 模型类名
 * @param {number} recordId - 记录ID
 * @returns {Promise<{editable: boolean, message: string}>}
 */
export async function checkEditPermission(model, recordId) {
  try {
    const res = await request.get(`/api/validators/check-edit-permission/${model}/${recordId}`)
    return { editable: true, message: '' }
  } catch (error) {
    if (error.response?.status === 403) {
      return { editable: false, message: error.response.data.message }
    }
    return { editable: true, message: '' }
  }
}

/**
 * 检查是否为业务单据（需要锁定检查）
 * @param {string} model - 模型类名
 * @returns {boolean}
 */
export function isBusinessDocument(model) {
  return BUSINESS_DOCUMENT_MODELS.includes(model)
}

// ============================================
// 辅助函数
// ============================================

/**
 * 获取模型的名称字段
 */
function getNameField(model) {
  const config = {
    'Office': 'name',
    'SysRole': 'role_name',
    'SysPermission': 'name',
    'BaseCustomer': 'customer_name',
    'BaseSupplier': 'supplier_name',
    'ProductInfo': 'product_name',
    'ProductCategory': 'category_name',
    'ProductUnit': 'unit_name',
    'WoType': 'type_name',
    'WoSubType': 'sub_type_name',
    'Project': 'project_name',
    'Warehouse': 'warehouse_name',
    'Shelf': 'shelf_name',
    'AssetType': 'type_name',
    'Asset': 'asset_name',
    'FinanceAccount': 'account_name',
    'Expense': 'expense_name',
  }
  return config[model]
}

/**
 * 获取模型的编码字段
 */
function getCodeField(model) {
  const config = {
    'Office': 'code',
    'SysRole': 'role_code',
    'SysPermission': 'code',
    'BaseCustomer': 'customer_code',
    'BaseSupplier': 'supplier_code',
    'ProductInfo': 'product_code',
    'ProductUnit': 'unit_code',
    'WoType': 'type_code',
    'WoSubType': 'sub_type_code',
    'Project': 'project_code',
    'Warehouse': 'warehouse_code',
    'Shelf': 'shelf_code',
    'AssetType': 'type_code',
    'Asset': 'asset_no',
  }
  return config[model]
}

// ============================================
// 统一保存校验（组合校验）
// ============================================

/**
 * 保存前统一校验（必填 + 重名）
 * @param {string} model - 模型类名
 * @param {Object} data - 表单数据
 * @param {number} excludeId - 编辑时排除的ID
 * @returns {Promise<boolean>} - true表示校验通过
 */
export async function validateBeforeSave(model, data, excludeId = null) {
  // 1. 必填校验
  if (!validateRequiredFields(model, data)) {
    return false
  }
  
  // 2. 重名校验
  if (!await validateDuplicateBeforeSave(model, data, excludeId)) {
    return false
  }
  
  return true
}
