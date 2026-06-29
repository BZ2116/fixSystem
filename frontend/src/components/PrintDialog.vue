<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="1000px"
    destroy-on-close
    @open="onOpen"
    class="print-dialog"
  >
    <!-- 模板选择标签栏 -->
    <div class="template-tabs" v-if="templateList.length > 0">
      <div class="section-title">打印模板</div>
      <el-radio-group v-model="selectedId" size="small" @change="onTemplateChange">
        <el-radio-button
          v-for="t in templateList"
          :key="t.id"
          :label="t.id"
        >
          {{ t.template_name }}
          <el-tag v-if="t.is_default === 1" size="small" type="success" style="margin-left:4px">默认</el-tag>
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 纸张尺寸选择 -->
    <div class="paper-section" v-if="isLabel">
      <div class="section-title">纸张尺寸</div>
      <el-radio-group v-model="paperSize" size="small">
        <el-radio-button label="6040">60×40mm</el-radio-button>
        <el-radio-button label="4030">40×30mm</el-radio-button>
        <el-radio-button label="3020">30×20mm</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 打印引擎选择 -->
    <div class="engine-section">
      <div class="section-title">打印引擎</div>
      <el-radio-group v-model="useClodop" size="small">
        <el-radio-button :label="false">浏览器打印</el-radio-button>
        <el-radio-button :label="true" :disabled="!clodopReady">
          C-Lodop 打印
          <el-tag v-if="!clodopReady" size="small" type="danger">未安装</el-tag>
        </el-radio-button>
      </el-radio-group>
      <el-link v-if="!clodopReady" type="primary" :underline="false" @click="showClodopTip" style="margin-left:10px;font-size:12px">如何安装？</el-link>
    </div>

    <!-- 打印预览区域 -->
    <div class="print-preview-wrapper">
      <div class="preview-header">
        <span class="preview-title">
          <el-icon><View /></el-icon>
          打印预览
          <el-tag v-if="pageTotal > 1" type="info" size="small">共 {{ pageTotal }} 页</el-tag>
        </span>
        <el-pagination
          v-if="pageTotal > 1"
          v-model:current-page="curPage"
          :page-size="1"
          :total="pageTotal"
          layout="prev, pager, next"
          small
        />
      </div>
      <div class="print-preview">
        <div v-if="loading" style="text-align:center;padding:40px;color:#909399">
          <p>正在加载打印模板...</p>
        </div>
        <div v-if="!previewHtml" style="text-align:center;padding:40px;color:#909399">
          <p>没有可用的打印模板内容</p>
          <p style="font-size:12px;margin-top:8px">请先在「系统设置 > 打印模板管理」中配置模板</p>
          <p style="font-size:12px;margin-top:8px;color:#e6a23c">调试：模板数={{templateList.length}}, 当前模板={{activeTemplate ? activeTemplate.template_name : '无'}}, 数据字段={{Object.keys(printData).length}}个</p>
        </div>
        <div
          v-else
          ref="printContentRef"
          class="print-content"
          :style="containerStyle"
          v-html="previewHtml"
        ></div>
      </div>
    </div>

    <!-- 底部操作按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false" size="large">
          <el-icon><Close /></el-icon> 取消
        </el-button>
        <el-button type="primary" @click="handlePrint" size="large" :loading="printing">
          <el-icon><Printer /></el-icon> 打印
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Printer, View, Close } from '@element-plus/icons-vue'
import request from '@/api/request'
import { checkClodopInstalled, initClodop, getClodopInstallTip } from '@/utils/clodop'

const props = defineProps({
  visible: { type: Boolean, default: false },
  templateType: { type: String, default: '' },
  printData: { type: Object, default: () => ({}) },
  labelData: { type: Array, default: null },
  printMode: { type: String, default: 'document' },
  labelType: { type: String, default: '' }
})

