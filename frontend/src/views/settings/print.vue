<template>
  <div class="print-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="header-title">打印模版管理</span>
            <el-select
              v-model="filterType"
              placeholder="全部类型"
              clearable
              style="width: 150px; margin-left: 16px;"
              @change="fetchTemplates"
            >
              <el-option
                v-for="(label, key) in templateTypeMap"
                :key="key"
                :label="label"
                :value="key"
              />
            </el-select>
          </div>
          <div class="header-right">
            <el-button type="warning" plain @click="handleInitDefaults">
              <el-icon><RefreshRight /></el-icon>
              <span>初始化默认模板</span>
            </el-button>
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              <span>新增模版</span>
            </el-button>
          </div>
        </div>
      </template>

      <!-- 卡片网格展示 -->
      <el-row :gutter="20" v-loading="loading">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in templateList" :key="item.id">
          <el-card class="template-card" shadow="hover">
            <div class="template-header">
              <el-icon :size="36" :color="getTemplateIconColor(item.template_type)">
                <Document />
              </el-icon>
              <div class="template-meta">
                <h4 class="template-name">{{ item.template_name }}</h4>
                <el-tag size="small" :type="item.is_default ? 'success' : 'info'">
                  {{ item.is_default ? '默认' : '普通' }}
                </el-tag>
              </div>
            </div>
            <div class="template-body">
              <div class="template-desc">{{ item.description || '暂无描述' }}</div>
              <div class="template-info">
                <span class="info-item">
                  <el-icon><Collection /></el-icon>
                  {{ getTemplateTypeText(item.template_type) }}
                </span>
                <span class="info-item">
                  <el-icon><Document /></el-icon>
                  {{ item.paper_size || 'A4' }}
                </span>
                <span class="info-item update-time">{{ item.updated_at }}</span>
              </div>
            </div>
            <div class="template-footer">
              <el-button type="primary" link size="small" @click="handleEdit(item)">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button type="success" link size="small" @click="handleSetDefault(item)" :disabled="item.is_default">
                <el-icon><Star /></el-icon> 设为默认
              </el-button>
              <el-button type="primary" link size="small" @click="handlePreview(item)">
                <el-icon><View /></el-icon> 预览
              </el-button>
              <el-button type="danger" link size="small" @click="handleDelete(item)">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-if="templateList.length === 0 && !loading" description="暂无打印模版" />
    </el-card>

    <!-- 模版编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模版' : '新增模版'" width="750px" destroy-on-close>
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模版名称" prop="template_name">
              <el-input v-model="form.template_name" placeholder="请输入模版名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模版类型" prop="template_type">
              <el-select v-model="form.template_type" placeholder="请选择模版类型" style="width: 100%">
                <el-option
                  v-for="(label, key) in templateTypeMap"
                  :key="key"
                  :label="label"
                  :value="key"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="模版描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入模版描述" />
        </el-form-item>

        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
          <span class="form-tip">设为默认后，该类型单据将自动使用此模版</span>
        </el-form-item>

        <el-form-item label="模版内容">
          <el-tabs v-model="activeEditorTab" type="border-card">
            <el-tab-pane label="页眉设置" name="header">
              <el-input
                v-model="form.header_content"
                type="textarea"
                :rows="6"
                placeholder="页眉HTML内容，支持变量如：{{company_name}}"
              />
            </el-tab-pane>
            <el-tab-pane label="主体内容" name="body">
              <el-input
                v-model="form.body_content"
                type="textarea"
                :rows="10"
                placeholder="主体HTML内容，支持变量如：{{order_no}}、{{customer_name}}等"
              />
            </el-tab-pane>
            <el-tab-pane label="页脚设置" name="footer">
              <el-input
                v-model="form.footer_content"
                type="textarea"
                :rows="6"
                placeholder="页脚HTML内容"
              />
            </el-tab-pane>
            <el-tab-pane label="样式设置" name="style">
              <el-input
                v-model="form.style_content"
                type="textarea"
                :rows="8"
                placeholder="CSS样式代码"
              />
            </el-tab-pane>
          </el-tabs>
        </el-form-item>

        <el-form-item label="纸张设置">
          <el-row :gutter="10">
            <el-col :span="8">
              <el-select v-model="form.paper_size" placeholder="纸张尺寸" @change="onPaperSizeChange">
                <el-option label="A4" value="A4" />
                <el-option label="A5" value="A5" />
                <el-option label="A6" value="A6" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-input-number
                v-model="form.paper_width"
                :min="10"
                :max="500"
                :disabled="form.paper_size !== 'custom'"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-tip">宽度(mm)</div>
            </el-col>
            <el-col :span="8">
              <el-input-number
                v-model="form.paper_height"
                :min="10"
                :max="500"
                :disabled="form.paper_size !== 'custom'"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-tip">高度(mm)</div>
            </el-col>
          </el-row>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button @click="handlePreviewForm">预览</el-button>
        <el-button type="primary" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 预览弹窗 -->
    <el-dialog v-model="previewVisible" title="模版预览" width="800px" destroy-on-close>
      <div class="preview-container" v-html="previewContent"></div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handlePrintPreview">打印测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Plus,
  Edit,
  Delete,
  View,
  Star,
  RefreshRight,
  Collection
} from '@element-plus/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const templateList = ref([])
const dialogVisible = ref(false)
const previewVisible = ref(false)
const isEdit = ref(false)
const activeEditorTab = ref('body')
const formRef = ref(null)
const previewContent = ref('')
const filterType = ref('')

