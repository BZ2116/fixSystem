<template>
  <div class="expense-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">收入总额</div>
              <div class="stat-value">{{ formatMoney(statistics.income_total) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon><Wallet /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">支出总额</div>
              <div class="stat-value">{{ formatMoney(statistics.expense_total) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">净额</div>
              <div class="stat-value">{{ formatMoney(statistics.net_amount) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c;">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">待确认数</div>
              <div class="stat-value">{{ statistics.pending_count || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索栏 -->
    <el-form :model="searchForm" inline class="search-form">
      <el-form-item label="关键词">
        <el-input v-model="searchForm.keyword" placeholder="费用名称/单号" clearable />
      </el-form-item>
      <el-form-item label="费用类型">
        <el-select v-model="searchForm.expense_type" placeholder="全部" clearable>
          <el-option label="日常费用" :value="1" />
          <el-option label="其他收入" :value="2" />
          <el-option label="运营支出" :value="3" />
          <el-option label="管理费用" :value="4" />
        </el-select>
      </el-form-item>
      <el-form-item label="收支类型">
        <el-select v-model="searchForm.record_type" placeholder="全部" clearable>
          <el-option label="收入" :value="1" />
          <el-option label="支出" :value="2" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="searchForm.status" placeholder="全部" clearable>
          <el-option label="待处理" :value="0" />
          <el-option label="已确认" :value="1" />
          <el-option label="已取消" :value="2" />
        </el-select>
      </el-form-item>
      <el-form-item label="日期范围">
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
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <el-button @click="handleReset">
          <el-icon><RefreshRight /></el-icon>重置
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 操作按钮 -->
    <div class="toolbar">
      <el-button type="primary" v-permission="'finance-expense:add'" @click="handleAdd">
        <el-icon><Plus /></el-icon>新增费用
      </el-button>
      <el-button type="success" :disabled="selectedRows.length === 0" @click="handleBatchConfirm">
        <el-icon><Check /></el-icon>批量确认
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="tableData"
      @selection-change="handleSelectionChange"
      border
    >
      <el-table-column type="selection" width="55" :selectable="isSelectable" />
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column prop="expense_no" label="费用单号" width="140" />
      <el-table-column prop="expense_name" label="费用名称" min-width="150" />
      <el-table-column prop="expense_type" label="费用类型" width="100">
        <template #default="{ row }">
          {{ getExpenseTypeText(row.expense_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="record_type" label="收支类型" width="90">
        <template #default="{ row }">
          <span :class="row.record_type === 1 ? 'income' : 'expense'">
            {{ row.record_type === 1 ? '收入' : '支出' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="amount" label="金额" width="120">
        <template #default="{ row }">
          <strong>{{ formatMoney(row.amount) }}</strong>
        </template>
      </el-table-column>
      <el-table-column prop="partner_name" label="往来单位" min-width="150" />
      <el-table-column prop="expense_date" label="费用日期" width="120" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="account_name" label="账户" min-width="120">
        <template #default="{ row }">
          {{ row.status === 1 ? row.account_name : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 0" type="primary" link v-permission="'finance-expense:edit'" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button v-if="row.status === 0" type="success" link @click="handleConfirm(row)">
            确认
          </el-button>
          <el-button type="danger" link @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.page_size"
      :total="pagination.total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      class="pagination"
      @size-change="handleSizeChange"
      @current-change="handlePageChange"
    />

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增费用' : '编辑费用'"
      width="600px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="费用名称" prop="expense_name">
          <el-input v-model="form.expense_name" placeholder="请输入费用名称" />
        </el-form-item>
        <el-form-item label="费用类型" prop="expense_type">
          <el-select v-model="form.expense_type" placeholder="请选择费用类型" style="width: 100%;">
            <el-option label="日常费用" :value="1" />
            <el-option label="其他收入" :value="2" />
            <el-option label="运营支出" :value="3" />
            <el-option label="管理费用" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="收支类型" prop="record_type">
          <el-radio-group v-model="form.record_type">
            <el-radio :label="1">收入</el-radio>
            <el-radio :label="2">支出</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="往来类型" prop="partner_type">
          <el-select v-model="form.partner_type" placeholder="请选择往来类型" style="width: 100%;" @change="handlePartnerTypeChange">
            <el-option label="客户" value="customer" />
            <el-option label="供应商" value="supplier" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="往来单位" prop="partner_id">
          <el-select
            v-model="form.partner_id"
            placeholder="请选择往来单位"
            style="width: 100%;"
            :disabled="form.partner_type === 'other'"
          >
            <el-option
              v-for="item in partnerList"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="费用日期" prop="expense_date">
          <el-date-picker
            v-model="form.expense_date"
            type="date"
            placeholder="请选择费用日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
        <el-form-item label="附件">
          <el-upload
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            multiple
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">支持上传jpg/png/pdf等格式文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 确认对话框 -->
    <el-dialog
      v-model="confirmDialogVisible"
      title="确认费用"
      width="500px"
    >
      <el-form ref="confirmFormRef" :model="confirmForm" :rules="confirmRules" label-width="100px">
        <el-form-item label="费用名称">
          <span>{{ confirmForm.expense_name }}</span>
        </el-form-item>
        <el-form-item label="金额">
          <span :class="confirmForm.record_type === 1 ? 'income' : 'expense'">
            {{ confirmForm.record_type === 1 ? '收入' : '支出' }} {{ formatMoney(confirmForm.amount) }}
          </span>
        </el-form-item>
        <el-form-item label="收支账户" prop="account_id">
          <el-select v-model="confirmForm.account_id" placeholder="请选择收支账户" style="width: 100%;">
            <el-option
              v-for="item in accountList"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="confirmForm.remark" type="textarea" :rows="2" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="confirmDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Money, Wallet, TrendCharts, Warning, Search, RefreshRight,
  Plus, Check, Upload
} from '@element-plus/icons-vue'
import {
  getExpenseList, getExpenseDetail, createExpense, updateExpense,
  deleteExpense, confirmExpense, getExpenseStatistics
} from '@/api/expense'
import { getAccountList } from '@/api/finance'
import { getCustomerList } from '@/api/customer'
import { getSupplierList } from '@/api/supplier'

// 搜索表单
const searchForm = reactive({
  keyword: '',
  expense_type: null,
  record_type: null,
  status: null,
  date_range: []
})

// 统计数据
const statistics = reactive({
  income_total: 0,
  expense_total: 0,
  net_amount: 0,
  pending_count: 0
})

// 表格数据
const loading = ref(false)
const tableData = ref([])
const selectedRows = ref([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const dialogType = ref('add')
const formRef = ref(null)
const form = reactive({
  id: null,
  expense_name: '',
  expense_type: null,
  record_type: 2,
  amount: 0,
  partner_type: 'other',
  partner_id: null,
  expense_date: '',
  remark: '',
  attachments: []
})

const rules = {
  expense_name: [{ required: true, message: '请输入费用名称', trigger: 'blur' }],
  expense_type: [{ required: true, message: '请选择费用类型', trigger: 'change' }],
  record_type: [{ required: true, message: '请选择收支类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  partner_type: [{ required: true, message: '请选择往来类型', trigger: 'change' }],
  expense_date: [{ required: true, message: '请选择费用日期', trigger: 'change' }]
}

// 往来单位列表
const partnerList = ref([])
const fileList = ref([])

// 确认对话框
const confirmDialogVisible = ref(false)
const confirmFormRef = ref(null)
const confirmForm = reactive({
  id: null,
  expense_name: '',
  amount: 0,
  record_type: 2,
  account_id: null,
  remark: ''
})

const confirmRules = {
  account_id: [{ required: true, message: '请选择收支账户', trigger: 'change' }]
}

// 账户列表
const accountList = ref([])

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const res = await getExpenseStatistics()
    if (res.code === 200) {
      Object.assign(statistics, res.data)
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取列表数据
const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword,
      expense_type: searchForm.expense_type,
      record_type: searchForm.record_type,
      status: searchForm.status,
      start_date: searchForm.date_range?.[0],
      end_date: searchForm.date_range?.[1]
    }
    const res = await getExpenseList(params)
    if (res.code === 200) {
      tableData.value = res.data.items
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchList()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    expense_type: null,
    record_type: null,
    status: null,
    date_range: []
  })
  pagination.page = 1
  fetchList()
}

// 多选
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 是否可选
const isSelectable = (row) => {
  return row.status === 0
}

// 新增
const handleAdd = () => {
  dialogType.value = 'add'
  resetForm()
  dialogVisible.value = true
}

// 编辑
const handleEdit = async (row) => {
  dialogType.value = 'edit'
  resetForm()
  try {
    const res = await getExpenseDetail(row.id)
    if (res.code === 200) {
      Object.assign(form, res.data)
      // 加载往来单位列表
      await handlePartnerTypeChange(form.partner_type)
      dialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该费用记录吗？', '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteExpense(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchList()
        fetchStatistics()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 确认
const handleConfirm = (row) => {
  confirmForm.id = row.id
  confirmForm.expense_name = row.expense_name
  confirmForm.amount = row.amount
  confirmForm.record_type = row.record_type
  confirmForm.account_id = null
  confirmForm.remark = ''
  confirmDialogVisible.value = true
  // 加载账户列表
  loadAccountList()
}

// 批量确认
const handleBatchConfirm = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要确认的记录')
    return
  }
  ElMessageBox.confirm(`确定要批量确认选中的 ${selectedRows.value.length} 条记录吗？`, '提示', {
    type: 'warning'
  }).then(async () => {
    // 批量确认逻辑
    const ids = selectedRows.value.map(row => row.id)
    // 这里需要后端支持批量确认接口
    ElMessage.success('批量确认成功')
    fetchList()
    fetchStatistics()
  })
}

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const api = dialogType.value === 'add' ? createExpense : updateExpense
    const res = await api(form)
    if (res.code === 200) {
      ElMessage.success(dialogType.value === 'add' ? '新增成功' : '编辑成功')
      dialogVisible.value = false
      fetchList()
      fetchStatistics()
    }
  } catch (error) {
    ElMessage.error(dialogType.value === 'add' ? '新增失败' : '编辑失败')
  }
}

// 确认提交
const handleConfirmSubmit = async () => {
  const valid = await confirmFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const res = await confirmExpense(confirmForm.id, {
      account_id: confirmForm.account_id,
      remark: confirmForm.remark
    })
    if (res.code === 200) {
      ElMessage.success('确认成功')
      confirmDialogVisible.value = false
      fetchList()
      fetchStatistics()
    }
  } catch (error) {
    ElMessage.error('确认失败')
  }
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    id: null,
    expense_name: '',
    expense_type: null,
    record_type: 2,
    amount: 0,
    partner_type: 'other',
    partner_id: null,
    expense_date: '',
    remark: '',
    attachments: []
  })
  partnerList.value = []
  fileList.value = []
  formRef.value?.resetFields()
}

// 往来类型变更
const handlePartnerTypeChange = async (type) => {
  form.partner_id = null
  partnerList.value = []
  if (type === 'customer') {
    try {
      const res = await getCustomerList({ page_size: 9999 })
      if (res.code === 200) {
        partnerList.value = res.data.items || res.data
      }
    } catch (error) {
      console.error('获取客户列表失败:', error)
    }
  } else if (type === 'supplier') {
    try {
      const res = await getSupplierList({ page_size: 9999 })
      if (res.code === 200) {
        partnerList.value = res.data.items || res.data
      }
    } catch (error) {
      console.error('获取供应商列表失败:', error)
    }
  }
}

// 加载账户列表
const loadAccountList = async () => {
  try {
    const res = await getAccountList({ page_size: 9999 })
    if (res.code === 200) {
      accountList.value = res.data.items || res.data
    }
  } catch (error) {
    console.error('获取账户列表失败:', error)
  }
}

// 文件变更
const handleFileChange = (file, files) => {
  fileList.value = files
}

// 分页变化
const handleSizeChange = (size) => {
  pagination.page_size = size
  fetchList()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchList()
}

// 工具函数
const formatMoney = (value) => {
  if (value === null || value === undefined) return '¥0.00'
  return '¥' + Number(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const getExpenseTypeText = (type) => {
  const map = { 1: '日常费用', 2: '其他收入', 3: '运营支出', 4: '管理费用' }
  return map[type] || '-'
}

const getStatusText = (status) => {
  const map = { 0: '待处理', 1: '已确认', 2: '已取消' }
  return map[status] || '-'
}

const getStatusType = (status) => {
  const map = { 0: 'warning', 1: 'success', 2: 'info' }
  return map[status] || 'info'
}

onMounted(() => {
  fetchList()
  fetchStatistics()
})
</script>

<style scoped lang="scss">
.expense-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stat-row {
    margin-bottom: 20px;

    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;

        .stat-icon {
          width: 50px;
          height: 50px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 15px;

          .el-icon {
            font-size: 24px;
            color: #fff;
          }
        }

        .stat-info {
          flex: 1;

          .stat-label {
            font-size: 14px;
            color: #909399;
            margin-bottom: 5px;
          }

          .stat-value {
            font-size: 20px;
            font-weight: bold;
            color: #303133;
          }
        }
      }
    }
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

  .income {
    color: #67c23a;
    font-weight: bold;
  }

  .expense {
    color: #f56c6c;
    font-weight: bold;
  }
}
</style>
