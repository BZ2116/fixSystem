<template>
  <el-dialog
    v-model="dialogVisible"
    title="条码打印"
    width="900px"
    destroy-on-close
    @open="onOpen"
  >
    <!-- 打印设置 -->
    <div class="print-settings">
      <el-form :inline="true" :model="settings" label-width="100px">
        <el-form-item label="标签尺寸">
          <el-select v-model="settings.labelSize" style="width: 160px">
            <el-option
              v-for="item in labelSizeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="每行数量">
          <el-input-number v-model="settings.cols" :min="1" :max="5" :step="1" />
        </el-form-item>
        <el-form-item label="条码高度">
          <el-slider v-model="settings.barcodeHeight" :min="30" :max="100" style="width: 120px" />
          <span class="slider-value">{{ settings.barcodeHeight }}px</span>
        </el-form-item>
        <el-form-item label="显示价格">
          <el-switch v-model="settings.showPrice" />
        </el-form-item>
      </el-form>
    </div>

    <!-- 打印预览 -->
    <div class="print-preview-wrapper">
      <div class="preview-header">
        <span>打印预览（共 {{ printList.length }} 个标签）</span>
        <el-button type="primary" size="small" @click="handlePrint">
          <el-icon><Printer /></el-icon>
          打印
        </el-button>
      </div>
      <div ref="previewRef" class="print-preview" :style="previewStyle">
        <div
          v-for="(item, index) in printList"
          :key="index"
          class="barcode-label"
          :style="labelStyle"
        >
          <div class="label-content">
            <div class="product-name">{{ item.product_name }}</div>
            <canvas
              :ref="el => setBarcodeRef(el, index)"
              class="barcode-canvas"
              :style="{ height: settings.barcodeHeight + 'px' }"
            ></canvas>
            <div class="label-info">
              <span class="spec">{{ item.specification }}</span>
              <span v-if="settings.showPrice && item.sale_price" class="price">
                ¥{{ item.sale_price }}
              </span>
            </div>
            <div class="label-code">{{ item.barcode || item.product_code }}</div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="dialogVisible = false">关闭</el-button>
      <el-button type="primary" @click="handlePrint">打印</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Printer } from '@element-plus/icons-vue'
import JsBarcode from 'jsbarcode'