const emit = defineEmits(['update:visible'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const isLabel = computed(() => props.printMode === 'label')

const dialogTitle = computed(() => {
  if (isLabel.value) {
    const map = { device: '设备标签打印', customer: '客户自带标签打印', product: '商品条码标签打印' }
    return map[props.labelType] || '标签打印'
  }
  return '单据打印'
})

// ========== 状态 ==========
const templateList = ref([])
const selectedId = ref(null)
const activeTemplate = ref(null)
const paperSize = ref('A4')
const curPage = ref(1)
const printContentRef = ref(null)
const printing = ref(false)
const loading = ref(false)
const renderedPages = ref([])
const useClodop = ref(false)
const clodopReady = ref(false)

const labelTypeMap = { device: 'device_label', customer: 'customer_label', product: 'product_barcode' }
const labelSizeMap = { device: '6040', customer: '4030', product: '3020' }

const sizeConfig = {
  A4: { w: 210, h: 297 },
  A5: { w: 148, h: 210 },
  '6040': { w: 60, h: 40 },
  '4030': { w: 40, h: 30 },
  '3020': { w: 30, h: 20 }
}

const curSize = computed(() => sizeConfig[paperSize.value] || { w: 210, h: 297 })

const containerStyle = computed(() => ({
  width: curSize.value.w + 'mm',
  minHeight: curSize.value.h + 'mm',
  padding: isLabel.value ? '1mm' : '10mm',
  boxSizing: 'border-box',
  background: 'white',
  border: '1px solid #ddd',
  borderRadius: '2mm',
  margin: '0 auto',
  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
}))

const pageTotal = computed(() => renderedPages.value.length)

// ========== 模板变量替换 ==========
function fillTemplate(htmlStr, data) {
  if (!htmlStr || !data) return htmlStr || ''
  let result = htmlStr
  // 遍历数据对象，替换所有 {{key}} 为实际值
  const keys = Object.keys(data)
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i]
    const val = data[key]
    const strVal = val !== null && val !== undefined ? String(val) : ''
    // 用字符串分割替换，最简单可靠
    while (result.indexOf('{{' + key + '}}') !== -1) {
      result = result.replace('{{' + key + '}}', strVal)
    }
  }
  // 把剩余未替换的 {{xxx}} 替换为空
  result = result.replace(/\{\{[^}]*\}\}/g, '')
  return result
}

// ========== 构建页面HTML ==========
function buildPages() {
  const tpl = activeTemplate.value
  const data = props.printData
  const pages = []

  // 调试信息
  console.log('[PrintDialog] buildPages called')
  console.log('[PrintDialog] activeTemplate:', tpl ? tpl.template_name : 'NULL')
  console.log('[PrintDialog] printData keys:', data ? Object.keys(data) : 'NO DATA')
  console.log('[PrintDialog] printData:', JSON.stringify(data).substring(0, 500))

  if (isLabel.value) {
    // 标签模式
    const items = props.labelData || []
    items.forEach((item, idx) => {
      const countText = items.length > 1 ? '共 ' + items.length + ' 件，第 ' + (idx + 1) + ' 件' : ''
      const merged = Object.assign({}, item, { count_text: countText })

      let bodyHtml = ''
      if (tpl && tpl.body_content) {
        bodyHtml = fillTemplate(tpl.body_content, merged)
      } else {
        // 前端默认标签
        const name = item.product_name || item.device_name || item.name || ''
        const code = item.barcode || item.product_code || item.code || ''
        const spec = item.specification || item.model || ''
        const price = item.sale_price || item.price || ''
        bodyHtml = '<div style="text-align:center;padding:1mm">' +
          '<div style="font-weight:bold;font-size:' + Math.max(7, curSize.value.w * 0.2) + 'px">' + name + '</div>' +
          '<div style="margin:1mm 0"><svg class="barcode-svg" data-barcode="' + code + '" style="max-width:100%;max-height:100%"></svg></div>' +
          (spec ? '<div style="font-size:' + Math.max(6, curSize.value.w * 0.15) + 'px;color:#333">' + spec + '</div>' : '') +
          (price ? '<div style="font-size:' + Math.max(7, curSize.value.w * 0.15) + 'px;color:#f56c6c;font-weight:bold">¥' + price + '</div>' : '') +
          '<div style="font-size:' + Math.max(6, curSize.value.w * 0.14) + 'px;color:#666;font-family:monospace">' + code + '</div>' +
          (countText ? '<div style="font-size:' + Math.max(6, curSize.value.w * 0.12) + 'px;color:#999">' + countText + '</div>' : '') +
          '</div>'
      }

      pages.push({
        html: bodyHtml,
        pageNum: idx + 1,
        totalPages: items.length
      })
    })
  } else {
    // 单据模式
    if (!tpl) {
      renderedPages.value = []
      return
    }

    const headerHtml = fillTemplate(tpl.header_content || '', data)
    const bodyHtml = fillTemplate(tpl.body_content || '', data)
    const footerHtml = fillTemplate(tpl.footer_content || '', data)

    if (!bodyHtml) {
      renderedPages.value = []
      return
    }

    // 解析表格分页
    const tableRe = /<table[\s\S]*?<\/table>/i
    const tableMatch = bodyHtml.match(tableRe)

    if (!tableMatch) {
      pages.push({ header: headerHtml, body: bodyHtml, footer: footerHtml, pageNum: 1, totalPages: 1 })
    } else {
      const before = bodyHtml.substring(0, tableMatch.index)
      const after = bodyHtml.substring(tableMatch.index + tableMatch[0].length)
      const tableHtml = tableMatch[0]

      // 提取行
      const theadRe = /<thead>[\s\S]*?<\/thead>/i
      const tbodyRe = /<tbody>([\s\S]*?)<\/tbody>/i
      const trRe = /<tr[\s\S]*?<\/tr>/gi

      const theadMatch = tableHtml.match(theadRe)
      const tbodyMatch = tableHtml.match(tbodyRe)

      let header = ''
      let rows = []

      if (theadMatch && tbodyMatch) {
        header = theadMatch[0]
        rows = tbodyMatch[1].match(trRe) || []
      } else {
        const allRows = tableHtml.match(trRe) || []
        if (allRows.length > 0) {
          header = '<thead>' + allRows[0] + '</thead>'
          rows = allRows.slice(1)
        }
      }

      if (rows.length === 0) {
        pages.push({ header: headerHtml, body: bodyHtml, footer: footerHtml, pageNum: 1, totalPages: 1 })
      } else {
        const maxRows = paperSize.value === 'A4' ? 15 : 10
        const totalPg = Math.ceil(rows.length / maxRows)
        for (let i = 0; i < totalPg; i++) {
          const start = i * maxRows
          const end = Math.min(start + maxRows, rows.length)
          const pageBody = before +
            '<table class="print-table" style="width:100%;border-collapse:collapse;font-size:12px">' +
            header +
            '<tbody>' + rows.slice(start, end).join('') + '</tbody>' +
            '</table>' +
            after

          pages.push({
            header: headerHtml,
            body: pageBody,
            footer: footerHtml,
            pageNum: i + 1,
            totalPages: totalPg
          })
        }
      }
    }
  }

  renderedPages.value = pages
}

