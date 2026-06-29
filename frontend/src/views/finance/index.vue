<template>
  <div class="finance-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>财务管理</span>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stat-row">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #67c23a;">
                <el-icon><Wallet /></el-icon>
              </div>
              <div class="stat-info">
                <p class="stat-label">账户总数</p>
                <p class="stat-value">{{ accountStats.total_count || 0 }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #409eff;">
                <el-icon><Money /></el-icon>
              </div>
              <div class="stat-info">
                <p class="stat-label">总余额</p>
                <p class="stat-value">¥{{ (accountStats.total_balance || 0).toFixed(2) }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #e6a23c;">
                <el-icon><ArrowDown /></el-icon>
              </div>
              <div class="stat-info">
                <p class="stat-label">今日收入</p>
                <p class="stat-value">¥{{ (accountStats.today_income || 0).toFixed(2) }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #f56c6c;">
                <el-icon><ArrowUp /></el-icon>
              </div>
              <div class="stat-info">
                <p class="stat-label">今日支出</p>
                <p class="stat-value">¥{{ (accountStats.today_expense || 0).toFixed(2) }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Tabs -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- ==================== 账户管理 tab ==================== -->
        <el-tab-pane label="账户管理" name="account">
          <!-- 顶部操作按钮 -->
          <div class="tab-toolbar">
            <div>
              <el-button type="primary" :icon="Plus" @click="handleAddAccount">新增账户</el-button>
              <el-button type="warning" :icon="Sort" @click="handleOpenTransfer">账户转账</el-button>
            </div>
          </div>

          <!-- 账户搜索 -->
          <el-form :inline="true" :model="accountSearchForm" class="search-form">
            <el-form-item label="关键词">
              <el-input v-model="accountSearchForm.keyword" placeholder="账户名称" clearable />
            </el-form-item>
            <el-form-item label="账户类型">
              <el-select v-model="accountSearchForm.account_type" placeholder="全部" clearable style="width: 150px">
                <el-option label="现金" :value="1" />
                <el-option label="银行" :value="2" />
                <el-option label="支付宝" :value="3" />
                <el-option label="微信" :value="4" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="fetchAccounts">搜索</el-button>
              <el-button :icon="Refresh" @click="resetAccountSearch">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- 账户表格 -->
          <el-table :data="accountData" stripe border v-loading="accountLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="account_name" label="账户名称" min-width="150" />
            <el-table-column prop="account_type" label="账户类型" width="100" align="center">
              <template #default="{ row }">
                {{ accountTypeMap[row.account_type] || row.account_type }}
              </template>
            </el-table-column>
            <el-table-column prop="account_no" label="账号" width="150" />
            <el-table-column prop="balance" label="当前余额" width="120" align="right">
              <template #default="{ row }">
                <span :class="{ 'negative': row.balance < 0 }">¥{{ row.balance?.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status ? 'success' : 'info'" size="small">{{ row.status ? '启用' : '禁用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" :icon="Edit" @click="handleEditAccount(row)">编辑</el-button>
                <el-button type="warning" link size="small" @click="handleOpenAdjust(row)">余额调整</el-button>
                <el-button type="danger" link size="small" @click="handleDeleteAccount(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="accountPagination.page"
            v-model:page-size="accountPagination.pageSize"
            :total="accountPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="fetchAccounts"
            @current-change="fetchAccounts"
          />
        </el-tab-pane>

        <!-- ==================== 流水查询 tab ==================== -->
        <el-tab-pane label="流水查询" name="records">
          <!-- 筛选条件 -->
          <el-form :inline="true" :model="recordSearchForm" class="search-form">
            <el-form-item label="账户">
              <el-select v-model="recordSearchForm.account_id" placeholder="全部账户" clearable style="width: 180px">
                <el-option v-for="a in accountData" :key="a.id" :label="a.account_name" :value="a.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="recordSearchForm.record_type" placeholder="全部" clearable style="width: 120px">
                <el-option label="收入" value="income" />
                <el-option label="支出" value="expense" />
              </el-select>
            </el-form-item>
            <el-form-item label="关联类型">
              <el-select v-model="recordSearchForm.related_type" placeholder="全部" clearable style="width: 120px">
                <el-option label="收款" value="receive" />
                <el-option label="付款" value="pay" />
                <el-option label="转账" value="transfer" />
                <el-option label="调整" value="adjust" />
              </el-select>
            </el-form-item>
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="recordSearchForm.date_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="recordSearchForm.keyword" placeholder="备注/单号" clearable style="width: 150px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="fetchEnhancedRecords">搜索</el-button>
              <el-button :icon="Refresh" @click="resetRecordSearch">重置</el-button>
              <el-button type="success" :icon="Download" @click="exportRecords">导出</el-button>
            </el-form-item>
          </el-form>

          <!-- 流水表格 -->
          <el-table :data="enhancedRecords" stripe border v-loading="recordLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="account_name" label="账户名称" min-width="120" />
            <el-table-column prop="account_type_text" label="账户类型" width="100" align="center" />
            <el-table-column prop="record_type_text" label="类型" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.record_type === 'income' ? 'success' : 'danger'" size="small">
                  {{ row.record_type_text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="120" align="right">
              <template #default="{ row }">
                <span :class="row.record_type === 'income' ? 'positive' : 'negative'">
                  {{ row.record_type === 'income' ? '+' : '-' }}¥{{ row.amount?.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="balance_before" label="变动前余额" width="120" align="right">
              <template #default="{ row }">
                ¥{{ row.balance_before?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="balance_after" label="变动后余额" width="120" align="right">
              <template #default="{ row }">
                ¥{{ row.balance_after?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="related_type" label="关联类型" width="100" align="center" />
            <el-table-column prop="related_no" label="关联单号" width="150" show-overflow-tooltip />
            <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
            <el-table-column prop="created_at" label="时间" width="160" />
          </el-table>

          <el-pagination
            v-model:current-page="recordPagination.page"
            v-model:page-size="recordPagination.pageSize"
            :total="recordPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="fetchEnhancedRecords"
            @current-change="fetchEnhancedRecords"
          />
        </el-tab-pane>

        <!-- ==================== 转账记录 tab ==================== -->
        <el-tab-pane label="转账记录" name="transfer">
          <el-table :data="transferRecords" stripe border v-loading="transferLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="account_name" label="账户名称" min-width="120" />
            <el-table-column prop="account_type_text" label="账户类型" width="100" align="center" />
            <el-table-column prop="record_type_text" label="类型" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.record_type === 'income' ? 'success' : 'danger'" size="small">
                  {{ row.record_type_text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="120" align="right">
              <template #default="{ row }">
                <span :class="row.record_type === 'income' ? 'positive' : 'negative'">
                  {{ row.record_type === 'income' ? '+' : '-' }}¥{{ row.amount?.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="balance_before" label="变动前余额" width="120" align="right">
              <template #default="{ row }">
                ¥{{ row.balance_before?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="balance_after" label="变动后余额" width="120" align="right">
              <template #default="{ row }">
                ¥{{ row.balance_after?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="related_no" label="关联单号" width="150" show-overflow-tooltip />
            <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
            <el-table-column prop="created_at" label="时间" width="160" />
          </el-table>

          <el-pagination
            v-model:current-page="transferPagination.page"
            v-model:page-size="transferPagination.pageSize"
            :total="transferPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="fetchTransferRecords"
            @current-change="fetchTransferRecords"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- ==================== 新增/编辑账户弹窗 ==================== -->
    <el-dialog v-model="accountDialogVisible" :title="isEditAccount ? '编辑账户' : '新增账户'" width="500px" destroy-on-close>
      <el-form :model="accountForm" :rules="accountRules" ref="accountFormRef" label-width="100px">
        <el-form-item label="账户名称" prop="account_name">
          <el-input v-model="accountForm.account_name" placeholder="账户名称" />
        </el-form-item>
        <el-form-item label="账户类型" prop="account_type">
          <el-select v-model="accountForm.account_type" placeholder="选择类型" style="width: 100%">
            <el-option label="现金" :value="1" />
            <el-option label="银行" :value="2" />
            <el-option label="支付宝" :value="3" />
            <el-option label="微信" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号">
          <el-input v-model="accountForm.account_no" placeholder="账号/卡号" />
        </el-form-item>
        <el-form-item label="期初余额">
          <el-input-number v-model="accountForm.opening_balance" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="accountForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="accountForm.remark" type="textarea" :rows="3" placeholder="备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAccountForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 转账对话框 ==================== -->
    <el-dialog v-model="transferDialogVisible" title="账户转账" width="500px" destroy-on-close>
      <el-form :model="transferForm" :rules="transferRules" ref="transferFormRef" label-width="100px">
        <el-form-item label="转出账户" prop="from_account_id">
          <el-select
            v-model="transferForm.from_account_id"
            placeholder="选择转出账户"
            style="width: 100%"
            @change="handleTransferFromChange"
          >
            <el-option
              v-for="a in accountData"
              :key="a.id"
              :label="`${a.account_name} (余额: ¥${a.balance?.toFixed(2)})`"
              :value="a.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="转入账户" prop="to_account_id">
          <el-select
            v-model="transferForm.to_account_id"
            placeholder="选择转入账户"
            style="width: 100%"
          >
            <el-option
              v-for="a in filteredTransferToAccounts"
              :key="a.id"
              :label="`${a.account_name} (余额: ¥${a.balance?.toFixed(2)})`"
              :value="a.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="转账金额" prop="amount">
          <el-input-number v-model="transferForm.amount" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="transferForm.remark" type="textarea" :rows="3" placeholder="备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transferDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTransferForm" :loading="submitLoading">确定转账</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 余额调整对话框 ==================== -->
    <el-dialog v-model="adjustDialogVisible" title="余额调整" width="500px" destroy-on-close>
      <el-form :model="adjustForm" :rules="adjustRules" ref="adjustFormRef" label-width="100px">
        <el-form-item label="账户名称">
          <el-input :model-value="adjustAccountName" disabled />
        </el-form-item>
        <el-form-item label="当前余额">
          <el-input :model-value="`¥${adjustCurrentBalance?.toFixed(2)}`" disabled />
        </el-form-item>
        <el-form-item label="调整金额" prop="amount">
          <el-input-number v-model="adjustForm.amount" :precision="2" style="width: 100%" placeholder="正数增加，负数减少" />
        </el-form-item>
        <el-form-item label="调整原因" prop="reason">
          <el-input v-model="adjustForm.reason" type="textarea" :rows="3" placeholder="请输入调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAdjustForm" :loading="submitLoading">确定调整</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Wallet, Money, ArrowDown, ArrowUp, Sort, Edit } from '@element-plus/icons-vue'
import { getAccountList, createAccount, updateAccount, deleteAccount, transferAccount, adjustAccount, getFinanceRecordsEnhanced } from '@/api/finance'

// ==================== 账户类型映射 ====================
const accountTypeMap = { 1: '现金', 2: '银行', 3: '支付宝', 4: '微信' }

// ==================== 通用状态 ====================
const activeTab = ref('account')
const accountLoading = ref(false)
const recordLoading = ref(false)
const transferLoading = ref(false)
const submitLoading = ref(false)
const accountData = ref([])
const accountStats = ref({})

// ==================== 账户管理 ====================
const accountDialogVisible = ref(false)
const isEditAccount = ref(false)
const currentAccount = ref(null)
const accountFormRef = ref(null)

const accountSearchForm = reactive({
  keyword: '',
  account_type: ''
})

const accountPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const accountForm = reactive({
  account_name: '',
  account_type: '',
  account_no: '',
  opening_balance: 0,
  status: 1,
  remark: ''
})

const accountRules = {
  account_name: [{ required: true, message: '请输入账户名称', trigger: 'blur' }],
  account_type: [{ required: true, message: '请选择账户类型', trigger: 'change' }]
}

// ==================== 转账 ====================
const transferDialogVisible = ref(false)
const transferFormRef = ref(null)

const transferForm = reactive({
  from_account_id: null,
  to_account_id: null,
  amount: null,
  remark: ''
})

const transferRules = {
  from_account_id: [{ required: true, message: '请选择转出账户', trigger: 'change' }],
  to_account_id: [{ required: true, message: '请选择转入账户', trigger: 'change' }],
  amount: [{ required: true, message: '请输入转账金额', trigger: 'blur' }]
}

// 过滤转入账户（排除已选转出账户）
const filteredTransferToAccounts = computed(() => {
  if (!transferForm.from_account_id) return accountData.value
  return accountData.value.filter(a => a.id !== transferForm.from_account_id)
})

// ==================== 余额调整 ====================
const adjustDialogVisible = ref(false)
const adjustFormRef = ref(null)
const adjustTargetAccount = ref(null)

const adjustForm = reactive({
  amount: null,
  reason: ''
})

const adjustRules = {
  amount: [{ required: true, message: '请输入调整金额', trigger: 'blur' }],
  reason: [{ required: true, message: '请输入调整原因', trigger: 'blur' }]
}

const adjustAccountName = computed(() => adjustTargetAccount.value?.account_name || '')
const adjustCurrentBalance = computed(() => adjustTargetAccount.value?.balance || 0)

// ==================== 流水查询 ====================
const enhancedRecords = ref([])

const recordSearchForm = reactive({
  account_id: null,
  record_type: '',
  related_type: '',
  date_range: null,
  keyword: ''
})

const recordPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// ==================== 转账记录 ====================
const transferRecords = ref([])

const transferPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// ==================== 数据获取 ====================
const fetchAccounts = async () => {
  accountLoading.value = true
  try {
    const params = {
      page: accountPagination.page,
      page_size: accountPagination.pageSize,
      keyword: accountSearchForm.keyword,
      account_type: accountSearchForm.account_type
    }
    const res = await getAccountList(params)
    if (res.code === 200) {
      accountData.value = res.data.list || res.data
      accountPagination.total = res.data.total || 0
      accountStats.value = res.data.stats || {}
    }
  } catch (error) {
    console.error('获取账户列表失败:', error)
    ElMessage.error('获取账户列表失败')
  } finally {
    accountLoading.value = false
  }
}

const fetchEnhancedRecords = async () => {
  recordLoading.value = true
  try {
    const params = {
      page: recordPagination.page,
      page_size: recordPagination.pageSize,
      account_id: recordSearchForm.account_id,
      record_type: recordSearchForm.record_type,
      related_type: recordSearchForm.related_type,
      start_date: recordSearchForm.date_range?.[0],
      end_date: recordSearchForm.date_range?.[1],
      keyword: recordSearchForm.keyword
    }
    const res = await getFinanceRecordsEnhanced(params)
    if (res.code === 200) {
      enhancedRecords.value = res.data.items || []
      recordPagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取流水记录失败:', error)
    ElMessage.error('获取流水记录失败')
  } finally {
    recordLoading.value = false
  }
}

const fetchTransferRecords = async () => {
  transferLoading.value = true
  try {
    const params = {
      page: transferPagination.page,
      page_size: transferPagination.pageSize,
      related_type: 'transfer'
    }
    const res = await getFinanceRecordsEnhanced(params)
    if (res.code === 200) {
      transferRecords.value = res.data.items || []
      transferPagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取转账记录失败:', error)
    ElMessage.error('获取转账记录失败')
  } finally {
    transferLoading.value = false
  }
}

// ==================== Tab 切换 ====================
const handleTabChange = (tab) => {
  if (tab === 'records') {
    fetchEnhancedRecords()
  } else if (tab === 'transfer') {
    fetchTransferRecords()
  }
}

// ==================== 账户搜索重置 ====================
const resetAccountSearch = () => {
  accountSearchForm.keyword = ''
  accountSearchForm.account_type = ''
  accountPagination.page = 1
  fetchAccounts()
}

// ==================== 流水搜索重置 ====================
const resetRecordSearch = () => {
  recordSearchForm.account_id = null
  recordSearchForm.record_type = ''
  recordSearchForm.related_type = ''
  recordSearchForm.date_range = null
  recordSearchForm.keyword = ''
  recordPagination.page = 1
  fetchEnhancedRecords()
}

// ==================== 导出流水 ====================
const exportRecords = () => {
  if (!enhancedRecords.value || enhancedRecords.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  
  const headers = ['日期', '账户名称', '账户类型', '类型', '金额', '变动前余额', '变动后余额', '关联类型', '关联单号', '备注']
  const rows = enhancedRecords.value.map(item => [
    item.record_date || '',
    item.account_name || '',
    item.account_type_text || '',
    item.record_type_text || '',
    item.record_type === 'income' ? `+${Number(item.amount || 0).toFixed(2)}` : `-${Number(item.amount || 0).toFixed(2)}`,
    Number(item.balance_before || 0).toFixed(2),
    Number(item.balance_after || 0).toFixed(2),
    item.related_type || '',
    item.related_no || '',
    item.remark || ''
  ])
  
  const csvContent = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `账户流水_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// ==================== 新增账户 ====================
const handleAddAccount = () => {
  isEditAccount.value = false
  currentAccount.value = null
  Object.assign(accountForm, {
    account_name: '',
    account_type: '',
    account_no: '',
    opening_balance: 0,
    status: 1,
    remark: ''
  })
  accountDialogVisible.value = true
}

// ==================== 编辑账户 ====================
const handleEditAccount = (row) => {
  isEditAccount.value = true
  currentAccount.value = row
  Object.assign(accountForm, {
    account_name: row.account_name,
    account_type: row.account_type,
    account_no: row.account_no,
    opening_balance: row.opening_balance || 0,
    status: row.status,
    remark: row.remark
  })
  accountDialogVisible.value = true
}

// ==================== 删除账户 ====================
const handleDeleteAccount = (row) => {
  ElMessageBox.confirm('确定要删除该账户吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteAccount(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchAccounts()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// ==================== 提交账户表单 ====================
const submitAccountForm = async () => {
  if (!accountFormRef.value) return
  await accountFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      let res
      if (isEditAccount.value) {
        res = await updateAccount(currentAccount.value.id, accountForm)
      } else {
        res = await createAccount(accountForm)
      }
      if (res.code === 200) {
        ElMessage.success(isEditAccount.value ? '更新成功' : '创建成功')
        accountDialogVisible.value = false
        fetchAccounts()
      }
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// ==================== 打开转账对话框 ====================
const handleOpenTransfer = () => {
  Object.assign(transferForm, {
    from_account_id: null,
    to_account_id: null,
    amount: null,
    remark: ''
  })
  transferDialogVisible.value = true
}

// 转出账户变更时清空转入账户
const handleTransferFromChange = () => {
  transferForm.to_account_id = null
}

// ==================== 提交转账表单 ====================
const submitTransferForm = async () => {
  if (!transferFormRef.value) return
  await transferFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const res = await transferAccount(transferForm)
      if (res.code === 200) {
        ElMessage.success('转账成功')
        transferDialogVisible.value = false
        fetchAccounts()
      }
    } catch (error) {
      ElMessage.error('转账失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// ==================== 打开余额调整对话框 ====================
const handleOpenAdjust = (row) => {
  adjustTargetAccount.value = row
  Object.assign(adjustForm, {
    amount: null,
    reason: ''
  })
  adjustDialogVisible.value = true
}

// ==================== 提交余额调整表单 ====================
const submitAdjustForm = async () => {
  if (!adjustFormRef.value) return
  await adjustFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const res = await adjustAccount(adjustTargetAccount.value.id, adjustForm)
      if (res.code === 200) {
        ElMessage.success('余额调整成功')
        adjustDialogVisible.value = false
        fetchAccounts()
      }
    } catch (error) {
      ElMessage.error('余额调整失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// ==================== 初始化 ====================
onMounted(() => {
  fetchAccounts()
})
</script>

<style lang="scss" scoped>
.finance-page {
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

  .tab-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .positive {
    color: #67c23a;
    font-weight: bold;
  }

  .negative {
    color: #f56c6c;
    font-weight: bold;
  }

  .warning {
    color: #e6a23c;
    font-weight: bold;
  }
}
</style>