const form = reactive({
  id: null,
  template_name: '',
  template_type: '',
  description: '',
  is_default: false,
  header_content: '',
  body_content: '',
  footer_content: '',
  style_content: '',
  paper_size: 'A4',
  paper_width: 210,
  paper_height: 297
})

const rules = {
  template_name: [{ required: true, message: '请输入模版名称', trigger: 'blur' }],
  template_type: [{ required: true, message: '请选择模版类型', trigger: 'change' }]
}

const templateTypeMap = {
  work_order: '工单',
  receive: '接件单',
  dispatch: '派工单',
  quote: '报价单',
  sale: '销售单',
  purchase: '采购单',
  return_purchase: '采购退货单',
  return_sale: '销售退货单',
  inventory_in: '入库单',
  inventory_out: '出库单',
  inventory_check: '盘点单',
  transfer: '调拨单',
  receivable: '应收对账单',
  payable: '应付对账单',
  receipt: '收款凭证',
  payment: '付款凭证',
  device_label: '设备标签',
  customer_label: '客户自带标签',
  product_barcode: '商品条码标签'
}

const templateTypeColorMap = {
  work_order: '#E6A23C',
  receive: '#409EFF',
  dispatch: '#67C23A',
  quote: '#F56C6C',
  sale: '#8E44AD',
  purchase: '#67C23A',
  purchase_return: '#909399',
  sale_return: '#909399',
  inbound: '#409EFF',
  outbound: '#E6A23C',
  check: '#F56C6C',
  transfer: '#8E44AD',
  receivable: '#409EFF',
  payable: '#F56C6C',
  receipt: '#67C23A',
  payment: '#E6A23C',
  device_label: '#E6A23C',
  customer_label: '#409EFF',
  product_barcode: '#67C23A'
}

const paperSizeMap = {
  A4: { width: 210, height: 297 },
  A5: { width: 148, height: 210 },
  A6: { width: 105, height: 148 }
}

const getTemplateTypeText = (type) => templateTypeMap[type] || type
const getTemplateIconColor = (type) => templateTypeColorMap[type] || '#409EFF'

const onPaperSizeChange = (size) => {
  if (size !== 'custom' && paperSizeMap[size]) {
    form.paper_width = paperSizeMap[size].width
    form.paper_height = paperSizeMap[size].height
  }
}

const fetchTemplates = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterType.value) {
      params.template_type = filterType.value
    }
    const res = await request.get('/settings/print-templates', { params })
    if (res.code === 200) {
      templateList.value = res.data || []
    }
  } catch (e) {
    console.error('获取模版失败:', e)
    ElMessage.error('获取模版失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    template_name: '',
    template_type: filterType.value || '',
    description: '',
    is_default: false,
    header_content: '<div style="text-align: center;"><h2>{{company_name}}</h2></div>',
    body_content: '<div>订单号：{{order_no}}</div>\n<div>客户：{{customer_name}}</div>',
    footer_content: '<div style="text-align: center;">感谢您的惠顾</div>',
    style_content: 'body { font-size: 14px; }',
    paper_size: 'A4',
    paper_width: 210,
    paper_height: 297
  })
  activeEditorTab.value = 'body'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(form, {
    ...row,
    is_default: !!row.is_default,
    paper_width: row.paper_width || 210,
    paper_height: row.paper_height || 297
  })
  activeEditorTab.value = 'body'
  dialogVisible.value = true
}

const handleSetDefault = async (row) => {
  if (row.is_default) return
  try {
    await ElMessageBox.confirm(
      `确认将模版"${row.template_name}"设为该类型的默认模版？`,
      '提示',
      { type: 'info' }
    )
    const res = await request.put(`/settings/print-templates/${row.id}`, { is_default: 1 })
    if (res.code === 200) {
      ElMessage.success('设置成功')
      fetchTemplates()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('设置默认模版失败:', e)
      ElMessage.error('设置默认模版失败')
    }
  }
}

