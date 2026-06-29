/**
 * 全局中文错误消息映射表
 * 将后端返回的英文/技术错误转换为中文业务提示
 */

// 数据库相关错误
const DB_ERROR_MAP = {
  'Duplicate entry': '数据重复',
  'IntegrityError': '数据完整性错误',
  'ForeignKeyViolation': '关联数据不存在',
  'UniqueViolation': '数据已存在，不可重复',
  'NotNullViolation': '必填项不能为空',
  'DataError': '数据格式错误',
}

// 常见英文错误关键词映射
const ENGLISH_ERROR_MAP = {
  // 通用技术错误
  'Internal Server Error': '服务器内部错误，请联系管理员',
  'Bad Request': '请求参数错误',
  'Not Found': '请求的资源不存在',
  'Forbidden': '没有操作权限',
  'Unauthorized': '登录已过期，请重新登录',
  'Timeout': '请求超时，请稍后重试',
  'Network Error': '网络连接失败，请检查网络',
  'Connection refused': '服务器连接失败',
  
  // 数据库错误
  'duplicate entry': '数据已存在，不可重复',
  'unique constraint': '数据已存在，不可重复',
  'foreign key constraint': '关联数据不存在，请先创建关联数据',
  'cannot be null': '必填项不能为空',
  'Data too long': '输入内容过长',
  'Incorrect integer value': '数字格式不正确',
  'Incorrect decimal value': '金额格式不正确',
  
  // 业务错误关键词
  'stock not enough': '库存不足',
  'insufficient stock': '库存不足',
  'out of stock': '库存不足',
  'quantity exceeds': '数量超出范围',
  'already exists': '数据已存在',
  'not found': '数据不存在',
  'does not exist': '数据不存在',
  'is required': '必填项不能为空',
  'cannot be empty': '不能为空',
  'invalid format': '格式不正确',
  'parse error': '解析失败',
  'serialize': '序列号',
  'barcode': '条形码',
  'product_code': '商品编码',
  'warehouse_code': '仓库编码',
}

// HTTP状态码映射
const HTTP_STATUS_MAP = {
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '没有操作权限',
  404: '请求的资源不存在',
  405: '请求方式不正确',
  408: '请求超时，请稍后重试',
  409: '数据冲突，请刷新后重试',
  413: '上传文件过大',
  422: '数据校验失败',
  429: '请求过于频繁，请稍后重试',
  500: '服务器内部错误，请联系管理员',
  502: '服务器暂时不可用',
  503: '服务维护中，请稍后重试',
  504: '服务器响应超时',
}

// 业务模块错误映射
const BUSINESS_ERROR_MAP = {
  // 工单相关
  '工单': {
    'wo_type': '工单类型',
    'work_order': '工单',
    'dispatch': '派工',
    'check': '检测',
    'repair': '维修',
  },
  // 库存相关
  '库存': {
    'stock': '库存',
    'inventory': '库存',
    'warehouse': '仓库',
    'shelf': '货架',
    'in_stock': '入库',
    'out_stock': '出库',
    'transfer': '调拨',
    'check_stock': '盘点',
  },
  // 财务相关
  '财务': {
    'receivable': '应收款',
    'payable': '应付款',
    'invoice': '发票',
    'receipt': '收款',
    'payment': '付款',
    'salary': '工资',
    'expense': '费用',
  },
}

/**
 * 智能转换错误消息为中文
 * @param {string} message - 原始错误消息
 * @param {number} status - HTTP状态码
 * @returns {string} - 中文错误消息
 */
