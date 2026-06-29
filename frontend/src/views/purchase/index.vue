<template>
  <div class="purchase-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>采购管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
            <el-button type="warning" :icon="Upload" @click="handleImport">导入</el-button>
            <el-button type="primary" :icon="Plus" @click="handleAdd">新建采购单</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="采购单号/供应商" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-select v-model="searchForm.supplier_id" placeholder="选择供应商" clearable filterable style="width: 180px">
            <el-option v-for="s in suppliers" :key="s.id" :label="s.supplier_name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="待审核" :value="0" />
            <el-option label="已审核" :value="1" />
            <el-option label="已入库" :value="2" />
            <el-option label="已取消" :value="9" />
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

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="purchase_no" label="采购单号" width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.purchase_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="供应商" min-width="150" />
        <el-table-column prop="purchase_date" label="采购日期" width="120" />
        <el-table-column prop="total_quantity" label="数量" width="80" align="center" />
        <el-table-column prop="total_amount" label="采购金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="paid_amount" label="已付金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.paid_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发票" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.has_invoice === 1" type="success">已收票</el-tag>
            <el-tag v-else type="info">未收票</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">详情</el-button>
            <el-button type="info" link size="small" @click="handlePrint(row)">打印</el-button>
            <el-button type="primary" link size="small" @click="handleEdit(row)" v-if="row.status === 0">编辑</el-button>
            <el-button type="success" link size="small" @click="handleAudit(row)" v-if="row.status === 0">审核</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)" v-if="row.status === 0">删除</el-button>
            <el-button
              v-if="row.status === 1 && row.has_invoice !== 1"
              type="primary"
              link
              size="small"
              @click="handleInvoice(row)"
            >
              收发票
            </el-button>
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

    <!-- 新增/编辑采购单弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑采购单' : '新建采购单'" width="900px" destroy-on-close>
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="供应商" prop="supplier_id">
              <el-select v-model="formData.supplier_id" placeholder="选择供应商" filterable style="width: 100%">
                <el-option v-for="s in suppliers" :key="s.id" :label="s.supplier_name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="发票">
              <el-radio-group v-model="formData.has_invoice">
                <el-radio :label="0">未收发票</el-radio>
                <el-radio :label="1">已收发票</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="采购日期" prop="purchase_date">
              <el-date-picker v-model="formData.purchase_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="备注">
              <el-input v-model="formData.remark" placeholder="备注" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">采购明细</el-divider>

        <div class="items-header">
          <el-button type="primary" size="small" :icon="Plus" @click="addItem">添加商品</el-button>
        </div>

        <el-table :data="formData.items" border size="small" class="items-table">
          <el-table-column type="index" label="序号" width="50" align="center" />
          <el-table-column label="商品" min-width="200">
            <template #default="{ row, $index }">
              <el-select v-model="row.product_id" placeholder="选择商品" filterable @change="(val) => onProductChange(val, $index)" style="width: 100%">
                <el-option v-for="p in products" :key="p.id" :label="p.product_name + ' (库存:' + (p.current_stock || 0) + ')'" :value="p.id">
                  <span style="float: left">{{ p.product_name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">库存: {{ p.current_stock || 0 }}</span>
                </el-option>
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="规格" width="100">
            <template #default="{ row }">
              <span>{{ row.specification || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="单位" width="80">
            <template #default="{ row }">
              <span>{{ row.unit || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="库存" width="80" align="center">
            <template #default="{ row }">
              <span style="color: #67c23a;">{{ row.current_stock || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="120">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.quantity" :min="1" :precision="0" style="width: 100%" @change="calculateItemAmount($index)" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" style="width: 100%" @change="calculateItemAmount($index)" />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.amount?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="amount-summary">
          <el-row :gutter="20">
            <el-col :span="6">
              <span>数量合计: <strong>{{ totalQuantity }}</strong></span>
            </el-col>
            <el-col :span="6">
              <span>金额合计: <strong>¥{{ totalAmount.toFixed(2) }}</strong></span>
            </el-col>
          </el-row>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 采购单详情弹窗 -->
    <el-dialog v-model="detailVisible" title="采购单详情" width="800px" destroy-on-close>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="采购单号">{{ currentOrder.purchase_no }}</el-descriptions-item>
        <el-descriptions-item label="供应商">{{ currentOrder.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentOrder.status)">{{ getStatusText(currentOrder.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="采购日期">{{ currentOrder.purchase_date }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentOrder.operator_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentOrder.created_at }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">采购明细</el-divider>

      <el-table :data="currentOrder.items || []" border size="small">
        <el-table-column type="index" label="序号" width="50" align="center" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column prop="unit_price" label="单价" width="100" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
      </el-table>

      <div class="detail-summary">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="数量合计" :value="currentOrder.total_quantity || 0" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="金额合计" :value="currentOrder.total_amount || 0" :precision="2" prefix="¥" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="已付金额" :value="currentOrder.paid_amount || 0" :precision="2" prefix="¥" />
          </el-col>
        </el-row>
      </div>

      <el-divider content-position="left">备注</el-divider>
      <p>{{ currentOrder.remark || '无' }}</p>
    </el-dialog>

    <!-- 发票录入弹窗 -->
    <el-dialog v-model="invoiceDialogVisible" title="采购收票" width="600px">
      <el-form :model="invoiceForm" label-width="100px">
        <el-form-item label="采购单号">
          <span>{{ invoiceForm.order_no }}</span>
        </el-form-item>
        <el-form-item label="供应商">
          <span>{{ invoiceForm.supplier_name }}</span>
        </el-form-item>
        <el-form-item label="发票号码">
          <el-input v-model="invoiceForm.invoice_no" placeholder="系统自动生成，可留空" />
        </el-form-item>
        <el-form-item label="发票代码">
          <el-input v-model="invoiceForm.invoice_code" />
        </el-form-item>
        <el-form-item label="发票类型">
          <el-radio-group v-model="invoiceForm.invoice_type">
            <el-radio :label="1">普通发票</el-radio>
            <el-radio :label="2">增值税专用发票</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="不含税金额">
          <el-input-number v-model="invoiceForm.amount" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="税率%">
          <el-input-number v-model="invoiceForm.tax_rate" :precision="2" :min="0" :max="100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="税额">
          <el-input-number v-model="invoiceForm.tax_amount" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="价税合计">
          <span style="font-weight: bold; color: #f56c6c;">{{ computedTotalAmount }}</span>
        </el-form-item>
        <el-form-item label="开票日期">
          <el-date-picker v-model="invoiceForm.invoice_date" type="date" placeholder="选择日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="invoiceForm.remark" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="invoiceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitInvoice" :loading="invoiceLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="导入采购单" width="500px">
      <el-upload
        ref="uploadRef"
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".xlsx,.xls,.csv"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx, .xls, .csv 格式文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importLoading">导入</el-button>
      </template>
    </el-dialog>

    <PrintDialog
      v-model:visible="printDialogVisible"
      template-type="purchase"
      :print-data="printData"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Upload, Download } from '@element-plus/icons-vue'
import { getPurchaseList, createPurchase, updatePurchase, deletePurchase, auditPurchase } from '@/api/purchase'
import { getSupplierList } from '@/api/supplier'
import { getProductList } from '@/api/product'
import request from '@/api/request'
import PrintDialog from '@/components/PrintDialog.vue'

const loading = ref(false)
const submitLoading = ref(false)
const importLoading = ref(false)
const tableData = ref([])
const suppliers = ref([])
const products = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const uploadRef = ref(null)
const currentOrder = ref({})
const importFile = ref(null)

// 打印相关
const printDialogVisible = ref(false)
const printData = ref({})

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
  supplier_id: null,
  purchase_date: new Date().toISOString().split('T')[0],
  remark: '',
  items: [],
  has_invoice: 0
})

// 发票相关数据
const invoiceDialogVisible = ref(false)
const invoiceLoading = ref(false)
const invoiceForm = reactive({
  order_id: null,
  order_no: '',
  supplier_name: '',
  invoice_no: '',
  invoice_code: '',
  invoice_type: 1,
  amount: 0,
  tax_rate: 13,
  tax_amount: 0,
  invoice_date: '',
  remark: ''
})

const computedTotalAmount = computed(() => {
  return (invoiceForm.amount + invoiceForm.tax_amount).toFixed(2)
})

const rules = {
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  purchase_date: [{ required: true, message: '请选择采购日期', trigger: 'change' }]
}

const totalQuantity = computed(() => {
  return formData.items.reduce((sum, item) => sum + (item.quantity || 0), 0)
})

const totalAmount = computed(() => {
  return formData.items.reduce((sum, item) => sum + (item.amount || 0), 0)
})

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'success', 2: 'info', 9: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '待审核', 1: '已审核', 2: '已入库', 9: '已取消' }
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
    const res = await getPurchaseList(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取采购单列表失败:', error)
    ElMessage.error('获取采购单列表失败')
  } finally {
    loading.value = false
  }
}

const fetchSuppliers = async () => {
  try {
    const res = await getSupplierList({ page_size: 1000 })
    if (res.code === 200) {
      suppliers.value = res.data.list
    }
  } catch (error) {
    console.error('获取供应商列表失败:', error)
  }
}

const fetchProducts = async () => {
  try {
    const res = await getProductList({ page_size: 1000 })
    if (res.code === 200) {
      products.value = res.data.list
    }
  } catch (error) {
    console.error('获取商品列表失败:', error)
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

const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    supplier_id: null,
    purchase_date: new Date().toISOString().split('T')[0],
    remark: '',
    items: [],
    has_invoice: 0
  })
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  currentOrder.value = row
  try {
    const { getPurchaseDetail } = await import('@/api/purchase')
    const res = await getPurchaseDetail(row.id)
    if (res.code === 200) {
      const order = res.data
      Object.assign(formData, {
        supplier_id: order.supplier_id ? Number(order.supplier_id) : null,
        purchase_date: order.order_date || order.purchase_date,
        remark: order.remark,
        has_invoice: order.has_invoice || 0,
        items: (order.items || []).map(item => {
          const product = products.value.find(p => p.id === Number(item.product_id))
          return {
            ...item,
            product_id: item.product_id ? Number(item.product_id) : null,
            unit: item.unit || item.unit_name || '',
            unit_price: item.price || item.unit_price || 0,
            amount: item.amount || 0,
            current_stock: product ? product.current_stock || 0 : 0
          }
        })
      })
      dialogVisible.value = true
    }
  } catch (error) {
    console.error('获取采购单详情失败:', error)
    ElMessage.error('获取采购单详情失败')
  }
}

const handleView = async (row) => {
  try {
    const { getPurchaseDetail } = await import('@/api/purchase')
    const res = await getPurchaseDetail(row.id)
    if (res.code === 200) {
      currentOrder.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('获取采购单详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

const handlePrint = async (row) => {
  try {
    const res = await request.get(`/purchase/orders/${row.id}`)
    if (res.code === 200) {
      const data = res.data
      let itemsHtml = ''
      if (data.items && data.items.length > 0) {
        itemsHtml = '<table class="print-table"><thead><tr><th>商品</th><th>规格</th><th>单位</th><th>数量</th><th>单价</th><th>金额</th></tr></thead><tbody>' +
          data.items.map(item => `<tr><td>${item.product_name || ''}</td><td>${item.specification || ''}</td><td>${item.unit || ''}</td><td>${item.quantity || 0}</td><td>${(item.price || 0).toFixed(2)}</td><td>${(item.amount || 0).toFixed(2)}</td></tr>`).join('') +
          '</tbody></table>'
      }
      printData.value = {
        order_no: data.order_no || '',
        order_date: data.order_date || '',
        supplier_name: data.supplier_name || '',
        supplier_phone: data.supplier_phone || '',
        supplier_address: data.supplier_address || '',
        total_amount: (data.total_amount || 0).toFixed(2),
        freight_amount: (data.freight_amount || 0).toFixed(2),
        discount_amount: (data.discount_amount || 0).toFixed(2),
        actual_amount: (data.actual_amount || 0).toFixed(2),
        items_detail: itemsHtml,
        remark: data.remark || '',
        status_name: data.status_name || '',
        operator_name: data.operator_name || ''
      }
      printDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取打印数据失败:', error)
    ElMessage.error('获取打印数据失败')
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该采购单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deletePurchase(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleAudit = (row) => {
  ElMessageBox.confirm('确定要审核该采购单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await auditPurchase(row.id)
      if (res.code === 200) {
        ElMessage.success('审核成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('审核失败')
    }
  }).catch(() => {})
}

// 发票相关方法
const handleInvoice = (row) => {
  invoiceForm.order_id = row.id
  invoiceForm.order_no = row.purchase_no
  invoiceForm.supplier_name = row.supplier_name
  invoiceForm.amount = row.total_amount || 0
  invoiceForm.tax_rate = 13
  invoiceForm.tax_amount = parseFloat((invoiceForm.amount * 0.13).toFixed(2))
  invoiceForm.invoice_no = ''
  invoiceForm.invoice_code = ''
  invoiceForm.invoice_type = 1
  invoiceForm.invoice_date = new Date().toISOString().split('T')[0]
  invoiceForm.remark = ''
  invoiceDialogVisible.value = true
}

const submitInvoice = async () => {
  invoiceLoading.value = true
  try {
    await request.post(`/purchase/orders/${invoiceForm.order_id}/invoice`, invoiceForm)
    ElMessage.success('发票录入成功')
    invoiceDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('发票录入失败')
  } finally {
    invoiceLoading.value = false
  }
}

// 监听金额和税率变化自动计算税额
watch([() => invoiceForm.amount, () => invoiceForm.tax_rate], ([amount, rate]) => {
  invoiceForm.tax_amount = parseFloat((amount * rate / 100).toFixed(2))
})

const addItem = () => {
  formData.items.push({
    product_id: null,
    product_name: '',
    specification: '',
    unit: '',
    quantity: 1,
    unit_price: 0,
    amount: 0
  })
}

const removeItem = (index) => {
  formData.items.splice(index, 1)
}

const onProductChange = (productId, index) => {
  const product = products.value.find(p => p.id === productId)
  if (product) {
    formData.items[index].product_name = product.product_name
    formData.items[index].specification = product.specification
    formData.items[index].unit = product.unit_name || '个'
    formData.items[index].unit_price = product.purchase_price || 0
    formData.items[index].current_stock = product.current_stock || 0
    calculateItemAmount(index)
  }
}

const calculateItemAmount = (index) => {
  const item = formData.items[index]
  item.amount = (item.quantity || 0) * (item.unit_price || 0)
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (formData.items.length === 0) {
      ElMessage.warning('请至少添加一个商品')
      return
    }

    submitLoading.value = true
    try {
      const data = {
        ...formData,
        total_quantity: totalQuantity.value,
        total_amount: totalAmount.value,
        has_invoice: formData.has_invoice
      }
      let res
      if (isEdit.value) {
        res = await updatePurchase(currentOrder.value.id, data)
      } else {
        res = await createPurchase(data)
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

const handleImport = () => {
  importDialogVisible.value = true
  importFile.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const handleFileChange = (file) => {
  importFile.value = file.raw
}

const submitImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  importLoading.value = true
  try {
    const { importPurchases } = await import('@/api/purchase')
    const res = await importPurchases(importFile.value)
    if (res.code === 200) {
      ElMessage.success('导入成功')
      importDialogVisible.value = false
      fetchData()
    }
  } catch (error) {
    ElMessage.error('导入失败')
  } finally {
    importLoading.value = false
  }
}

const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.status !== '' && searchForm.status !== null && searchForm.status !== undefined) params.append('status', searchForm.status)
  if (searchForm.date_range && searchForm.date_range[0]) params.append('date_start', searchForm.date_range[0])
  if (searchForm.date_range && searchForm.date_range[1]) params.append('date_end', searchForm.date_range[1])
  const token = localStorage.getItem('token') || ''
  window.open(`/api/purchase/orders/export?${params.toString()}&token=${token}`, '_blank')
}

onMounted(() => {
  fetchData()
  fetchSuppliers()
  fetchProducts()
})
</script>

<style lang="scss" scoped>
.purchase-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .items-header {
    margin-bottom: 10px;
  }

  .items-table {
    margin-bottom: 15px;
  }

  .amount-summary {
    margin-top: 15px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;
    text-align: right;

    strong {
      color: #f56c6c;
      font-size: 16px;
    }
  }

  .detail-summary {
    margin-top: 20px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 4px;
  }
}
</style>
