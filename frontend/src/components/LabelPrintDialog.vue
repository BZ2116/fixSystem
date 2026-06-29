<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="900px"
    destroy-on-close
    @open="onOpen"
    class="label-print-dialog"
  >
    <!-- 模板选择 -->
    <div class="template-section">
      <div class="section-title">标签模板</div>
      <el-radio-group v-model="selectedTemplate" size="small">
        <el-radio-button label="template1">模板一</el-radio-button>
        <el-radio-button label="template2">模板二</el-radio-button>
        <el-radio-button label="template3">模板三</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 纸张尺寸 -->
    <div class="paper-section">
      <div class="section-title">纸张尺寸</div>
      <el-radio-group v-model="paperSize" size="small">
        <el-radio-button label="6040">60×40mm</el-radio-button>
        <el-radio-button label="4030">40×30mm</el-radio-button>
        <el-radio-button label="3020">30×20mm</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 打印预览 -->
    <div class="print-preview-wrapper">
      <div class="preview-header">
        <span class="preview-title">
          <el-icon><View /></el-icon>
          打印预览
          <el-tag type="info" size="small">共 {{ labelData.length }} 个标签</el-tag>
        </span>
      </div>
      <div class="print-preview" ref="previewContainer">
        <div
          v-for="(item, index) in labelData"
          :key="index"
          class="label-item"
          :style="labelItemStyle"
        >
          <div class="label-content" v-html="generateLabelContent(item, index)"></div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false" size="large">
          <el-icon><Close /></el-icon>
          取消
        </el-button>
        <el-button type="primary" @click="handlePrint" size="large" :loading="printing">
          <el-icon><Printer /></el-icon>
          打印
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Printer, View, Close } from '@element-plus/icons-vue'
import JsBarcode from 'jsbarcode'