export function translateError(message, status = null) {
  if (!message) {
    return status ? (HTTP_STATUS_MAP[status] || '操作失败') : '操作失败'
  }
  
  // 如果已经是纯中文（不含英文字母），直接返回
  if (/^[\u4e00-\u9fa5\d\s，。！？、：；""''（）【】]+$/.test(message)) {
    return message
  }
  
  const lowerMessage = message.toLowerCase()
  
  // 1. 检查HTTP状态码 - 优先使用状态码对应的中文提示
  if (status && HTTP_STATUS_MAP[status]) {
    // 如果是标准的HTTP错误消息（如 Request failed with status code xxx），直接返回中文
    if (/request failed with status code/i.test(message) || 
        /network error/i.test(message) ||
        /timeout/i.test(message)) {
      return HTTP_STATUS_MAP[status]
    }
    // 如果消息包含 Error/error 且不是纯英文技术错误，保留原消息
    if (!message.includes('Error') && !message.includes('error')) {
      return message
    }
    return HTTP_STATUS_MAP[status]
  }
  
  // 2. 检查数据库重复错误（提取字段名）
  const duplicateMatch = message.match(/Duplicate entry ['"](.+?)['"] for key ['"](.+?)\.(.*?)['"]/i)
  if (duplicateMatch) {
    const fieldName = translateFieldName(duplicateMatch[3] || duplicateMatch[2])
    return `${fieldName}已存在，不可重复`
  }
  
  // 3. 检查外键错误
  const foreignKeyMatch = message.match(/foreign key constraint fails.*?`(.+?)`/i)
  if (foreignKeyMatch) {
    return '关联数据不存在，请先创建关联数据'
  }
  
  // 4. 检查非空错误
  const notNullMatch = message.match(/Column ['"](.+?)['"] cannot be null/i)
  if (notNullMatch) {
    const fieldName = translateFieldName(notNullMatch[1])
    return `${fieldName}不能为空`
  }
  
  // 5. 遍历英文错误映射表
  for (const [en, cn] of Object.entries(ENGLISH_ERROR_MAP)) {
    if (lowerMessage.includes(en.toLowerCase())) {
      return cn
    }
  }
  
  // 6. 包含英文代码/字段名的通用处理
  if (/[a-zA-Z_]{3,}/.test(message)) {
    // 提取可能的字段名并翻译
    let translated = message
    const fieldMatches = message.match(/[a-zA-Z_][a-zA-Z0-9_]*/g) || []
    for (const field of fieldMatches) {
      const cnField = translateFieldName(field)
      if (cnField !== field) {
        translated = translated.replace(new RegExp(`\\b${field}\\b`, 'g'), cnField)
      }
    }
    
    // 如果翻译后仍包含大量英文，返回通用中文错误
    if (/[a-zA-Z]{5,}/.test(translated)) {
      return '操作失败，请检查数据后重试'
    }
    return translated
  }
  
  return message
}

/**
 * 翻译字段名为中文
 * @param {string} fieldName - 英文字段名
 * @returns {string} - 中文字段名
 */
function translateFieldName(fieldName) {
  const fieldMap = {
    // 通用字段
    'name': '名称',
    'code': '编码',
    'id': '编号',
    'status': '状态',
    'type': '类型',
    'remark': '备注',
    'created_at': '创建时间',
    'updated_at': '更新时间',
    
    // 商品相关
    'product_code': '商品编码',
    'product_name': '商品名称',
    'barcode': '条形码',
    'category_id': '分类',
    'category_name': '分类名称',
    'brand': '品牌',
    'specification': '规格',
    'unit_id': '单位',
    'unit_name': '单位',
    'purchase_price': '采购价',
    'sale_price': '销售价',
    'cost_price': '成本价',
    'stock': '库存',
    'min_stock': '最低库存',
    'max_stock': '最高库存',
    'current_stock': '当前库存',
    
    // 客户/供应商
    'customer_name': '客户名称',
    'customer_code': '客户编码',
    'customer_phone': '联系电话',
    'supplier_name': '供应商名称',
    'supplier_code': '供应商编码',
    
    // 仓库
    'warehouse_code': '仓库编码',
    'warehouse_name': '仓库名称',
    'shelf_code': '货架编码',
    'shelf_name': '货架名称',
    
    // 工单
    'wo_no': '工单号',
    'wo_type': '工单类型',
    'wo_status': '工单状态',
    'fault_desc': '故障描述',
    
    // 财务
    'account_name': '账户名称',
    'amount': '金额',
    'total_amount': '总金额',
    'paid_amount': '已付金额',
    'unpaid_amount': '未付金额',
    
    // 用户
    'username': '用户名',
    'real_name': '姓名',
    'password': '密码',
    'phone': '电话',
    'email': '邮箱',
    'role_id': '角色',
    
    // 单据
    'order_no': '单号',
    'order_date': '日期',
    'order_status': '状态',
    
    // 库存单据
    'in_no': '入库单号',
    'out_no': '出库单号',
    'check_no': '盘点单号',
    'transfer_no': '调拨单号',
  }
  
  return fieldMap[fieldName] || fieldName
}

/**
 * 根据业务场景生成友好的错误消息
 * @param {string} action - 操作名称
 * @param {string} module - 模块名称
 * @param {string} error - 原始错误
 * @returns {string}
 */
export function generateBusinessError(action, module, error) {
  const translated = translateError(error)
  
  // 如果已经是友好的中文，直接返回
  if (!/[a-zA-Z]{3,}/.test(translated)) {
    return translated
  }
  
  // 根据操作和模块生成提示
  const actionMap = {
    'create': '新增',
    'add': '新增',
    'save': '保存',
    'update': '更新',
    'edit': '编辑',
    'delete': '删除',
    'remove': '删除',
    'query': '查询',
    'get': '获取',
    'list': '查询',
    'export': '导出',
    'import': '导入',
    'print': '打印',
    'submit': '提交',
    'approve': '审核',
    'reject': '驳回',
    'cancel': '取消',
    'confirm': '确认',
  }
  
  const cnAction = actionMap[action] || action
  return `${cnAction}${module}失败，${translated}`
}

export default {
  translateError,
  generateBusinessError,
}
