<template>
  <div class="salary-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">应发总额</div>
              <div class="stat-value">{{ formatMoney(statistics.total_should_pay) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon><Wallet /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">实发总额</div>
              <div class="stat-value">{{ formatMoney(statistics.total_actual_pay) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c;">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">个税总额</div>
              <div class="stat-value">{{ formatMoney(statistics.total_tax) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">待发放数</div>
              <div class="stat-value">{{ statistics.pending_count || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索栏 -->
    <el-form :model="searchForm" inline class="search-form">
      <el-form-item label="关键词">
        <el-input v-model="searchForm.keyword" placeholder="员工姓名/工资单号" clearable />
      </el-form-item>
      <el-form-item label="部门">
        <el-select v-model="searchForm.department" placeholder="选择部门" clearable>
          <el-option label="全部" :label="'全部'" :value="''" />
          <el-option label="技术部" :label="'技术部'" :value="'技术部'" />
          <el-option label="销售部" :label="'销售部'" :value="'销售部'" />
          <el-option label="财务部" :label="'财务部'" :value="'财务部'" />
          <el-option label="行政部" :label="'行政部'" :value="'行政部'" />
        </el-select>
      </el-form-item>
      <el-form-item label="工资月份">
        <el-date-picker
          v-model="searchForm.salary_month"
          type="month"
          format="YYYY-MM"
          value-format="YYYY-MM"
          placeholder="选择月份"
          clearable
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="searchForm.status" placeholder="选择状态" clearable>
          <el-option label="待发放" :label="'待发放'" :value="0" />
          <el-option label="已发放" :label="'已发放'" :value="1" />
          <el-option label="已取消" :label="'已取消'" :value="2" />
        </el-select>
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
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>新增工资单
      </el-button>
      <el-button type="success" :disabled="selectedRows.length === 0" @click="handleBatchPay">
        <el-icon><Check /></el-icon>批量发放
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="tableData"
      @selection-change="handleSelectionChange"
      border
    >
      <el-table-column type="selection" width="55" :selectable="selectableFn" />
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column prop="salary_no" label="工资单号" width="140" />
      <el-table-column prop="user_name" label="员工姓名" width="100" />
      <el-table-column prop="department" label="部门" width="100" />
      <el-table-column prop="position" label="岗位" width="100" />
      <el-table-column prop="salary_month" label="工资月份" width="100" />
      <el-table-column prop="base_salary" label="基本工资" width="100">
        <template #default="{ row }">
          {{ formatMoney(row.base_salary) }}
        </template>
      </el-table-column>
      <el-table-column prop="performance_salary" label="绩效工资" width="100">
        <template #default="{ row }">
          {{ formatMoney(row.performance_salary) }}
        </template>
      </el-table-column>
      <el-table-column prop="commission" label="提成" width="100">
        <template #default="{ row }">
          {{ formatMoney(row.commission) }}
        </template>
      </el-table-column>
      <el-table-column prop="subsidy" label="补贴" width="100">
        <template #default="{ row }">
          {{ formatMoney(row.subsidy) }}
        </template>
      </el-table-column>
      <el-table-column prop="deduction" label="扣款" width="100">
        <template #default="{ row }">
          {{ formatMoney(row.deduction) }}
        </template>
      </el-table-column>
      <el-table-column prop="should_pay" label="应发金额" width="120">
        <template #default="{ row }">
          <span class="amount">{{ formatMoney(row.should_pay) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="tax" label="个税" width="100">
        <template #default="{ row }">
          {{ formatMoney(row.tax) }}
        </template>
      </el-table-column>
      <el-table-column prop="actual_pay" label="实发金额" width="120">
        <template #default="{ row }">
          <span class="actual">{{ formatMoney(row.actual_pay) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.status === 0" type="warning">待发放</el-tag>
          <el-tag v-else-if="row.status === 1" type="success">已发放</el-tag>
          <el-tag v-else type="info">已取消</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="account_name" label="发放账户" width="140">
        <template #default="{ row }">
          {{ row.status === 1 ? row.account_name : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 0" type="primary" link @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button v-if="row.status === 0" type="success" link @click="handlePay(row)">
            发放
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
      :title="dialogType === 'add' ? '新增工资单' : '编辑工资单'"
      width="700px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="员工" prop="user_id">
              <el-select
                v-model="form.user_id"
                placeholder="选择员工"
                filterable
                :loading="userLoading"
                @change="handleUserChange"
              >
                <el-option
                  v-for="user in userList"
                  :key="user.id"
                  :label="user.real_name || user.username"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工资月份" prop="salary_month">
              <el-date-picker
                v-model="form.salary_month"
                type="month"
                format="YYYY-MM"
                value-format="YYYY-MM"
                placeholder="选择月份"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="部门" prop="department">
              <el-input v-model="form.department" placeholder="输入部门" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="岗位" prop="position">
              <el-input v-model="form.position" placeholder="输入岗位" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="基本工资" prop="base_salary">
              <el-input-number v-model="form.base_salary" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="绩效工资" prop="performance_salary">
              <el-input-number v-model="form.performance_salary" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="提成" prop="commission">
              <el-input-number v-model="form.commission" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="补贴" prop="subsidy">
              <el-input-number v-model="form.subsidy" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="扣款" prop="deduction">
              <el-input-number v-model="form.deduction" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="应发金额">
              <el-input :model-value="formatMoney(shouldPayAmount)" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="个税" prop="tax">
              <el-input-number v-model="form.tax" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实发金额">
              <el-input :model-value="formatMoney(actualPayAmount)" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 发放对话框 -->
    <el-dialog
      v-model="payDialogVisible"
      title="发放工资"
      width="500px"
      destroy-on-close
    >
      <el-form ref="payFormRef" :model="payForm" :rules="payFormRules" label-width="100px">
        <el-form-item label="员工姓名">
          <el-input :model-value="currentRow?.user_name" disabled />
        </el-form-item>
        <el-form-item label="实发金额">
          <el-input :model-value="formatMoney(currentRow?.actual_pay)" disabled />
        </el-form-item>
        <el-form-item label="发放账户" prop="account_id">
          <el-select v-model="payForm.account_id" placeholder="选择发放账户" style="width: 100%;">
            <el-option
              v-for="account in accountList"
              :key="account.id"
              :label="account.name"
              :value="account.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="payForm.remark" type="textarea" :rows="3" placeholder="输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePaySubmit">确定发放</el-button>
      </template>
    </el-dialog>

    <!-- 批量发放对话框 -->
    <el-dialog
      v-model="batchPayDialogVisible"
      title="批量发放工资"
      width="500px"
      destroy-on-close
    >
      <el-form ref="batchPayFormRef" :model="batchPayForm" :rules="batchPayFormRules" label-width="100px">
        <el-form-item label="已选工资单">
          <el-input :model-value="selectedRows.length + '条'" disabled />
        </el-form-item>
        <el-form-item label="发放账户" prop="account_id">
          <el-select v-model="batchPayForm.account_id" placeholder="选择发放账户" style="width: 100%;">
            <el-option
              v-for="account in accountList"
              :key="account.id"
              :label="account.name"
              :value="account.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="统一备注" prop="remark">
          <el-input v-model="batchPayForm.remark" type="textarea" :rows="3" placeholder="输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchPayDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchPaySubmit">确定发放</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Money, Wallet, Document, Timer, Search, RefreshRight,
  Plus, Check
} from '@element-plus/icons-vue'
import {
  getSalaryList, getSalaryDetail, createSalary, updateSalary,
  deleteSalary, paySalary, getSalaryStatistics
} from '@/api/salary'
import { getAccountList } from '@/api/finance'
import { getUserList } from '@/api/user'

// 统计数据
const statistics = reactive({
  total_should_pay: 0,
  total_actual_pay: 0,
  total_tax: 0,
  pending_count: 0
})

// 搜索表单
const searchForm = reactive({
  keyword: '',
  department: '',
  salary_month: '',
  status: null
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 表格数据
const loading = ref(false)
const tableData = ref([])
const selectedRows = ref([])

// 用户列表
const userList = ref([])
const userLoading = ref(false)

// 账户列表
const accountList = ref([])

// 对话框
const dialogVisible = ref(false)
const dialogType = ref('add')
const formRef = ref(null)
const currentRow = ref(null)

// 表单数据
const form = reactive({
  id: null,
  user_id: null,
  department: '',
  position: '',
  salary_month: '',
  base_salary: 0,
  performance_salary: 0,
  commission: 0,
  subsidy: 0,
  deduction: 0,
  tax: 0,
  remark: ''
})

// 表单校验规则
const formRules = {
  user_id: [{ required: true, message: '请选择员工', trigger: 'change' }],
  salary_month: [{ required: true, message: '请选择工资月份', trigger: 'change' }],
  department: [{ required: true, message: '请输入部门', trigger: 'blur' }],
  position: [{ required: true, message: '请输入岗位', trigger: 'blur' }],
  base_salary: [{ required: true, message: '请输入基本工资', trigger: 'blur' }]
}

// 计算应发金额
const shouldPayAmount = computed(() => {
  return (form.base_salary || 0) +
         (form.performance_salary || 0) +
         (form.commission || 0) +
         (form.subsidy || 0) -
         (form.deduction || 0)
})

// 计算实发金额
const actualPayAmount = computed(() => {
  return shouldPayAmount.value - (form.tax || 0)
})

// 发放对话框
const payDialogVisible = ref(false)
const payFormRef = ref(null)
const payForm = reactive({
  account_id: null,
  remark: ''
})

const payFormRules = {
  account_id: [{ required: true, message: '请选择发放账户', trigger: 'change' }]
}

// 批量发放对话框
const batchPayDialogVisible = ref(false)
const batchPayFormRef = ref(null)
const batchPayForm = reactive({
  account_id: null,
  remark: ''
})

const batchPayFormRules = {
  account_id: [{ required: true, message: '请选择发放账户', trigger: 'change' }]
}

// 格式化金额
const formatMoney = (value) => {
  if (value === null || value === undefined) return '¥0.00'
  return '¥' + parseFloat(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const res = await getSalaryStatistics()
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
      ...searchForm
    }
    const res = await getSalaryList(params)
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

// 获取用户列表
const fetchUserList = async (keyword = '') => {
  userLoading.value = true
  try {
    const res = await getUserList({ keyword, page_size: 50 })
    if (res.code === 200) {
      userList.value = res.data.items || res.data || []
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    userLoading.value = false
  }
}

// 获取账户列表
const fetchAccountList = async () => {
  try {
    const res = await getAccountList({ page_size: 100 })
    if (res.code === 200) {
      accountList.value = res.data.items || []
    }
  } catch (error) {
    console.error('获取账户列表失败:', error)
  }
}

// 用户选择变化
const handleUserChange = (userId) => {
  const user = userList.value.find(u => u.id === userId)
  if (user) {
    form.department = user.department || ''
    form.position = user.position || ''
    // 自动带入用户的基本工资
    if (user.base_salary !== null && user.base_salary !== undefined) {
      form.base_salary = Number(user.base_salary)
    }
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchList()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.department = ''
  searchForm.salary_month = ''
  searchForm.status = null
  handleSearch()
}

// 分页大小变化
const handleSizeChange = (size) => {
  pagination.page_size = size
  fetchList()
}

// 页码变化
const handlePageChange = (page) => {
  pagination.page = page
  fetchList()
}

// 表格选择变化
const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

// 是否可选
const selectableFn = (row) => {
  return row.status === 0
}

// 新增
const handleAdd = () => {
  dialogType.value = 'add'
  resetForm()
  dialogVisible.value = true
  fetchUserList()
}

// 编辑
const handleEdit = async (row) => {
  dialogType.value = 'edit'
  resetForm()
  try {
    const res = await getSalaryDetail(row.id)
    if (res.code === 200) {
      Object.assign(form, res.data)
      dialogVisible.value = true
      fetchUserList()
    }
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

// 重置表单
const resetForm = () => {
  form.id = null
  form.user_id = null
  form.department = ''
  form.position = ''
  form.salary_month = ''
  form.base_salary = 0
  form.performance_salary = 0
  form.commission = 0
  form.subsidy = 0
  form.deduction = 0
  form.tax = 0
  form.remark = ''
}

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const data = {
      ...form,
      should_pay: shouldPayAmount.value,
      actual_pay: actualPayAmount.value
    }
    const res = dialogType.value === 'add'
      ? await createSalary(data)
      : await updateSalary(form.id, data)

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

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm('确定删除该工资单吗？', '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteSalary(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchList()
        fetchStatistics()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 发放
const handlePay = (row) => {
  currentRow.value = row
  payForm.account_id = null
  payForm.remark = ''
  payDialogVisible.value = true
  fetchAccountList()
}

// 提交发放
const handlePaySubmit = async () => {
  const valid = await payFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const res = await paySalary(currentRow.value.id, {
      account_id: payForm.account_id,
      remark: payForm.remark
    })
    if (res.code === 200) {
      ElMessage.success('发放成功')
      payDialogVisible.value = false
      fetchList()
      fetchStatistics()
    }
  } catch (error) {
    ElMessage.error('发放失败')
  }
}

// 批量发放
const handleBatchPay = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要发放的工资单')
    return
  }
  batchPayForm.account_id = null
  batchPayForm.remark = ''
  batchPayDialogVisible.value = true
  fetchAccountList()
}

// 提交批量发放
const handleBatchPaySubmit = async () => {
  const valid = await batchPayFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const ids = selectedRows.value.map(row => row.id)
    // 假设批量发放API为 batchPaySalary
    const res = await paySalary(ids, {
      account_id: batchPayForm.account_id,
      remark: batchPayForm.remark,
      batch: true
    })
    if (res.code === 200) {
      ElMessage.success('批量发放成功')
      batchPayDialogVisible.value = false
      selectedRows.value = []
      fetchList()
      fetchStatistics()
    }
  } catch (error) {
    ElMessage.error('批量发放失败')
  }
}

onMounted(() => {
  fetchList()
  fetchStatistics()
})
</script>

<style scoped lang="scss">
.salary-page {
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

  .amount {
    color: #409eff;
    font-weight: bold;
  }

  .actual {
    color: #67c23a;
    font-weight: bold;
  }
}
</style>