const props = defineProps({
  visible: Boolean,
  labelType: { type: String, default: 'product' }, // device / customer / product
  labelData: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const dialogTitle = computed(() => {
  const titles = {
    device: '设备标签打印',
    customer: '客户自带标签打印',
    product: '商品条码标签打印'
  }
  return titles[props.labelType] || '标签打印'
})

const selectedTemplate = ref('template1')
const paperSize = ref('6040')
const printing = ref(false)
const previewContainer = ref(null)

// 纸张尺寸映射
const paperSizeMap = {
  '6040': { width: 60, height: 40 },
  '4030': { width: 40, height: 30 },
  '3020': { width: 30, height: 20 }
}

// 标签类型默认尺寸
const defaultSizeMap = {
  device: '6040',
  customer: '4030',
  product: '3020'
}

const labelItemStyle = computed(() => {
  const size = paperSizeMap[paperSize.value] || { width: 60, height: 40 }
  return {
    width: size.width + 'mm',
    height: size.height + 'mm',
    padding: '1mm',
    boxSizing: 'border-box',
    background: 'white',
    border: '1px solid #333',
    borderRadius: '1mm',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'flex-start',
    overflow: 'hidden',
    margin: '2mm'
  }
})

const onOpen = () => {
  paperSize.value = defaultSizeMap[props.labelType] || '6040'
  nextTick(() => generateBarcodes())
}

// 生成标签内容HTML
const generateLabelContent = (item, index) => {
  const size = paperSizeMap[paperSize.value] || { width: 60, height: 40 }
  const totalItems = props.labelData.length
  const countText = totalItems > 1 ? `共 ${totalItems} 件，第 ${index + 1} 件` : ''
  const itemName = item.product_name || item.device_name || item.name || ''
  const code = item.barcode || item.product_code || item.code || ''
  const spec = item.specification || item.model || ''
  const price = item.sale_price || item.price || ''

  // 根据模板生成不同布局
  const templates = {
    template1: `
      <div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;text-align:center;padding:0.5mm;">
        <div style="font-size:${Math.max(7, size.width * 0.18)}px;font-weight:bold;margin-bottom:0.5mm;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;">${itemName}</div>
        <div style="flex:1;display:flex;align-items:center;justify-content:center;width:100%;min-height:0;">
          <svg class="barcode-svg" data-barcode="${code}" style="max-width:100%;max-height:100%;"></svg>
        </div>
        <div style="font-size:${Math.max(6, size.width * 0.12)}px;color:#666;margin-top:0.5mm;">${code}</div>
        ${countText ? `<div style="font-size:${Math.max(5, size.width * 0.1)}px;color:#999;">${countText}</div>` : ''}
      </div>
    `,
    template2: `
      <div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;text-align:center;padding:0.5mm;">
        <div style="font-size:${Math.max(7, size.width * 0.16)}px;font-weight:bold;margin-bottom:0.5mm;">${itemName}</div>
        ${spec ? `<div style="font-size:${Math.max(6, size.width * 0.12)}px;color:#666;margin-bottom:0.5mm;">${spec}</div>` : ''}
        <div style="flex:1;display:flex;align-items:center;justify-content:center;width:100%;min-height:0;">
          <svg class="barcode-svg" data-barcode="${code}" style="max-width:100%;max-height:100%;"></svg>
        </div>
        ${price ? `<div style="font-size:${Math.max(7, size.width * 0.15)}px;color:#f56c6c;font-weight:bold;">¥${price}</div>` : ''}
        ${countText ? `<div style="font-size:${Math.max(5, size.width * 0.1)}px;color:#999;">${countText}</div>` : ''}
      </div>
    `,
    template3: `
      <div style="width:100%;height:100%;display:flex;flex-direction:row;align-items:center;justify-content:flex-start;text-align:left;padding:0.5mm;gap:1mm;">
        <div style="flex:1;display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start;overflow:hidden;">
          <div style="font-size:${Math.max(7, size.width * 0.16)}px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;">${itemName}</div>
          ${spec ? `<div style="font-size:${Math.max(6, size.width * 0.12)}px;color:#666;">${spec}</div>` : ''}
          ${price ? `<div style="font-size:${Math.max(7, size.width * 0.14)}px;color:#f56c6c;font-weight:bold;">¥${price}</div>` : ''}
          ${countText ? `<div style="font-size:${Math.max(5, size.width * 0.1)}px;color:#999;">${countText}</div>` : ''}
        </div>
        <div style="width:40%;display:flex;align-items:center;justify-content:center;">
          <svg class="barcode-svg" data-barcode="${code}" style="max-width:100%;max-height:100%;"></svg>
        </div>
      </div>
    `
  }

  return templates[selectedTemplate.value] || templates.template1
}

// 生成条码
const generateBarcodes = () => {
  if (!previewContainer.value) return
  nextTick(() => {
    const svgs = previewContainer.value.querySelectorAll('.barcode-svg[data-barcode]')
    svgs.forEach(svg => {
      const code = svg.getAttribute('data-barcode')
      if (code) {
        try {
          JsBarcode(svg, code, {
            format: 'CODE128',
            width: 2,
            height: 40,
            displayValue: false,
            margin: 0
          })
        } catch (e) {
          console.warn('条码生成失败:', code, e)
        }
      }
    })
  })
}

watch(() => props.visible, (val) => {
  if (val) onOpen()
})

watch(() => selectedTemplate.value, () => {
  nextTick(() => generateBarcodes())
})

watch(() => paperSize.value, () => {
  nextTick(() => generateBarcodes())
})

// 打印功能
const handlePrint = () => {
  if (!props.labelData || props.labelData.length === 0) return

  printing.value = true
  const size = paperSizeMap[paperSize.value] || { width: 60, height: 40 }

  // 生成所有标签的打印HTML
  const labelsHtml = props.labelData.map((item, index) => {
    const countText = props.labelData.length > 1 ? `共 ${props.labelData.length} 件，第 ${index + 1} 件` : ''
    const itemName = item.product_name || item.device_name || item.name || ''
    const code = item.barcode || item.product_code || item.code || ''
    const spec = item.specification || item.model || ''
    const price = item.sale_price || item.price || ''

    // 生成条码图片
    let barcodeImg = ''
    if (code) {
      try {
        const canvas = document.createElement('canvas')
        JsBarcode(canvas, code, {
          format: 'CODE128',
          width: 2,
          height: 40,
          displayValue: false,
          margin: 0
        })
        barcodeImg = `<img src="${canvas.toDataURL('image/png')}" style="width:100%;height:auto;" />`
      } catch (e) {
        console.warn('条码生成失败:', code, e)
      }
    }

    // 根据模板生成布局
    const templates = {
      template1: `
        <div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0.5mm;">
          <div style="font-size:${Math.max(7, size.width * 0.18)}px;font-weight:bold;margin-bottom:0.5mm;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;">${itemName}</div>
          <div style="flex:1;display:flex;align-items:center;justify-content:center;width:100%;min-height:0;">${barcodeImg}</div>
          <div style="font-size:${Math.max(6, size.width * 0.12)}px;color:#666;margin-top:0.5mm;">${code}</div>
          ${countText ? `<div style="font-size:${Math.max(5, size.width * 0.1)}px;color:#999;">${countText}</div>` : ''}
        </div>
      `,
      template2: `
        <div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0.5mm;">
          <div style="font-size:${Math.max(7, size.width * 0.16)}px;font-weight:bold;margin-bottom:0.5mm;">${itemName}</div>
          ${spec ? `<div style="font-size:${Math.max(6, size.width * 0.12)}px;color:#666;margin-bottom:0.5mm;">${spec}</div>` : ''}
          <div style="flex:1;display:flex;align-items:center;justify-content:center;width:100%;min-height:0;">${barcodeImg}</div>
          ${price ? `<div style="font-size:${Math.max(7, size.width * 0.15)}px;color:#f56c6c;font-weight:bold;">¥${price}</div>` : ''}
          ${countText ? `<div style="font-size:${Math.max(5, size.width * 0.1)}px;color:#999;">${countText}</div>` : ''}
        </div>
      `,
      template3: `
        <div style="width:100%;height:100%;display:flex;flex-direction:row;align-items:center;justify-content:center;text-align:left;padding:0.5mm;gap:1mm;">
          <div style="flex:1;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;overflow:hidden;">
            <div style="font-size:${Math.max(7, size.width * 0.16)}px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;">${itemName}</div>
            ${spec ? `<div style="font-size:${Math.max(6, size.width * 0.12)}px;color:#666;">${spec}</div>` : ''}
            ${price ? `<div style="font-size:${Math.max(7, size.width * 0.14)}px;color:#f56c6c;font-weight:bold;">¥${price}</div>` : ''}
            ${countText ? `<div style="font-size:${Math.max(5, size.width * 0.1)}px;color:#999;">${countText}</div>` : ''}
          </div>
          <div style="width:40%;display:flex;align-items:center;justify-content:center;">${barcodeImg}</div>
        </div>
      `
    }

    const content = templates[selectedTemplate.value] || templates.template1

    return `
      <div class="label-page" style="
        width: ${size.width}mm;
        height: ${size.height}mm;
        padding: 1mm;
        box-sizing: border-box;
        background: white;
        border: 1px solid #333;
        page-break-inside: avoid;
        page-break-after: always;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        overflow: hidden;
      ">
        ${content}
      </div>
    `
  }).join('')

  const printWindow = window.open('', '_blank')
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${dialogTitle.value}</title>
      <style>
        @page {
          size: ${size.width}mm ${size.height}mm;
          margin: 0;
        }
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        body {
          margin: 0;
          padding: 0;
          font-family: 'Microsoft YaHei', 'SimHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
          background: white;
        }
        .label-page {
          width: ${size.width}mm;
          height: ${size.height}mm;
          padding: 1mm;
          box-sizing: border-box;
          background: white;
          border: 1px solid #333;
          page-break-inside: avoid;
          page-break-after: always;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-start;
          overflow: hidden;
        }
        .label-page:last-child {
          page-break-after: auto;
        }
        @media print {
          body {
            background: white;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .label-page {
            border: 1px solid #333 !important;
            margin: 0 !important;
          }
        }
      </style>
    </head>
    <body>
      ${labelsHtml}
    </body>
    </html>
  `)
  printWindow.document.close()

  setTimeout(() => {
    printWindow.print()
    printWindow.close()
    printing.value = false
  }, 1000)
}
</script>

<style lang="scss" scoped>
.label-print-dialog {
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

.template-section,
.paper-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
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

      .el-icon {
        color: #409eff;
      }
    }
  }

  .print-preview {
    max-height: 500px;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: flex-start;
    gap: 4mm;
  }
}

.label-item {
  .label-content {
    width: 100%;
    height: 100%;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;

  .el-button {
    min-width: 100px;

    .el-icon {
      margin-right: 4px;
    }
  }
}
</style>
