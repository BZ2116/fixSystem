<template>
  <div class="invoice-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>发票管理</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增发票</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="发票号码/客户/供应商名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="发票类型">
          <el-select v-model="searchForm.invoice_type" placeholder="全部" clearable>
            <el-option label="销售发票" value="sales" />
            <el-option label="采购发票" value="purchase" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="未开" value="pending" />
            <el-option label="已开" value="issued" />
            <el-option label="已作废" value="cancelled" />
            <el-option label="已红冲" value="red_flushed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="invoice_number" label="发票号码" width="160" />
        <el-table-column prop="invoice_type" label="发票类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="invoiceTypeTag(row.invoice_type)" size="small">
              {{ invoiceTypeLabel(row.invoice_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="invoice_date" label="开票日期" width="120" />
        <el-table-column prop="party_name" label="客户/供应商名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="tax_rate" label="税率" width="80" align="center">
          <template #default="{ row }">
            {{ row.tax_rate }}%
          </template>
        </el-table-column>
        <el-table-column prop="tax_amount" label="税额" width="110" align="right">
          <template #default="{ row }">
            ¥{{ row.tax_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="价税合计" width="130" align="right">
          <template #default="{ row }">
            <span class="total-amount">¥{{ row.total_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" :icon="View" @click="handleView(row)">查看</el-button>
            <el-button type="primary" link size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleCancel(row)" :disabled="row.status !== 'issued'">作废</el-button>
            <el-button type="warning" link size="small" @click="handleRedFlush(row)" :disabled="row.status !== 'issued'">红冲</el-button>
            <el-button type="danger" link size="small" :icon="Delete" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="750px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发票类型" prop="invoice_type">
              <el-select v-model="form.invoice_type" placeholder="请选择发票类型" style="width: 100%" @change="handleInvoiceTypeChange">
                <el-option label="销售发票" value="sales" />
                <el-option label="采购发票" value="purchase" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发票号码" prop="invoice_number">
              <el-input v-model="form.invoice_number" placeholder="请输入发票号码" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开票日期" prop="invoice_date">
              <el-date-picker v-model="form.invoice_date" type="date" placeholder="请选择开票日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="form.invoice_type === 'sales' ? '客户' : '供应商'" prop="party_id">
              <el-select v-model="form.party_id" :placeholder="form.invoice_type === 'sales' ? '请选择客户' : '请选择供应商'" filterable style="width: 100%">
                <el-option v-for="item in partyOptions" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">{{ form.invoice_type === 'sales' ? '购方信息' : '销方信息' }}</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="名称" prop="buyer_name">
              <el-input v-model="form.buyer_name" placeholder="请输入名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税号" prop="buyer_tax_number">
              <el-input v-model="form.buyer_tax_number" placeholder="请输入税号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开户行" prop="buyer_bank">
              <el-input v-model="form.buyer_bank" placeholder="请输入开户行" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="银行账号" prop="buyer_bank_account">
              <el-input v-model="form.buyer_bank_account" placeholder="请输入银行账号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="地址电话" prop="buyer_address_phone">
              <el-input v-model="form.buyer_address_phone" placeholder="请输入地址电话" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">{{ form.invoice_type === 'sales' ? '销方信息' : '购方信息' }}</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="名称" prop="seller_name">
              <el-input v-model="form.seller_name" placeholder="请输入名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税号" prop="seller_tax_number">
              <el-input v-model="form.seller_tax_number" placeholder="请输入税号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开户行" prop="seller_bank">
              <el-input v-model="form.seller_bank" placeholder="请输入开户行" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="银行账号" prop="seller_bank_account">
              <el-input v-model="form.seller_bank_account" placeholder="请输入银行账号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="地址电话" prop="seller_address_phone">
              <el-input v-model="form.seller_address_phone" placeholder="请输入地址电话" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">商品/服务明细</el-divider>
        <el-table :data="form.items" border class="items-table">
          <el-table-column label="名称" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.name" placeholder="名称" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="规格" width="100">
            <template #default="{ row }">
              <el-input v-model="row.spec" placeholder="规格" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="80">
            <template #default="{ row }">
              <el-input v-model="row.unit" placeholder="单位" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="80">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="0" :precision="2" :controls="false" size="small" style="width: 100%" @change="calcItemAmount(row)" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.price" :min="0" :precision="2" :controls="false" size="small" style="width: 100%" @change="calcItemAmount(row)" />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="100">
            <template #default="{ row }">
              <span>{{ row.amount?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="税率" width="80">
            <template #default="{ row }">
              <el-input-number v-model="row.tax_rate" :min="0" :max="100" :precision="0" :controls="false" size="small" style="width: 100%" @change="calcItemAmount(row)" />
            </template>
          </el-table-column>
          <el-table-column label="税额" width="90">
            <template #default="{ row }">
              <span>{{ row.tax_amount?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="价税合计" width="100">
            <template #default="{ row }">
              <span>{{ row.total?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" :icon="Delete" @click="removeItem($index)" />
            </template>
          </el-table-column>
        </el-table>
        <el-button type="primary" link :icon="Plus" class="add-item-btn" @click="addItem">添加明细行</el-button>

        <el-divider />
        <el-row :gutter="20" justify="end">
          <el-col :span="8">
            <div class="summary-row">
              <span>合计金额：</span>
              <span class="summary-value">¥{{ summaryAmount.toFixed(2) }}</span>
            </div>
            <div class="summary-row">
              <span>合计税额：</span>
              <span class="summary-value">¥{{ summaryTax.toFixed(2) }}</span>
            </div>
            <div class="summary-row total-row">
              <span>价税合计：</span>
              <span class="summary-value">¥{{ summaryTotal.toFixed(2) }}</span>
            </div>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="发票详情"
      width="850px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="发票号码">{{ detailData.invoice_number }}</el-descriptions-item>
        <el-descriptions-item label="发票类型">
          <el-tag :type="invoiceTypeTag(detailData.invoice_type)" size="small">
            {{ invoiceTypeLabel(detailData.invoice_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开票日期">{{ detailData.invoice_date }}</el-descriptions-item>
        <el-descriptions-item label="客户/供应商">{{ detailData.party_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(detailData.status)" size="small">
            {{ statusLabel(detailData.status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">购方信息</el-divider>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="名称">{{ detailData.buyer_name }}</el-descriptions-item>
        <el-descriptions-item label="税号">{{ detailData.buyer_tax_number }}</el-descriptions-item>
        <el-descriptions-item label="开户行">{{ detailData.buyer_bank }}</el-descriptions-item>
        <el-descriptions-item label="银行账号">{{ detailData.buyer_bank_account }}</el-descriptions-item>
        <el-descriptions-item label="地址电话" :span="2">{{ detailData.buyer_address_phone }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">销方信息</el-divider>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="名称">{{ detailData.seller_name }}</el-descriptions-item>
        <el-descriptions-item label="税号">{{ detailData.seller_tax_number }}</el-descriptions-item>
        <el-descriptions-item label="开户行">{{ detailData.seller_bank }}</el-descriptions-item>
        <el-descriptions-item label="银行账号">{{ detailData.seller_bank_account }}</el-descriptions-item>
        <el-descriptions-item label="地址电话" :span="2">{{ detailData.seller_address_phone }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">商品/服务明细</el-divider>
      <el-table :data="detailData.items || []" border>
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="spec" label="规格" width="100" />
        <el-table-column prop="unit" label="单位" width="80" align="center" />
        <el-table-column prop="quantity" label="数量" width="80" align="right" />
        <el-table-column prop="price" label="单价" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="tax_rate" label="税率" width="80" align="center">
          <template #default="{ row }">
            {{ row.tax_rate }}%
          </template>
        </el-table-column>
        <el-table-column prop="tax_amount" label="税额" width="90" align="right">
          <template #default="{ row }">
            ¥{{ row.tax_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="total" label="价税合计" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.total?.toFixed(2) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="detail-summary">
        <span>合计金额：¥{{ detailData.amount?.toFixed(2) }}</span>
        <span>合计税额：¥{{ detailData.tax_amount?.toFixed(2) }}</span>
        <span class="detail-total">价税合计：¥{{ detailData.total_amount?.toFixed(2) }}</span>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, View, Edit, Delete } from '@element-plus/icons-vue'
import { getInvoiceList, createInvoice, updateInvoice, deleteInvoice, cancelInvoice, redFlushInvoice } from '@/api/invoice'

// ==================== 标签映射 ====================
const invoiceTypeTag = (type) => {
  return type === 'sales' ? 'primary' : 'success'
}

const invoiceTypeLabel = (type) => {
  return type === 'sales' ? '销售发票' : '采购发票'
}

const statusTagType = (status) => {
  const map = { pending: 'info', issued: 'success', cancelled: 'danger', red_flushed: 'warning' }
  return map[status] || 'info'
}

const statusLabel = (status) => {
  const map = { pending: '未开', issued: '已开', cancelled: '已作废', red_flushed: '已红冲' }
  return map[status] || '未知'
}

// ==================== 列表数据 ====================
const loading = ref(false)
const tableData = ref([])
const partyOptions = ref([])

const searchForm = reactive({
  keyword: '',
  invoice_type: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getInvoiceList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      invoice_type: searchForm.invoice_type,
      status: searchForm.status
    })
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取发票列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.invoice_type = ''
  searchForm.status = ''
  handleSearch()
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  fetchData()
}

const handlePageChange = (val) => {
  pagination.page = val
  fetchData()
}

// ==================== 新增/编辑弹窗 ====================
const dialogVisible = ref(false)
const dialogTitle = ref('新增发票')
const formRef = ref()

const getDefaultItem = () => ({
  name: '',
  spec: '',
  unit: '',
  quantity: 0,
  price: 0,
  amount: 0,
  tax_rate: 0,
  tax_amount: 0,
  total: 0
})

const getDefaultForm = () => ({
  id: null,
  invoice_type: 'sales',
  invoice_number: '',
  invoice_date: '',
  party_id: '',
  buyer_name: '',
  buyer_tax_number: '',
  buyer_bank: '',
  buyer_bank_account: '',
  buyer_address_phone: '',
  seller_name: '',
  seller_tax_number: '',
  seller_bank: '',
  seller_bank_account: '',
  seller_address_phone: '',
  items: [{ ...getDefaultItem() }]
})

const form = reactive(getDefaultForm())

const formRules = {
  invoice_type: [{ required: true, message: '请选择发票类型', trigger: 'change' }],
  invoice_number: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  invoice_date: [{ required: true, message: '请选择开票日期', trigger: 'change' }],
  party_id: [{ required: true, message: '请选择关联单据', trigger: 'change' }],
  buyer_name: [{ required: true, message: '请输入购方名称', trigger: 'blur' }],
  seller_name: [{ required: true, message: '请输入销方名称', trigger: 'blur' }]
}

// ==================== 明细行计算 ====================
const calcItemAmount = (row) => {
  row.amount = +(row.quantity * row.price).toFixed(2)
  row.tax_amount = +(row.amount * row.tax_rate / 100).toFixed(2)
  row.total = +(row.amount + row.tax_amount).toFixed(2)
}

const addItem = () => {
  form.items.push({ ...getDefaultItem() })
}

const removeItem = (index) => {
  if (form.items.length <= 1) {
    ElMessage.warning('至少保留一条明细')
    return
  }
  form.items.splice(index, 1)
}

// ==================== 合计 ====================
const summaryAmount = computed(() => {
  return form.items.reduce((sum, item) => sum + (item.amount || 0), 0)
})

const summaryTax = computed(() => {
  return form.items.reduce((sum, item) => sum + (item.tax_amount || 0), 0)
})

const summaryTotal = computed(() => {
  return form.items.reduce((sum, item) => sum + (item.total || 0), 0)
})

// ==================== 发票类型切换 ====================
const handleInvoiceTypeChange = () => {
  // 切换类型时清空关联方选择
  form.party_id = ''
  // TODO: 根据类型加载对应的客户/供应商列表
}

// ==================== 操作 ====================
const handleAdd = () => {
  dialogTitle.value = '新增发票'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑发票'
  Object.assign(form, {
    ...row,
    items: row.items?.length ? row.items.map(item => ({ ...item })) : [{ ...getDefaultItem() }]
  })
  dialogVisible.value = true
}

const handleView = (row) => {
  Object.assign(detailData, row)
  detailVisible.value = true
}

const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm('确定要作废该发票吗？作废后不可恢复。', '提示', { type: 'warning' })
    const res = await cancelInvoice(row.id)
    if (res.code === 200) {
      ElMessage.success('作废成功')
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('作废失败:', error)
    }
  }
}

const handleRedFlush = async (row) => {
  try {
    await ElMessageBox.confirm('确定要红冲该发票吗？', '提示', { type: 'warning' })
    const res = await redFlushInvoice(row.id)
    if (res.code === 200) {
      ElMessage.success('红冲成功')
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('红冲失败:', error)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该发票吗？', '提示', { type: 'warning' })
    const res = await deleteInvoice(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      const submitData = {
        ...form,
        amount: summaryAmount.value,
        tax_amount: summaryTax.value,
        total_amount: summaryTotal.value
      }
      const api = form.id ? updateInvoice : createInvoice
      const res = form.id ? await updateInvoice(form.id, submitData) : await createInvoice(submitData)
      if (res.code === 200) {
        ElMessage.success(dialogTitle.value + '成功')
        dialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      console.error('操作失败:', error)
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(form, getDefaultForm())
}

// ==================== 详情弹窗 ====================
const detailVisible = ref(false)
const detailData = reactive({})

// ==================== 初始化 ====================
onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.invoice-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .total-amount {
    font-weight: bold;
    color: #409eff;
  }

  .items-table {
    margin-bottom: 10px;
  }

  .add-item-btn {
    margin-bottom: 16px;
  }

  .summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    font-size: 14px;

    .summary-value {
      font-weight: 500;
    }

    &.total-row {
      font-size: 16px;
      font-weight: bold;
      color: #409eff;
      padding-top: 8px;
      border-top: 1px solid #ebeef5;
      margin-top: 4px;

      .summary-value {
        font-size: 16px;
      }
    }
  }

  .detail-summary {
    display: flex;
    justify-content: flex-end;
    gap: 30px;
    margin-top: 16px;
    padding: 12px 0;
    font-size: 14px;

    .detail-total {
      font-weight: bold;
      color: #409eff;
      font-size: 16px;
    }
  }
}
</style>