// ========== 预览HTML ==========
const previewHtml = computed(() => {
  const pages = renderedPages.value
  if (pages.length === 0) return ''
  const page = pages[curPage.value - 1]
  if (!page) return ''

  if (isLabel.value) {
    return page.html
  }

  const pageInfo = page.totalPages > 1
    ? '<div style="text-align:center;font-size:11px;color:#666;margin-top:8px;padding-top:4px;border-top:1px dashed #ddd">共 ' + page.totalPages + ' 页 / 第 ' + page.pageNum + ' 页</div>'
    : ''

  return '<div style="width:100%">' +
    page.header +
    '<div style="margin:8px 0">' + page.body + '</div>' +
    page.footer +
    pageInfo +
    '</div>'
})

// ========== 事件处理 ==========
const onOpen = async () => {
  curPage.value = 1
  printing.value = false
  loading.value = true
  templateList.value = []
  activeTemplate.value = null
  renderedPages.value = []

  // 检查 C-Lodop 安装状态
  clodopReady.value = await checkClodopInstalled()

  // 标签模式设置默认纸张
  if (isLabel.value && props.labelType) {
    paperSize.value = labelSizeMap[props.labelType] || '6040'
  } else {
    paperSize.value = 'A4'
  }

  try {
    // 确定模板类型
    const tplType = isLabel.value
      ? (labelTypeMap[props.labelType] || props.templateType)
      : props.templateType

    const res = await request.get('/settings/print-templates', {
      params: { template_type: tplType }
    })

    if (res.code === 200 && res.data && res.data.length > 0) {
      templateList.value = res.data
      // 找默认模板
      const defaultTpl = res.data.find(function(t) { return t.is_default === 1 || t.is_default === true })
      const firstTpl = defaultTpl || res.data[0]
      selectedId.value = firstTpl.id
      activeTemplate.value = firstTpl

      // 设置纸张
      if (firstTpl.paper_size && sizeConfig[firstTpl.paper_size]) {
        paperSize.value = firstTpl.paper_size
      }
    } else {
      if (!isLabel.value) {
        ElMessage.warning('没有可用的打印模板，请先在打印模版管理中添加')
      }
    }
  } catch (err) {
    console.error('获取打印模板失败:', err)
    ElMessage.error('获取打印模板失败')
  }

  loading.value = false

  // 等待 props.printData 更新后再构建页面
  nextTick(function() {
    buildPages()
    // 标签模式生成条码
    if (isLabel.value) {
      nextTick(function() { generateBarcodes() })
    }
  })
}

