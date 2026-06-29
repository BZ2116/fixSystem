import request from './request'

// ==================== 接件单基础 CRUD ====================

/** 获取接件单列表（分页、搜索） */
export const getReceiveList = (params) => request.get('/receiveorders', { params })

/** 获取接件单详情 */
export const getReceiveDetail = (id) => request.get(`/receiveorders/${id}`)

/** 创建接件单 */
export const createReceive = (data) => request.post('/receiveorders', data)

/** 更新接件单 */
export const updateReceive = (id, data) => request.put(`/receiveorders/${id}`, data)

// ==================== 流程操作 API ====================

/** 工程师检测 */
export const detectReceive = (id, data) => request.post(`/receiveorders/${id}/detect`, data)

/** 生成报价 */
export const quoteReceive = (id, data) => request.post(`/receiveorders/${id}/quote`, data)

/** 客户确认/拒绝报价 */
export const confirmReceive = (id, data) => request.post(`/receiveorders/${id}/confirm`, data)

/** 领料/采购 */
export const allocateReceive = (id, data) => request.post(`/receiveorders/${id}/allocate`, data)

/** 提交完工 */
export const finishReceive = (id, data) => request.post(`/receiveorders/${id}/finish`, data)

/** 测试设备 */
export const testReceive = (id, data) => request.post(`/receiveorders/${id}/test`, data)

/** 通知取件 */
export const notifyReceive = (id, data) => request.post(`/receiveorders/${id}/notify`, data)

/** 取件完成 */
export const completeReceive = (id, data) => request.post(`/receiveorders/${id}/complete`, data)

/** 取消接件单 */
export const cancelReceive = (id, data) => request.post(`/receiveorders/${id}/cancel`, data)

// ==================== 外店流程 API ====================

/** 送修外店 */
export const externalSendReceive = (id, data) => request.post(`/receiveorders/${id}/external-send`, data)

/** 外店报价 */
export const externalQuoteReceive = (id, data) => request.post(`/receiveorders/${id}/external-quote`, data)

/** 给客户报价（外店流程） */
export const customerQuoteReceive = (id, data) => request.post(`/receiveorders/${id}/customer-quote`, data)

/** 确认送修 */
export const externalConfirmReceive = (id, data) => request.post(`/receiveorders/${id}/external-confirm`, data)

/** 取回设备 */
export const externalReturnReceive = (id, data) => request.post(`/receiveorders/${id}/external-return`, data)

/** 外店取回后测试 */
export const externalRetestReceive = (id, data) => request.post(`/receiveorders/${id}/external-retest`, data)

// ==================== 操作日志 ====================

/** 获取操作日志 */
export const getReceiveLogs = (id) => request.get(`/receiveorders/${id}/logs`)
