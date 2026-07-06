<template>
  <div class="invoice-page">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 销售发票 Tab -->
      <el-tab-pane label="销售发票" name="sales">
        <!-- 筛选栏 -->
        <div class="filter-bar">
          <el-form :inline="true" :model="salesQueryForm">
            <el-form-item label="发票号码">
              <el-input v-model="salesQueryForm.invoiceNo" placeholder="请输入发票号码" clearable />
            </el-form-item>
            <el-form-item label="客户名称">
              <el-input v-model="salesQueryForm.customerName" placeholder="请输入客户名称" clearable />
            </el-form-item>
            <el-form-item label="开票日期">
              <el-date-picker
                v-model="salesQueryForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="salesQueryForm.status" placeholder="请选择状态" clearable>
                <el-option label="待开票" value="pending" />
                <el-option label="已开票" value="issued" />
                <el-option label="已作废" value="void" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSalesSearch">查询</el-button>
              <el-button @click="handleSalesReset">重置</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 工具栏 -->
        <div class="toolbar">
          <el-button type="primary" v-permission="'finance-invoice:add'" @click="handleSalesAdd">新增销售发票</el-button>
          <el-button type="danger" :disabled="!salesSelectedIds.length" @click="handleSalesBatchDelete">批量删除</el-button>
        </div>

        <!-- 销售发票表格 -->
        <el-table
          v-loading="salesLoading"
          :data="salesInvoiceList"
          @selection-change="handleSalesSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="invoiceNo" label="发票号码" min-width="120" />
          <el-table-column prop="invoiceType" label="发票类型" min-width="100">
            <template #default="{ row }">
              <el-tag v-if="row.invoiceType === 'special'" type="danger">专用发票</el-tag>
              <el-tag v-else-if="row.invoiceType === 'normal'" type="primary">普通发票</el-tag>
              <el-tag v-else-if="row.invoiceType === 'electronic'" type="success">电子发票</el-tag>
              <el-tag v-else>{{ row.invoiceType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="salesOrderNo" label="关联销售单号" min-width="140" />
          <el-table-column prop="customerName" label="客户名称" min-width="150" show-overflow-tooltip />
          <el-table-column prop="amount" label="金额" min-width="120">
            <template #default="{ row }">
              <span class="amount">{{ formatMoney(row.amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="taxRate" label="税率" min-width="80">
            <template #default="{ row }">
              {{ row.taxRate }}%
            </template>
          </el-table-column>
          <el-table-column prop="taxAmount" label="税额" min-width="120">
            <template #default="{ row }">
              {{ formatMoney(row.taxAmount) }}
            </template>
          </el-table-column>
          <el-table-column prop="totalAmount" label="合计" min-width="120">
            <template #default="{ row }">
              <span class="total">{{ formatMoney(row.totalAmount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="invoiceDate" label="开票日期" min-width="120" />
          <el-table-column prop="status" label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'pending'" type="warning">待开票</el-tag>
              <el-tag v-else-if="row.status === 'issued'" type="success">已开票</el-tag>
              <el-tag v-else-if="row.status === 'void'" type="info">已作废</el-tag>
              <el-tag v-else>{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" min-width="220">
            <template #default="{ row }">
              <el-button type="success" link @click="handleSalesPrint(row)">打印</el-button>
              <el-button type="primary" link v-permission="'finance-invoice:edit'" @click="handleSalesEdit(row)">编辑</el-button>
              <el-button type="danger" link @click="handleSalesDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination">
          <el-pagination
            v-model:current-page="salesPagination.page"
            v-model:page-size="salesPagination.pageSize"
            :total="salesPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSalesSizeChange"
            @current-change="handleSalesPageChange"
          />
        </div>
      </el-tab-pane>

      <!-- 采购发票 Tab -->
      <el-tab-pane label="采购发票" name="purchase">
        <!-- 筛选栏 -->
        <div class="filter-bar">
          <el-form :inline="true" :model="purchaseQueryForm">
            <el-form-item label="发票号码">
              <el-input v-model="purchaseQueryForm.invoiceNo" placeholder="请输入发票号码" clearable />
            </el-form-item>
            <el-form-item label="发票代码">
              <el-input v-model="purchaseQueryForm.invoiceCode" placeholder="请输入发票代码" clearable />
            </el-form-item>
            <el-form-item label="供应商名称">
              <el-input v-model="purchaseQueryForm.supplierName" placeholder="请输入供应商名称" clearable />
            </el-form-item>
            <el-form-item label="开票日期">
              <el-date-picker
                v-model="purchaseQueryForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="purchaseQueryForm.status" placeholder="请选择状态" clearable>
                <el-option label="待认证" value="pending" />
                <el-option label="已认证" value="certified" />
                <el-option label="已抵扣" value="deducted" />
                <el-option label="已作废" value="void" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handlePurchaseSearch">查询</el-button>
              <el-button @click="handlePurchaseReset">重置</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 工具栏 -->
        <div class="toolbar">
          <el-button type="primary" v-permission="'finance-invoice:add'" @click="handlePurchaseAdd">新增采购发票</el-button>
          <el-button type="success" :disabled="!purchaseSelectedIds.length" @click="handlePurchaseBatchCertify">批量认证</el-button>
          <el-button type="warning" :disabled="!purchaseSelectedIds.length" @click="handlePurchaseBatchDeduct">批量抵扣</el-button>
          <el-button type="danger" :disabled="!purchaseSelectedIds.length" @click="handlePurchaseBatchDelete">批量删除</el-button>
        </div>

        <!-- 采购发票表格 -->
        <el-table
          v-loading="purchaseLoading"
          :data="purchaseInvoiceList"
          @selection-change="handlePurchaseSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="invoiceNo" label="发票号码" min-width="120" />
          <el-table-column prop="invoiceCode" label="发票代码" min-width="120" />
          <el-table-column prop="invoiceType" label="发票类型" min-width="100">
            <template #default="{ row }">
              <el-tag v-if="row.invoiceType === 'special'" type="danger">专用发票</el-tag>
              <el-tag v-else-if="row.invoiceType === 'normal'" type="primary">普通发票</el-tag>
              <el-tag v-else-if="row.invoiceType === 'electronic'" type="success">电子发票</el-tag>
              <el-tag v-else>{{ row.invoiceType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="purchaseOrderNo" label="关联采购单号" min-width="140" />
          <el-table-column prop="supplierName" label="供应商名称" min-width="150" show-overflow-tooltip />
          <el-table-column prop="amountWithoutTax" label="不含税金额" min-width="120">
            <template #default="{ row }">
              <span class="amount">{{ formatMoney(row.amountWithoutTax) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="taxRate" label="税率" min-width="80">
            <template #default="{ row }">
              {{ row.taxRate }}%
            </template>
          </el-table-column>
          <el-table-column prop="taxAmount" label="税额" min-width="120">
            <template #default="{ row }">
              {{ formatMoney(row.taxAmount) }}
            </template>
          </el-table-column>
          <el-table-column prop="totalAmount" label="价税合计" min-width="120">
            <template #default="{ row }">
              <span class="total">{{ formatMoney(row.totalAmount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="invoiceDate" label="开票日期" min-width="120" />
          <el-table-column prop="status" label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'pending'" type="warning">待认证</el-tag>
              <el-tag v-else-if="row.status === 'certified'" type="primary">已认证</el-tag>
              <el-tag v-else-if="row.status === 'deducted'" type="success">已抵扣</el-tag>
              <el-tag v-else-if="row.status === 'void'" type="info">已作废</el-tag>
              <el-tag v-else>{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" min-width="280">
            <template #default="{ row }">
              <el-button type="success" link @click="handlePurchasePrint(row)">打印</el-button>
              <el-button type="primary" link v-permission="'finance-invoice:edit'" @click="handlePurchaseEdit(row)">编辑</el-button>
              <el-button 
                v-if="row.status === 'pending'" 
                type="success" 
                link 
                @click="handlePurchaseCertify(row)"
              >
                认证
              </el-button>
              <el-button 
                v-if="row.status === 'certified'" 
                type="warning" 
                link 
                @click="handlePurchaseDeduct(row)"
              >
                抵扣
              </el-button>
              <el-button type="danger" link @click="handlePurchaseDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination">
          <el-pagination
            v-model:current-page="purchasePagination.page"
            v-model:page-size="purchasePagination.pageSize"
            :total="purchasePagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePurchaseSizeChange"
            @current-change="handlePurchasePageChange"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 销售发票表单对话框 -->
    <el-dialog
      v-model="salesDialogVisible"
      :title="salesForm.id ? '编辑销售发票' : '新增销售发票'"
      width="700px"
    >
      <el-form ref="salesFormRef" :model="salesForm" :rules="salesFormRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发票号码" prop="invoiceNo">
              <el-input v-model="salesForm.invoiceNo" placeholder="请输入发票号码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发票类型" prop="invoiceType">
              <el-select v-model="salesForm.invoiceType" placeholder="请选择发票类型" style="width: 100%">
                <el-option label="专用发票" value="special" />
                <el-option label="普通发票" value="normal" />
                <el-option label="电子发票" value="electronic" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关联销售单号" prop="salesOrderNo">
              <el-input v-model="salesForm.salesOrderNo" placeholder="请输入关联销售单号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户名称" prop="customerName">
              <el-input v-model="salesForm.customerName" placeholder="请输入客户名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="金额" prop="amount">
              <el-input-number v-model="salesForm.amount" :precision="2" :min="0" style="width: 100%" @change="calculateSalesTotal" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率" prop="taxRate">
              <el-input-number v-model="salesForm.taxRate" :precision="2" :min="0" :max="100" style="width: 100%" @change="calculateSalesTotal">
                <template #append>%</template>
              </el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="税额" prop="taxAmount">
              <el-input-number v-model="salesForm.taxAmount" :precision="2" :min="0" style="width: 100%" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合计" prop="totalAmount">
              <el-input-number v-model="salesForm.totalAmount" :precision="2" :min="0" style="width: 100%" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开票日期" prop="invoiceDate">
              <el-date-picker v-model="salesForm.invoiceDate" type="date" placeholder="选择开票日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="salesForm.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="待开票" value="pending" />
                <el-option label="已开票" value="issued" />
                <el-option label="已作废" value="void" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="salesDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSalesSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 采购发票表单对话框 -->
    <el-dialog
      v-model="purchaseDialogVisible"
      :title="purchaseForm.id ? '编辑采购发票' : '新增采购发票'"
      width="700px"
    >
      <el-form ref="purchaseFormRef" :model="purchaseForm" :rules="purchaseFormRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发票号码" prop="invoiceNo">
              <el-input v-model="purchaseForm.invoiceNo" placeholder="请输入发票号码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发票代码" prop="invoiceCode">
              <el-input v-model="purchaseForm.invoiceCode" placeholder="请输入发票代码" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发票类型" prop="invoiceType">
              <el-select v-model="purchaseForm.invoiceType" placeholder="请选择发票类型" style="width: 100%">
                <el-option label="专用发票" value="special" />
                <el-option label="普通发票" value="normal" />
                <el-option label="电子发票" value="electronic" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联采购单号" prop="purchaseOrderNo">
              <el-input v-model="purchaseForm.purchaseOrderNo" placeholder="请输入关联采购单号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="供应商名称" prop="supplierName">
              <el-input v-model="purchaseForm.supplierName" placeholder="请输入供应商名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开票日期" prop="invoiceDate">
              <el-date-picker v-model="purchaseForm.invoiceDate" type="date" placeholder="选择开票日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="不含税金额" prop="amountWithoutTax">
              <el-input-number v-model="purchaseForm.amountWithoutTax" :precision="2" :min="0" style="width: 100%" @change="calculatePurchaseTotal" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率" prop="taxRate">
              <el-input-number v-model="purchaseForm.taxRate" :precision="2" :min="0" :max="100" style="width: 100%" @change="calculatePurchaseTotal">
                <template #append>%</template>
              </el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="税额" prop="taxAmount">
              <el-input-number v-model="purchaseForm.taxAmount" :precision="2" :min="0" style="width: 100%" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="价税合计" prop="totalAmount">
              <el-input-number v-model="purchaseForm.totalAmount" :precision="2" :min="0" style="width: 100%" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="purchaseForm.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="待认证" value="pending" />
                <el-option label="已认证" value="certified" />
                <el-option label="已抵扣" value="deducted" />
                <el-option label="已作废" value="void" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="purchaseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePurchaseSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 销售发票打印对话框 -->
    <PrintDialog v-model:visible="salesPrintDialogVisible" template-type="sales_invoice" :print-data="salesPrintData" />

    <!-- 采购发票打印对话框 -->
    <PrintDialog v-model:visible="purchasePrintDialogVisible" template-type="purchase_invoice" :print-data="purchasePrintData" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PrintDialog from '@/components/PrintDialog.vue'
import { 
  getInvoiceList as getSalesInvoiceList, 
  saveInvoice as createSalesInvoice, 
  updateInvoiceStatus as updateSalesInvoice, 
  exportInvoices as deleteSalesInvoice 
} from '@/api/sales'
import { 
  getPurchaseInvoiceList, createPurchaseInvoice, updatePurchaseInvoice, 
  deletePurchaseInvoice, certifyPurchaseInvoice, deductPurchaseInvoice 
} from '@/api/finance'

// ==================== 通用 ====================
const activeTab = ref('sales')

// 金额格式化
const formatMoney = (value) => {
  if (!value && value !== 0) return '-'
  return '¥' + Number(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// ==================== 销售发票 ====================
const salesLoading = ref(false)
const salesInvoiceList = ref([])
const salesSelectedIds = ref([])
const salesPrintDialogVisible = ref(false)
const salesPrintData = ref({})

const salesQueryForm = reactive({
  invoiceNo: '',
  customerName: '',
  dateRange: [],
  status: ''
})

const salesPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const salesDialogVisible = ref(false)
const salesFormRef = ref(null)
const salesForm = reactive({
  id: null,
  invoiceNo: '',
  invoiceType: '',
  salesOrderNo: '',
  customerName: '',
  amount: 0,
  taxRate: 13,
  taxAmount: 0,
  totalAmount: 0,
  invoiceDate: '',
  status: 'pending'
})

const salesFormRules = {
  invoiceNo: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  invoiceType: [{ required: true, message: '请选择发票类型', trigger: 'change' }],
  customerName: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  taxRate: [{ required: true, message: '请输入税率', trigger: 'blur' }],
  invoiceDate: [{ required: true, message: '请选择开票日期', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

// 计算销售发票税额和合计
const calculateSalesTotal = () => {
  const amount = Number(salesForm.amount) || 0
  const taxRate = Number(salesForm.taxRate) || 0
  salesForm.taxAmount = Number((amount * taxRate / 100).toFixed(2))
  salesForm.totalAmount = Number((amount + salesForm.taxAmount).toFixed(2))
}

// 获取销售发票列表
const fetchSalesInvoiceList = async () => {
  salesLoading.value = true
  try {
    const params = {
      page: salesPagination.page,
      pageSize: salesPagination.pageSize,
      invoiceNo: salesQueryForm.invoiceNo,
      customerName: salesQueryForm.customerName,
      status: salesQueryForm.status,
      startDate: salesQueryForm.dateRange?.[0],
      endDate: salesQueryForm.dateRange?.[1]
    }
    const res = await getSalesInvoiceList(params)
    salesInvoiceList.value = res.data?.list || []
    salesPagination.total = res.data?.total || 0
  } catch (error) {
    ElMessage.error('获取销售发票列表失败')
  } finally {
    salesLoading.value = false
  }
}

// 销售发票搜索
const handleSalesSearch = () => {
  salesPagination.page = 1
  fetchSalesInvoiceList()
}

// 销售发票重置
const handleSalesReset = () => {
  salesQueryForm.invoiceNo = ''
  salesQueryForm.customerName = ''
  salesQueryForm.dateRange = []
  salesQueryForm.status = ''
  handleSalesSearch()
}

// 销售发票选择变化
const handleSalesSelectionChange = (selection) => {
  salesSelectedIds.value = selection.map(item => item.id)
}

// 销售发票分页
const handleSalesSizeChange = (size) => {
  salesPagination.pageSize = size
  fetchSalesInvoiceList()
}

const handleSalesPageChange = (page) => {
  salesPagination.page = page
  fetchSalesInvoiceList()
}

// 新增销售发票
const handleSalesAdd = () => {
  salesForm.id = null
  salesForm.invoiceNo = ''
  salesForm.invoiceType = ''
  salesForm.salesOrderNo = ''
  salesForm.customerName = ''
  salesForm.amount = 0
  salesForm.taxRate = 13
  salesForm.taxAmount = 0
  salesForm.totalAmount = 0
  salesForm.invoiceDate = ''
  salesForm.status = 'pending'
  salesDialogVisible.value = true
}

// 编辑销售发票
const handleSalesEdit = (row) => {
  Object.assign(salesForm, row)
  salesDialogVisible.value = true
}

// 删除销售发票
const handleSalesDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该销售发票吗？', '提示', { type: 'warning' })
    await deleteSalesInvoice(row.id)
    ElMessage.success('删除成功')
    fetchSalesInvoiceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除销售发票
const handleSalesBatchDelete = async () => {
  if (!salesSelectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${salesSelectedIds.value.length} 条销售发票吗？`, '提示', { type: 'warning' })
    await Promise.all(salesSelectedIds.value.map(id => deleteSalesInvoice(id)))
    ElMessage.success('批量删除成功')
    fetchSalesInvoiceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 提交销售发票表单
const handleSalesSubmit = async () => {
  const valid = await salesFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  try {
    if (salesForm.id) {
      await updateSalesInvoice(salesForm.id, salesForm)
      ElMessage.success('更新成功')
    } else {
      await createSalesInvoice(salesForm)
      ElMessage.success('创建成功')
    }
    salesDialogVisible.value = false
    fetchSalesInvoiceList()
  } catch (error) {
    ElMessage.error(salesForm.id ? '更新失败' : '创建失败')
  }
}

// ==================== 采购发票 ====================
const purchaseLoading = ref(false)
const purchaseInvoiceList = ref([])
const purchaseSelectedIds = ref([])
const purchasePrintDialogVisible = ref(false)
const purchasePrintData = ref({})

const purchaseQueryForm = reactive({
  invoiceNo: '',
  invoiceCode: '',
  supplierName: '',
  dateRange: [],
  status: ''
})

const purchasePagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const purchaseDialogVisible = ref(false)
const purchaseFormRef = ref(null)
const purchaseForm = reactive({
  id: null,
  invoiceNo: '',
  invoiceCode: '',
  invoiceType: '',
  purchaseOrderNo: '',
  supplierName: '',
  amountWithoutTax: 0,
  taxRate: 13,
  taxAmount: 0,
  totalAmount: 0,
  invoiceDate: '',
  status: 'pending'
})

const purchaseFormRules = {
  invoiceNo: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  invoiceCode: [{ required: true, message: '请输入发票代码', trigger: 'blur' }],
  invoiceType: [{ required: true, message: '请选择发票类型', trigger: 'change' }],
  supplierName: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
  amountWithoutTax: [{ required: true, message: '请输入不含税金额', trigger: 'blur' }],
  taxRate: [{ required: true, message: '请输入税率', trigger: 'blur' }],
  invoiceDate: [{ required: true, message: '请选择开票日期', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

// 计算采购发票税额和合计
const calculatePurchaseTotal = () => {
  const amount = Number(purchaseForm.amountWithoutTax) || 0
  const taxRate = Number(purchaseForm.taxRate) || 0
  purchaseForm.taxAmount = Number((amount * taxRate / 100).toFixed(2))
  purchaseForm.totalAmount = Number((amount + purchaseForm.taxAmount).toFixed(2))
}

// 获取采购发票列表
const fetchPurchaseInvoiceList = async () => {
  purchaseLoading.value = true
  try {
    const params = {
      page: purchasePagination.page,
      pageSize: purchasePagination.pageSize,
      invoiceNo: purchaseQueryForm.invoiceNo,
      invoiceCode: purchaseQueryForm.invoiceCode,
      supplierName: purchaseQueryForm.supplierName,
      status: purchaseQueryForm.status,
      startDate: purchaseQueryForm.dateRange?.[0],
      endDate: purchaseQueryForm.dateRange?.[1]
    }
    const res = await getPurchaseInvoiceList(params)
    purchaseInvoiceList.value = res.data?.list || []
    purchasePagination.total = res.data?.total || 0
  } catch (error) {
    ElMessage.error('获取采购发票列表失败')
  } finally {
    purchaseLoading.value = false
  }
}

// 采购发票搜索
const handlePurchaseSearch = () => {
  purchasePagination.page = 1
  fetchPurchaseInvoiceList()
}

// 采购发票重置
const handlePurchaseReset = () => {
  purchaseQueryForm.invoiceNo = ''
  purchaseQueryForm.invoiceCode = ''
  purchaseQueryForm.supplierName = ''
  purchaseQueryForm.dateRange = []
  purchaseQueryForm.status = ''
  handlePurchaseSearch()
}

// 采购发票选择变化
const handlePurchaseSelectionChange = (selection) => {
  purchaseSelectedIds.value = selection.map(item => item.id)
}

// 采购发票分页
const handlePurchaseSizeChange = (size) => {
  purchasePagination.pageSize = size
  fetchPurchaseInvoiceList()
}

const handlePurchasePageChange = (page) => {
  purchasePagination.page = page
  fetchPurchaseInvoiceList()
}

// 新增采购发票
const handlePurchaseAdd = () => {
  purchaseForm.id = null
  purchaseForm.invoiceNo = ''
  purchaseForm.invoiceCode = ''
  purchaseForm.invoiceType = ''
  purchaseForm.purchaseOrderNo = ''
  purchaseForm.supplierName = ''
  purchaseForm.amountWithoutTax = 0
  purchaseForm.taxRate = 13
  purchaseForm.taxAmount = 0
  purchaseForm.totalAmount = 0
  purchaseForm.invoiceDate = ''
  purchaseForm.status = 'pending'
  purchaseDialogVisible.value = true
}

// 编辑采购发票
const handlePurchaseEdit = (row) => {
  Object.assign(purchaseForm, row)
  purchaseDialogVisible.value = true
}

// 删除采购发票
const handlePurchaseDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该采购发票吗？', '提示', { type: 'warning' })
    await deletePurchaseInvoice(row.id)
    ElMessage.success('删除成功')
    fetchPurchaseInvoiceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除采购发票
const handlePurchaseBatchDelete = async () => {
  if (!purchaseSelectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${purchaseSelectedIds.value.length} 条采购发票吗？`, '提示', { type: 'warning' })
    await Promise.all(purchaseSelectedIds.value.map(id => deletePurchaseInvoice(id)))
    ElMessage.success('批量删除成功')
    fetchPurchaseInvoiceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 认证采购发票
const handlePurchaseCertify = async (row) => {
  try {
    await ElMessageBox.confirm('确定要认证该采购发票吗？', '提示', { type: 'info' })
    await certifyPurchaseInvoice(row.id)
    ElMessage.success('认证成功')
    fetchPurchaseInvoiceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('认证失败')
    }
  }
}

// 批量认证采购发票
const handlePurchaseBatchCertify = async () => {
  if (!purchaseSelectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定要认证选中的 ${purchaseSelectedIds.value.length} 条采购发票吗？`, '提示', { type: 'info' })
    await Promise.all(purchaseSelectedIds.value.map(id => certifyPurchaseInvoice(id)))
    ElMessage.success('批量认证成功')
    fetchPurchaseInvoiceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量认证失败')
    }
  }
}

// 抵扣采购发票
const handlePurchaseDeduct = async (row) => {
  try {
    await ElMessageBox.confirm('确定要抵扣该采购发票吗？', '提示', { type: 'info' })
    await deductPurchaseInvoice(row.id)
    ElMessage.success('抵扣成功')
    fetchPurchaseInvoiceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('抵扣失败')
    }
  }
}

// 批量抵扣采购发票
const handlePurchaseBatchDeduct = async () => {
  if (!purchaseSelectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定要抵扣选中的 ${purchaseSelectedIds.value.length} 条采购发票吗？`, '提示', { type: 'info' })
    await Promise.all(purchaseSelectedIds.value.map(id => deductPurchaseInvoice(id)))
    ElMessage.success('批量抵扣成功')
    fetchPurchaseInvoiceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量抵扣失败')
    }
  }
}

// 提交采购发票表单
const handlePurchaseSubmit = async () => {
  const valid = await purchaseFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  try {
    if (purchaseForm.id) {
      await updatePurchaseInvoice(purchaseForm.id, purchaseForm)
      ElMessage.success('更新成功')
    } else {
      await createPurchaseInvoice(purchaseForm)
      ElMessage.success('创建成功')
    }
    purchaseDialogVisible.value = false
    fetchPurchaseInvoiceList()
  } catch (error) {
    ElMessage.error(purchaseForm.id ? '更新失败' : '创建失败')
  }
}

// ==================== 打印功能 ====================
// 销售发票打印
const handleSalesPrint = (row) => {
  const invoiceTypeMap = {
    special: '专用发票',
    normal: '普通发票',
    electronic: '电子发票'
  }
  const statusMap = {
    pending: '待开票',
    issued: '已开票',
    void: '已作废'
  }
  salesPrintData.value = {
    invoiceNo: row.invoiceNo || '',
    invoiceType: invoiceTypeMap[row.invoiceType] || row.invoiceType || '',
    status: statusMap[row.status] || row.status || '',
    customerName: row.customerName || '',
    taxNo: row.taxNo || '-',
    salesOrderNo: row.salesOrderNo || '-',
    invoiceDate: row.invoiceDate || '',
    amount: Number(row.amount || 0).toFixed(2),
    taxRate: row.taxRate || 0,
    taxAmount: Number(row.taxAmount || 0).toFixed(2),
    totalAmount: Number(row.totalAmount || 0).toFixed(2),
    remark: row.remark || '-'
  }
  salesPrintDialogVisible.value = true
}

// 采购发票打印
const handlePurchasePrint = (row) => {
  const invoiceTypeMap = {
    special: '专用发票',
    normal: '普通发票',
    electronic: '电子发票'
  }
  const statusMap = {
    pending: '待认证',
    certified: '已认证',
    deducted: '已抵扣',
    void: '已作废'
  }
  purchasePrintData.value = {
    invoiceNo: row.invoiceNo || '',
    invoiceCode: row.invoiceCode || '-',
    invoiceType: invoiceTypeMap[row.invoiceType] || row.invoiceType || '',
    status: statusMap[row.status] || row.status || '',
    supplierName: row.supplierName || '',
    taxNo: row.taxNo || '-',
    purchaseOrderNo: row.purchaseOrderNo || '-',
    invoiceDate: row.invoiceDate || '',
    amount: Number(row.amount || 0).toFixed(2),
    taxRate: row.taxRate || 0,
    taxAmount: Number(row.taxAmount || 0).toFixed(2),
    totalAmount: Number(row.totalAmount || 0).toFixed(2),
    certifiedDate: row.certifiedDate || '-',
    deductedDate: row.deductedDate || '-',
    remark: row.remark || '-'
  }
  purchasePrintDialogVisible.value = true
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchSalesInvoiceList()
  fetchPurchaseInvoiceList()
})
</script>

<style scoped lang="scss">
.invoice-page {
  .filter-bar {
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
  }
}
</style>