const props = defineProps({
  visible: Boolean,
  products: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

// 标签尺寸选项
const labelSizeOptions = [
  { value: '50x30', label: '50 x 30 mm (小标签)' },
  { value: '60x40', label: '60 x 40 mm (常规)' },
  { value: '70x40', label: '70 x 40 mm (标准)' },
  { value: '80x50', label: '80 x 50 mm (大标签)' },
  { value: '100x60', label: '100 x 60 mm (超大)' }
]

// 打印设置
const settings = ref({
  labelSize: '60x40',
  cols: 2,
  barcodeHeight: 50,
  showPrice: true
})

// 标签尺寸映射（单位：mm）
const sizeMap = {
  '50x30': { width: 50, height: 30 },
  '60x40': { width: 60, height: 40 },
  '70x40': { width: 70, height: 40 },
  '80x50': { width: 80, height: 50 },
  '100x60': { width: 100, height: 60 }
}

// 打印列表（支持单条和批量）
const printList = computed(() => {
  return props.products.map(p => ({
    product_name: p.product_name || '',
    product_code: p.product_code || '',
    barcode: p.barcode || p.product_code || '',
    specification: p.specification || '',
    sale_price: p.sale_price ? parseFloat(p.sale_price).toFixed(2) : '',
    unit_name: p.unit_name || ''
  }))
})

// 预览区域样式
const previewStyle = computed(() => {
  const size = sizeMap[settings.value.labelSize]
  const colWidth = size.width + 4 // 加间距
  return {
    display: 'grid',
    gridTemplateColumns: `repeat(${settings.value.cols}, ${colWidth}mm)`,
    gap: '4mm',
    padding: '10mm',
    background: '#f5f5f5',
    justifyContent: 'center'
  }
})

// 单个标签样式
const labelStyle = computed(() => {
  const size = sizeMap[settings.value.labelSize]
  return {
    width: size.width + 'mm',
    height: size.height + 'mm',
    padding: '2mm',
    boxSizing: 'border-box',
    background: 'white',
    border: '1px solid #ddd',
    borderRadius: '2mm',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden'
  }
})

// 条码 Canvas ref
const barcodeRefs = ref([])
const setBarcodeRef = (el, index) => {
  if (el) barcodeRefs.value[index] = el
}

// 生成条码
const generateBarcodes = () => {
  nextTick(() => {
    printList.value.forEach((item, index) => {
      const canvas = barcodeRefs.value[index]
      if (canvas && item.barcode) {
        try {
          JsBarcode(canvas, item.barcode, {
            format: 'CODE128',
            width: 2,
            height: settings.value.barcodeHeight,
            displayValue: true,
            fontSize: 12,
            margin: 2
          })
        } catch (e) {
          console.warn('条码生成失败:', item.barcode, e)
        }
      }
    })
  })
}

// 监听设置变化和打开弹窗
watch(() => settings.value.barcodeHeight, generateBarcodes)
watch(() => settings.value.labelSize, generateBarcodes)
watch(() => props.visible, (val) => {
  if (val) generateBarcodes()
})

const onOpen = () => {
  barcodeRefs.value = []
  generateBarcodes()
}

// 打印功能
const previewRef = ref(null)

const handlePrint = () => {
  if (!previewRef.value) return

  const printWindow = window.open('', '_blank')
  const size = sizeMap[settings.value.labelSize]
  const colWidth = size.width + 4

  // 使用 Canvas 生成条码图片
  const labelsHtml = printList.value.map((item, index) => {
    // 生成条码 Canvas 并转为图片
    let barcodeImg = ''
    if (item.barcode) {
      try {
        const canvas = document.createElement('canvas')
        JsBarcode(canvas, item.barcode, {
          format: 'CODE128',
          width: 2,
          height: settings.value.barcodeHeight,
          displayValue: true,
          fontSize: 12,
          margin: 2
        })
        barcodeImg = `<img src="${canvas.toDataURL('image/png')}" style="width:100%;height:auto;" />`
      } catch (e) {
        console.warn('条码生成失败:', item.barcode, e)
      }
    }

    return `
      <div class="barcode-label">
        <div class="label-content">
          <div class="product-name">${item.product_name || ''}</div>
          <div class="barcode-img">${barcodeImg}</div>
          <div class="label-info">
            <span class="spec">${item.specification || ''}</span>
            ${settings.value.showPrice && item.sale_price ? `<span class="price">¥${item.sale_price}</span>` : ''}
          </div>
          <div class="label-code">${item.barcode || item.product_code || ''}</div>
        </div>
      </div>
    `
  }).join('')

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>条码打印</title>
      <style>
        @page {
          size: auto;
          margin: 5mm;
        }
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        body {
          margin: 0;
          padding: 5mm;
          font-family: 'Microsoft YaHei', 'SimHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
          background: white;
        }
        .print-container {
          display: grid;
          grid-template-columns: repeat(${settings.value.cols}, ${colWidth}mm);
          gap: 2mm;
          justify-content: start;
        }
        .barcode-label {
          width: ${size.width}mm;
          height: ${size.height}mm;
          padding: 1mm;
          box-sizing: border-box;
          background: white;
          border: 1px solid #000;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          page-break-inside: avoid;
        }
        .label-content {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: space-between;
          padding: 1mm;
        }
        .product-name {
          font-size: ${Math.max(7, size.width * 0.22)}px;
          font-weight: bold;
          text-align: center;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          width: 100%;
          line-height: 1.1;
          color: #000;
        }
        .barcode-img {
          width: 100%;
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 0;
        }
        .barcode-img img {
          max-width: 100%;
          max-height: 100%;
          width: auto;
          height: auto;
        }
        .label-info {
          display: flex;
          justify-content: space-between;
          width: 100%;
          font-size: ${Math.max(6, size.width * 0.15)}px;
          color: #000;
          line-height: 1.1;
        }
        .spec {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .price {
          color: #000;
          font-weight: bold;
          margin-left: 1mm;
        }
        .label-code {
          font-size: ${Math.max(6, size.width * 0.14)}px;
          color: #000;
          text-align: center;
          font-family: monospace;
          line-height: 1.1;
        }
        @media print {
          body { 
            -webkit-print-color-adjust: exact; 
            print-color-adjust: exact;
            background: white;
          }
          .barcode-label { 
            border: 1px solid #000 !important; 
          }
        }
      </style>
    </head>
    <body>
      <div class="print-container">
        ${labelsHtml}
      </div>
    </body>
    </html>
  `)
  printWindow.document.close()
  
  // 等待图片加载完成后再打印
  setTimeout(() => {
    printWindow.focus()
    printWindow.print()
    printWindow.close()
  }, 1000)
}
</script>

<style lang="scss" scoped>
.print-settings {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 16px;

  .slider-value {
    margin-left: 8px;
    font-size: 13px;
    color: #606266;
    min-width: 40px;
    display: inline-block;
  }
}

.print-preview-wrapper {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background: #f5f7fa;
    border-bottom: 1px solid #e4e7ed;
    font-size: 14px;
    color: #606266;
  }

  .print-preview {
    max-height: 500px;
    overflow-y: auto;
  }
}

.barcode-label {
  .label-content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 1mm;
  }

  .product-name {
    font-weight: bold;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
    line-height: 1.1;
    color: #303133;
  }

  .barcode-canvas {
    width: 100%;
    flex: 1;
  }

  .label-info {
    display: flex;
    justify-content: space-between;
    width: 100%;
    color: #606266;
    line-height: 1.1;

    .spec {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 10px;
    }

    .price {
      color: #f56c6c;
      font-weight: bold;
      margin-left: 1mm;
      font-size: 10px;
    }
  }

  .label-code {
    color: #909399;
    text-align: center;
    font-family: monospace;
    font-size: 9px;
    line-height: 1.1;
  }
}
</style>
