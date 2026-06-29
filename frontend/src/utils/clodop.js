/**
 * C-Lodop 打印服务封装
 * 提供统一的打印接口，支持单据打印和标签打印
 */

// C-Lodop 服务地址（本地或云端）
const CLODOP_HOST = 'http://localhost:8000'

/**
 * 检查 C-Lodop 是否已安装并可用
 * 通过检测全局对象 window.CLODOP 或 window.Lodop 判断
 * @returns {Promise<boolean>}
 */
export async function checkClodopInstalled() {
  return new Promise((resolve) => {
    if (typeof window === 'undefined') {
      resolve(false)
      return
    }
    // 直接检测全局 C-Lodop 对象
    if (window.CLODOP || window.Lodop || typeof window.getCLodop === 'function') {
      resolve(true)
      return
    }
    // 尝试加载 C-Lodop 脚本来确认
    const script = document.createElement('script')
    script.src = `${CLODOP_HOST}/CLodopfuncs.js`
    const timer = setTimeout(() => {
      // 3秒超时，未加载成功视为未安装
      script.onload = null
      script.onerror = null
      if (script.parentNode) script.parentNode.removeChild(script)
      resolve(false)
    }, 3000)
    script.onload = () => {
      clearTimeout(timer)
      if (script.parentNode) script.parentNode.removeChild(script)
      resolve(!!(window.CLODOP || window.Lodop))
    }
    script.onerror = () => {
      clearTimeout(timer)
      if (script.parentNode) script.parentNode.removeChild(script)
      resolve(false)
    }
    document.head.appendChild(script)
  })
}

/**
 * 获取 C-Lodop 对象
 * @returns {Object|null}
 */
export function getClodop() {
  if (typeof window === 'undefined') return null
  return window.CLODOP || window.Lodop
}

/**
 * 初始化 C-Lodop 打印对象
 * @returns {Promise<Object>}
 */
export async function initClodop() {
  return new Promise((resolve, reject) => {
    const clodop = getClodop()
    if (clodop) {
      resolve(clodop)
      return
    }

    // 动态加载 C-Lodop JS
    const script = document.createElement('script')
    script.src = `${CLODOP_HOST}/CLodopfuncs.js`
    script.onload = () => {
      const loaded = getClodop()
      if (loaded) {
        resolve(loaded)
      } else {
        reject(new Error('C-Lodop 加载失败'))
      }
    }
    script.onerror = () => {
      reject(new Error('C-Lodop 服务未启动，请先安装并启动 C-Lodop'))
    }
    document.head.appendChild(script)
  })
}

/**
 * 打印单据（A4/A5）
 * @param {Object} options
 * @param {string} options.paperSize - 纸张尺寸：A4 或 A5
 * @param {string} options.html - 打印内容 HTML
 * @param {string} options.orientation - 方向：portrait（纵向）或 landscape（横向）
 * @param {number} options.copies - 打印份数，默认 1
 */
export async function printDocument(options) {
  const { paperSize = 'A4', html, orientation = 'portrait', copies = 1 } = options

  try {
    const lodop = await initClodop()

    lodop.PRINT_INIT('单据打印')
    lodop.SET_PRINT_PAGESIZE(orientation === 'landscape' ? 2 : 1, 0, 0, paperSize)
    lodop.SET_PRINT_COPIES(copies)

    // 添加打印内容
    lodop.ADD_PRINT_HTM(0, 0, '100%', '100%', html)

    // 预览并打印
    lodop.PREVIEW()
  } catch (error) {
    throw new Error(`打印失败：${error.message}`)
  }
}

/**
 * 打印标签
 * @param {Object} options
 * @param {number} options.width - 标签宽度（mm）
 * @param {number} options.height - 标签高度（mm）
 * @param {Array} options.labels - 标签内容数组
 * @param {string} options.template - 模板类型：template1, template2, template3
 */
export async function printLabels(options) {
  const { width = 60, height = 40, labels = [], template = 'template1' } = options

  try {
    const lodop = await initClodop()

    lodop.PRINT_INIT('标签打印')
    lodop.SET_PRINT_PAGESIZE(1, width * 10, height * 10, '') // 单位：0.1mm

    labels.forEach((label, index) => {
      if (index > 0) {
        lodop.NewPage()
      }

      const html = generateLabelHtml(label, template, width, height)
      lodop.ADD_PRINT_HTM(0, 0, '100%', '100%', html)
    })

    lodop.PREVIEW()
  } catch (error) {
    throw new Error(`标签打印失败：${error.message}`)
  }
}