const onTemplateChange = (id) => {
  const tpl = templateList.value.find(function(t) { return t.id === id })
  if (tpl) {
    activeTemplate.value = tpl
    if (tpl.paper_size && sizeConfig[tpl.paper_size]) {
      paperSize.value = tpl.paper_size
    }
    curPage.value = 1
    buildPages()
    if (isLabel.value) {
      nextTick(function() { generateBarcodes() })
    }
  }
}

// 生成条码
const generateBarcodes = () => {
  if (!printContentRef.value) return
  const svgs = printContentRef.value.querySelectorAll('.barcode-svg[data-barcode]')
  svgs.forEach(function(svg) {
    const code = svg.getAttribute('data-barcode')
    if (code) {
      try {
        const canvas = document.createElement('canvas')
        import('jsbarcode').then(function(mod) {
          const JsBarcode = mod.default
          JsBarcode(canvas, code, {
            format: 'CODE128', width: 2, height: 40,
            displayValue: false, margin: 0
          })
          // 将canvas转为img放入svg
          const img = document.createElement('img')
          img.src = canvas.toDataURL('image/png')
          img.style.maxWidth = '100%'
          img.style.maxHeight = '100%'
          svg.innerHTML = ''
          svg.appendChild(img)
        })
      } catch (e) {
        console.warn('条码生成失败:', code, e)
      }
    }
  })
}

// ========== 打印 ==========
const showClodopTip = () => {
  ElMessageBox.alert(getClodopInstallTip(), 'C-Lodop 安装说明', {
    confirmButtonText: '我知道了',
    type: 'info'
  })
}

