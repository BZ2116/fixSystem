<template>
  <div class="invoices-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>采购发票管理</span>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="发票号/供应商名/采购单号" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-select v-model="searchForm.supplier_id" placeholder="选择供应商" clearable filterable style="width: 180px">
            <el-option v-for="s in suppliers" :key="s.id" :label="s.supplier_name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="待认证" :value="0" />
            <el-option label="已认证" :value="1" />
            <el-option label="已抵扣" :value="2" />
            <el-option label="已作废" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 操作按钮行 -->
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增发票</el-button>
        <el-button type="success" :icon="Check" @click="handleBatchCertify" :disabled="selectedRows.length === 0">批量认证</el-button>
        <el-button type="warning" :icon="Download" @click="handleExport">导出</el-button>
      </div>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="invoice_no" label="发票号码" width="160" />
        <el-table-column prop="invoice_code" label="发票代码" width="140" />
        <el-table-column prop="invoice_type" label="发票类型" width="160" align="center">
          <template #default="{ row }">
            <el-tag :type="row.invoice_type === 2 ? 'danger' : ''" size="small">
              {{ row.invoice_type === 1 ? '普通发票' : '增值税专用发票' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_order_no" label="关联采购单号" width="150" />
        <el-table-column prop="supplier_name" label="供应商名称" min-width="150" />
        <el-table-column prop="amount" label="不含税金额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount">{{ row.amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="tax_rate" label="税率" width="80" align="center">
          <template #default="{ row }">
            {{ row.tax_rate != null ? row.tax_rate + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="tax_amount" label="税额" width="100" align="right">
          <template #default="{ row }">
            {{ row.tax_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="价税合计" width="120" align="right">
          <template #default="{ row }">
            <span class="total">{{ row.total_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="invoice_date" label="开票日期" width="120" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="success" link size="small" @click="handleCertify(row)" v-if="row.status === 0">认证</el-button>
            <el-button type="warning" link size="small" @click="handleDeduct(row)" v-if="row.status === 1">抵扣</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)" v-if="row.status === 0">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑发票' : '新增发票'" width="700px" destroy-on-close>
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发票号码" prop="invoice_no">
              <el-input v-model="formData.invoice_no" placeholder="留空自动生成" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发票代码" prop="invoice_code">
              <el-input v-model="formData.invoice_code" placeholder="请输入发票代码" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发票类型" prop="invoice_type">
              <el-select v-model="formData.invoice_type" placeholder="请选择发票类型" style="width: 100%">
                <el-option label="普通发票" :value="1" />
                <el-option label="增值税专用发票" :value="2" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联采购单" prop="purchase_order_id">
              <el-select
                v-model="formData.purchase_order_id"
                placeholder="请选择采购单"
                filterable
                clearable
                style="width: 100%"
                @change="onPurchaseOrderChange"
              >
                <el-option
                  v-for="o in purchaseOrders"
                  :key="o.id"
                  :label="o.purchase_no"
                  :value="o.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="供应商" prop="supplier_name">
              <el-input v-model="formData.supplier_name" placeholder="选择采购单后自动填充，也可手动输入" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开票日期" prop="invoice_date">
              <el-date-picker v-model="formData.invoice_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="不含税金额" prop="amount">
              <el-input-number v-model="formData.amount" :precision="2" :min="0" :controls="false" placeholder="0.00" style="width: 100%" @change="calculateTax" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="税率%" prop="tax_rate">
              <el-input-number v-model="formData.tax_rate" :precision="2" :min="0" :max="100" :controls="false" placeholder="0" style="width: 100%" @change="calculateTax" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="税额" prop="tax_amount">
              <el-input-number v-model="formData.tax_amount" :precision="2" :min="0" :controls="false" placeholder="0.00" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="价税合计">
              <span class="total">{{ computedTotalAmount }}</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="请输入备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="detailVisible" title="发票详情" width="700px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="发票号码">{{ currentInvoice.invoice_no }}</el-descriptions-item>
        <el-descriptions-item label="发票代码">{{ currentInvoice.invoice_code }}</el-descriptions-item>
        <el-descriptions-item label="发票类型">
          <el-tag :type="currentInvoice.invoice_type === 2 ? 'danger' : ''" size="small">
            {{ currentInvoice.invoice_type === 1 ? '普通发票' : '增值税专用发票' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="关联采购单号">{{ currentInvoice.purchase_order_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="供应商名称">{{ currentInvoice.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="开票日期">{{ currentInvoice.invoice_date }}</el-descriptions-item>
        <el-descriptions-item label="不含税金额">{{ currentInvoice.amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="税率">{{ currentInvoice.tax_rate != null ? currentInvoice.tax_rate + '%' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="税额">{{ currentInvoice.tax_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="价税合计">
          <span class="total">{{ currentInvoice.total_amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentInvoice.status)" size="small">{{ getStatusText(currentInvoice.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentInvoice.created_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentInvoice.remark || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Check, Download } from '@element-plus/icons-vue'
import {
  getPurchaseInvoiceList,
  getPurchaseInvoiceDetail,
  createPurchaseInvoice,
  updatePurchaseInvoice,
  deletePurchaseInvoice,
  certifyPurchaseInvoice,
  deductPurchaseInvoice
} from '@/api/finance'
import { getSupplierList } from '@/api/supplier'
import { getPurchaseList } from '@/api/purchase'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const suppliers = ref([])
const purchaseOrders = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const currentInvoice = ref({})
const selectedRows = ref([])

const searchForm = reactive({
  keyword: '',
  supplier_id: null,
  status: null,
  date_range: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  invoice_no: '',
  invoice_code: '',
  invoice_type: null,
  purchase_order_id: null,
  supplier_name: '',
  amount: 0,
  tax_rate: 0,
  tax_amount: 0,
  invoice_date: '',
  remark: ''
})

const rules = {
  invoice_type: [{ required: true, message: '请选择发票类型', trigger: 'change' }],
  invoice_date: [{ required: true, message: '请选择开票日期', trigger: 'change' }]
}

// 自动计算价税合计
const computedTotalAmount = computed(() => {
  const amount = formData.amount || 0
  const taxAmount = formData.tax_amount || 0
  return (amount + taxAmount).toFixed(2)
})

// 监听不含税金额和税率变化，自动计算税额
const calculateTax = () => {
  if (formData.amount != null && formData.tax_rate != null) {
    formData.tax_amount = parseFloat(((formData.amount || 0) * (formData.tax_rate || 0) / 100).toFixed(2))
  }
}

// 监听不含税金额和税率变化自动计算
watch(() => formData.amount, () => {
  calculateTax()
})

watch(() => formData.tax_rate, () => {
  calculateTax()
})

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'primary', 2: 'success', 3: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '待认证', 1: '已认证', 2: '已抵扣', 3: '已作废' }
  return texts[status] || '未知'
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      supplier_id: searchForm.supplier_id,
      status: searchForm.status,
      start_date: searchForm.date_range?.[0],
      end_date: searchForm.date_range?.[1]
    }
    const res = await getPurchaseInvoiceList(params)
    if (res.code === 200) {
      tableData.value = res.data.items || res.data.list || []
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取发票列表失败:', error)
    ElMessage.error('获取发票列表失败')
  } finally {
    loading.value = false
  }
}

const fetchSuppliers = async () => {
  try {
    const res = await getSupplierList({ page_size: 1000 })
    if (res.code === 200) {
      suppliers.value = res.data.list || res.data.items || []
    }
  } catch (error) {
    console.error('获取供应商列表失败:', error)
  }
}

const fetchPurchaseOrders = async () => {
  try {
    const res = await getPurchaseList({ page_size: 1000 })
    if (res.code === 200) {
      purchaseOrders.value = res.data.list || res.data.items || []
    }
  } catch (error) {
    console.error('获取采购单列表失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.supplier_id = null
  searchForm.status = null
  searchForm.date_range = null
  handleSearch()
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    invoice_no: '',
    invoice_code: '',
    invoice_type: null,
    purchase_order_id: null,
    supplier_name: '',
    amount: 0,
    tax_rate: 0,
    tax_amount: 0,
    invoice_date: '',
    remark: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  currentInvoice.value = row
  Object.assign(formData, {
    invoice_no: row.invoice_no || '',
    invoice_code: row.invoice_code || '',
    invoice_type: row.invoice_type,
    purchase_order_id: row.purchase_order_id || null,
    supplier_name: row.supplier_name || '',
    amount: row.amount || 0,
    tax_rate: row.tax_rate || 0,
    tax_amount: row.tax_amount || 0,
    invoice_date: row.invoice_date || '',
    remark: row.remark || ''
  })
  dialogVisible.value = true
}

const onPurchaseOrderChange = (orderId) => {
  if (orderId) {
    const order = purchaseOrders.value.find(o => o.id === orderId)
    if (order) {
      formData.supplier_name = order.supplier_name || ''
    }
  } else {
    formData.supplier_name = ''
  }
}

const handleView = async (row) => {
  try {
    const res = await getPurchaseInvoiceDetail(row.id)
    if (res.code === 200) {
      currentInvoice.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('获取发票详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该发票吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deletePurchaseInvoice(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleCertify = (row) => {
  ElMessageBox.confirm('确定要认证该发票吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await certifyPurchaseInvoice(row.id)
      if (res.code === 200) {
        ElMessage.success('认证成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('认证失败')
    }
  }).catch(() => {})
}

const handleDeduct = (row) => {
  ElMessageBox.confirm('确定要抵扣该发票吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deductPurchaseInvoice(row.id)
      if (res.code === 200) {
        ElMessage.success('抵扣成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('抵扣失败')
    }
  }).catch(() => {})
}

const handleBatchCertify = () => {
  const certifiableRows = selectedRows.value.filter(row => row.status === 0)
  if (certifiableRows.length === 0) {
    ElMessage.warning('请选择待认证的发票')
    return
  }
  ElMessageBox.confirm(`确定要批量认证选中的 ${certifiableRows.length} 张发票吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const ids = certifiableRows.map(row => row.id)
      const res = await certifyPurchaseInvoice(ids)
      if (res.code === 200) {
        ElMessage.success('批量认证成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('批量认证失败')
    }
  }).catch(() => {})
}

const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.supplier_id) params.append('supplier_id', searchForm.supplier_id)
  if (searchForm.status !== null && searchForm.status !== '') params.append('invoice_status', searchForm.status)
  if (searchForm.date_range?.[0]) params.append('start_date', searchForm.date_range[0])
  if (searchForm.date_range?.[1]) params.append('end_date', searchForm.date_range[1])
  const token = localStorage.getItem('token') || ''
  window.open(`/api/sales/invoices/export?${params.toString()}&token=${token}`, '_blank')
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const data = { ...formData }
      let res
      if (isEdit.value) {
        res = await updatePurchaseInvoice(currentInvoice.value.id, data)
      } else {
        res = await createPurchaseInvoice(data)
      }
      if (res.code === 200) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      submitLoading.value = false
    }
  })
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  fetchData()
}

const handlePageChange = (val) => {
  pagination.page = val
  fetchData()
}

onMounted(() => {
  fetchData()
  fetchSuppliers()
  fetchPurchaseOrders()
})
</script>

<style lang="scss" scoped>
.invoices-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-form {
    margin-bottom: 20px;
  }

  .toolbar {
    margin-bottom: 15px;
    display: flex;
    gap: 10px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .amount {
    color: #409eff;
    font-weight: bold;
  }

  .total {
    color: #f56c6c;
    font-weight: bold;
    font-size: 14px;
  }
}
</style>