/**
 * 生成标签 HTML
 * @param {Object} label - 标签数据
 * @param {string} template - 模板类型
 * @param {number} width - 标签宽度
 * @param {number} height - 标签高度
 * @returns {string}
 */
function generateLabelHtml(label, template, width, height) {
  const itemName = label.product_name || label.device_name || label.name || ''
  const code = label.barcode || label.product_code || label.code || ''
  const spec = label.specification || label.model || ''
  const price = label.sale_price || label.price || ''
  const countText = label.countText || ''

  const templates = {
    template1: `
      <div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:1mm;font-family:Microsoft YaHei,SimHei,sans-serif;">
        <div style="font-size:${Math.max(7, width * 0.18)}px;font-weight:bold;margin-bottom:0.5mm;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;">${itemName}</div>
        <div style="flex:1;display:flex;align-items:center;justify-content:center;width:100%;min-height:0;">
          <img src="${label.barcodeImage || ''}" style="max-width:100%;max-height:100%;" />
        </div>
        <div style="font-size:${Math.max(6, width * 0.12)}px;color:#666;margin-top:0.5mm;">${code}</div>
        ${countText ? `<div style="font-size:${Math.max(5, width * 0.1)}px;color:#999;">${countText}</div>` : ''}
      </div>
    `,
    template2: `
      <div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:1mm;font-family:Microsoft YaHei,SimHei,sans-serif;">
        <div style="font-size:${Math.max(7, width * 0.16)}px;font-weight:bold;margin-bottom:0.5mm;">${itemName}</div>
        ${spec ? `<div style="font-size:${Math.max(6, width * 0.12)}px;color:#666;margin-bottom:0.5mm;">${spec}</div>` : ''}
        <div style="flex:1;display:flex;align-items:center;justify-content:center;width:100%;min-height:0;">
          <img src="${label.barcodeImage || ''}" style="max-width:100%;max-height:100%;" />
        </div>
        ${price ? `<div style="font-size:${Math.max(7, width * 0.15)}px;color:#f56c6c;font-weight:bold;">¥${price}</div>` : ''}
        ${countText ? `<div style="font-size:${Math.max(5, width * 0.1)}px;color:#999;">${countText}</div>` : ''}
      </div>
    `,
    template3: `
      <div style="width:100%;height:100%;display:flex;flex-direction:row;align-items:center;justify-content:center;text-align:left;padding:1mm;gap:1mm;font-family:Microsoft YaHei,SimHei,sans-serif;">
        <div style="flex:1;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;overflow:hidden;">
          <div style="font-size:${Math.max(7, width * 0.16)}px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;">${itemName}</div>
          ${spec ? `<div style="font-size:${Math.max(6, width * 0.12)}px;color:#666;">${spec}</div>` : ''}
          ${price ? `<div style="font-size:${Math.max(7, width * 0.14)}px;color:#f56c6c;font-weight:bold;">¥${price}</div>` : ''}
          ${countText ? `<div style="font-size:${Math.max(5, width * 0.1)}px;color:#999;">${countText}</div>` : ''}
        </div>
        <div style="width:40%;display:flex;align-items:center;justify-content:center;">
          <img src="${label.barcodeImage || ''}" style="max-width:100%;max-height:100%;" />
        </div>
      </div>
    `
  }

  return templates[template] || templates.template1
}

/**
 * 获取 C-Lodop 安装提示
 * @returns {string}
 */
export function getClodopInstallTip() {
  return '检测到未安装 C-Lodop 打印控件，请按以下步骤操作：\n\n' +
    '1. 下载 C-Lodop 安装包（http://www.c-lodop.com/download.html）\n' +
    '2. 安装并启动 C-Lodop 服务\n' +
    '3. 刷新页面后重试\n\n' +
    '如已安装但仍提示此信息，请检查 C-Lodop 服务是否已启动。'
}

export default {
  checkClodopInstalled,
  getClodop,
  initClodop,
  printDocument,
  printLabels,
  getClodopInstallTip
}