const handlePrint = async () => {
  if (renderedPages.value.length === 0) return
  printing.value = true

  // C-Lodop 打印
  if (useClodop.value) {
    try {
      const lodop = await initClodop()
      const size = curSize.value
      const tpl = activeTemplate.value

      lodop.PRINT_INIT(dialogTitle.value)

      if (isLabel.value) {
        lodop.SET_PRINT_PAGESIZE(1, size.w * 10, size.h * 10, '')
        renderedPages.value.forEach(function(page, idx) {
          if (idx > 0) lodop.NewPage()
          lodop.ADD_PRINT_HTM(0, 0, '100%', '100%', page.html)
        })
      } else {
        lodop.SET_PRINT_PAGESIZE(1, 0, 0, paperSize.value)
        renderedPages.value.forEach(function(page, idx) {
          if (idx > 0) lodop.NewPage()
          var pageHtml = '<div style="padding:10mm">' +
            page.header +
            '<div style="margin:8px 0">' + page.body + '</div>' +
            page.footer +
            (page.totalPages > 1 ? '<div style="text-align:center;font-size:11px;color:#666;margin-top:8px;border-top:1px dashed #ddd;padding-top:4px">共 ' + page.totalPages + ' 页 / 第 ' + page.pageNum + ' 页</div>' : '') +
            '</div>'
          lodop.ADD_PRINT_HTM(0, 0, '100%', '100%', pageHtml)
        })
      }

      lodop.PREVIEW()
      printing.value = false
      return
    } catch (error) {
      try {
        await ElMessageBox.confirm(
          error.message + '\n\n是否使用浏览器默认打印方式？',
          'C-Lodop 打印失败',
          { confirmButtonText: '使用浏览器打印', cancelButtonText: '取消', type: 'warning' }
        )
        // 用户选择浏览器打印，继续执行下面的浏览器打印逻辑
      } catch (e) {
        printing.value = false
        return
      }
    }
  }

  // 浏览器打印
  const size = curSize.value
  const tpl = activeTemplate.value
  const pw = (tpl && tpl.paper_width) || size.w
  const ph = (tpl && tpl.paper_height) || size.h

  // 构建所有页面的HTML（与预览完全一致）
  let allHtml = ''
  renderedPages.value.forEach(function(page, idx) {
    if (idx > 0) allHtml += '<div style="page-break-before:always"></div>'

    if (isLabel.value) {
      allHtml += page.html
    } else {
      const pageInfo = page.totalPages > 1
        ? '<div style="text-align:center;font-size:11px;color:#666;margin-top:8px;padding-top:4px;border-top:1px dashed #ddd">共 ' + page.totalPages + ' 页 / 第 ' + page.pageNum + ' 页</div>'
        : ''
      allHtml += '<div class="print-page">' +
        page.header +
        '<div style="margin:8px 0">' + page.body + '</div>' +
        page.footer +
        pageInfo +
        '</div>'
    }
  })

  const styleContent = (tpl && tpl.style_content) || ''
  const w = window.open('', '_blank')
  w.document.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' + dialogTitle.value + '</title>')
  w.document.write('<style>')
  w.document.write('@page { size: ' + pw + 'mm ' + ph + 'mm; margin: ' + (isLabel.value ? '0' : '5mm') + '; }')
  w.document.write('* { margin:0; padding:0; box-sizing:border-box; }')
  w.document.write('body { margin:0; padding:0; font-family:Microsoft YaHei,SimHei,sans-serif; background:white; }')
  w.document.write('.print-page { width:' + pw + 'mm; padding:' + (isLabel.value ? '1mm' : '8mm') + '; box-sizing:border-box; page-break-inside:avoid; page-break-after:always; }')
  w.document.write('.print-page:last-child { page-break-after:auto; }')
  w.document.write('table { width:100%; border-collapse:collapse; font-size:12px; }')
  w.document.write('th, td { border:1px solid #333; padding:6px 8px; text-align:center; }')
  w.document.write('th { background:#f5f5f5; font-weight:bold; }')
  if (styleContent) w.document.write(styleContent)
  w.document.write('@media print { body { background:white; -webkit-print-color-adjust:exact; print-color-adjust:exact; } .print-page { border:none !important; margin:0 !important; } }')
  w.document.write('</style></head><body>')
  w.document.write(allHtml)
  w.document.write('</body></html>')
  w.document.close()

  // 标签需要等条码生成
  if (isLabel.value) {
    setTimeout(function() {
      const svgs = w.document.querySelectorAll('.barcode-svg[data-barcode]')
      if (svgs.length === 0) {
        w.print(); w.close(); printing.value = false; return
      }
      let done = 0
      const total = svgs.length
      svgs.forEach(function(svg) {
        const code = svg.getAttribute('data-barcode')
        if (code) {
          const canvas = document.createElement('canvas')
          import('jsbarcode').then(function(mod) {
            mod.default(canvas, code, { format:'CODE128', width:2, height:40, displayValue:false, margin:0 })
            const img = document.createElement('img')
            img.src = canvas.toDataURL('image/png')
            img.style.maxWidth = '100%'
            img.style.maxHeight = '100%'
            svg.innerHTML = ''
            svg.appendChild(img)
            done++
            if (done >= total) { setTimeout(function() { w.print(); w.close(); printing.value = false }, 300) }
          }).catch(function() {
            done++
            if (done >= total) { setTimeout(function() { w.print(); w.close(); printing.value = false }, 300) }
          })
        } else {
          done++
          if (done >= total) { setTimeout(function() { w.print(); w.close(); printing.value = false }, 300) }
        }
      })
    }, 500)
  } else {
    w.onload = function() { w.print(); w.close(); printing.value = false }
  }
}

// 监听printData变化，重新构建页面
watch(function() { return JSON.stringify(props.printData) }, function() {
  if (props.visible && activeTemplate.value) {
    buildPages()
  }
})

watch(function() { return props.visible }, function(val) {
  if (!val) {
    curPage.value = 1
    renderedPages.value = []
    activeTemplate.value = null
    templateList.value = []
  }
})
</script>

<style lang="scss" scoped>
.print-dialog {
  :deep(.el-dialog__body) {
    padding: 20px;
  }
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}

.template-tabs {
  margin-bottom: 16px;
}

.paper-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.engine-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.print-preview-wrapper {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #fff;
    border-bottom: 1px solid #e4e7ed;

    .preview-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 600;
      color: #303133;

      .el-icon { color: #409eff; }
    }
  }

  .print-preview {
    max-height: 500px;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: flex-start;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;

  .el-button {
    min-width: 100px;
    .el-icon { margin-right: 4px; }
  }
}
</style>