const handlePreview = (row) => {
  const style = row.style_content ? `<style>${row.style_content}</style>` : ''
  const header = row.header_content || ''
  const body = row.body_content || ''
  const footer = row.footer_content || ''
  previewContent.value = `${style}<div class="print-page">${header}${body}${footer}</div>`
  previewVisible.value = true
}

const handlePreviewForm = () => {
  const style = form.style_content ? `<style>${form.style_content}</style>` : ''
  const header = form.header_content || ''
  const body = form.body_content || ''
  const footer = form.footer_content || ''
  previewContent.value = `${style}<div class="print-page">${header}${body}${footer}</div>`
  previewVisible.value = true
}

const handlePrintPreview = () => {
  const content = document.querySelector('.preview-container')
  if (!content) return

  const printWindow = window.open('', '_blank')
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>打印预览</title>
      <style>
        @page { size: A4; margin: 10mm; }
        body { margin: 0; padding: 20px; font-family: SimSun, serif; font-size: 12px; }
        @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
      </style>
    </head>
    <body>${content.innerHTML}</body>
    </html>
  `)
  printWindow.document.close()
  printWindow.onload = () => {
    printWindow.print()
    printWindow.close()
  }
}

const saveTemplate = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const payload = { ...form, is_default: form.is_default ? 1 : 0 }
    if (isEdit.value) {
      const res = await request.put(`/settings/print-templates/${form.id}`, payload)
      if (res.code === 200) {
        ElMessage.success('修改成功')
        dialogVisible.value = false
        fetchTemplates()
      }
    } else {
      const res = await request.post('/settings/print-templates', payload)
      if (res.code === 200) {
        ElMessage.success('添加成功')
        dialogVisible.value = false
        fetchTemplates()
      }
    }
  } catch (e) {
    console.error('保存模版失败:', e)
    ElMessage.error('保存失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除模版"${row.template_name}"？删除后不可恢复。`,
      '提示',
      { type: 'warning' }
    )
    const res = await request.delete(`/settings/print-templates/${row.id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchTemplates()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除模版失败:', e)
      ElMessage.error('删除失败')
    }
  }
}

const handleInitDefaults = async () => {
  try {
    await ElMessageBox.confirm(
      '确认初始化默认模板？这将创建各类型的默认打印模板（已有模板不会被覆盖）。',
      '初始化默认模板',
      { type: 'info', confirmButtonText: '确认初始化' }
    )
    const res = await request.post('/settings/print-templates/init-defaults')
    if (res.code === 200) {
      ElMessage.success('默认模板初始化成功')
      fetchTemplates()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('初始化默认模板失败:', e)
      ElMessage.error('初始化默认模板失败')
    }
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>

<style lang="scss" scoped>
.print-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;

    .header-left {
      display: flex;
      align-items: center;

      .header-title {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }

    .header-right {
      display: flex;
      gap: 8px;
    }
  }

  .template-card {
    margin-bottom: 20px;
    transition: transform 0.2s;

    &:hover {
      transform: translateY(-2px);
    }

    :deep(.el-card__body) {
      padding: 16px;
    }

    .template-header {
      display: flex;
      align-items: center;
      margin-bottom: 12px;

      .template-meta {
        margin-left: 12px;
        flex: 1;

        .template-name {
          margin: 0 0 4px;
          font-size: 15px;
          font-weight: 600;
          color: #303133;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }

    .template-body {
      .template-desc {
        margin: 0 0 10px;
        font-size: 12px;
        color: #909399;
        height: 36px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        line-height: 18px;
      }

      .template-info {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;

        .info-item {
          display: flex;
          align-items: center;
          gap: 3px;
          font-size: 12px;
          color: #909399;

          .el-icon {
            font-size: 13px;
          }
        }

        .update-time {
          font-size: 11px;
          color: #C0C4CC;
          margin-left: auto;
        }
      }
    }

    .template-footer {
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid #EBEEF5;
      display: flex;
      justify-content: center;
      gap: 4px;
      flex-wrap: wrap;
    }
  }

  .form-tip {
    margin-left: 8px;
    color: #999;
    font-size: 12px;
  }

  .unit-label {
    font-size: 11px;
    color: #999;
    margin-top: 2px;
    text-align: center;
  }

  .preview-container {
    min-height: 400px;
    padding: 20px;
    border: 1px solid #DCDFE6;
    border-radius: 4px;
    background: #fff;
    overflow: auto;
    max-height: 600px;
  }
}
</style>
