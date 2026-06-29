<template>
  <div class="payable-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>应付管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="供应商">
          <el-input v-model="searchForm.supplier" placeholder="供应商名称" clearable />
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
          <el-button type="primary" :icon="Search" @click="fetchData">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="supplier_name" label="供应商名称" min-width="150" />
        <el-table-column prop="biz_no" label="关联单号" width="150" />
        <el-table-column prop="total_amount" label="应付金额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ row.total_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="paid_amount" label="已付金额" width="120" align="right">
          <template #default="{ row }">
            <span class="positive">¥{{ row.paid_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unpaid_amount" label="未付金额" width="120" align="right">
          <template #default="{ row }">
            <span class="warning">¥{{ row.unpaid_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="aging_days" label="账龄" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getAgingType(row.aging_days)" size="small">{{ row.aging_days }}天</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handlePayment(row)">付款</el-button>
            <el-button type="info" link size="small" @click="handleView(row)">查看</el-button>
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
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </el-card>

    <!-- 付款弹窗 -->
    <el-dialog v-model="paymentDialogVisible" title="付款" width="500px" destroy-on-close>
      <el-form :model="paymentForm" :rules="paymentRules" ref="paymentFormRef" label-width="100px">
        <el-form-item label="供应商">
          <span>{{ currentRow?.supplier_name }}</span>
        </el-form-item>
        <el-form-item label="未付金额">
          <span class="warning">¥{{ currentRow?.unpaid_amount?.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="付款金额" prop="amount">
          <el-input-number v-model="paymentForm.amount" :min="0" :max="currentRow?.unpaid_amount" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="付款方式" prop="payment_method">
          <el-select v-model="paymentForm.payment_method" placeholder="选择付款方式" style="width: 100%">
            <el-option label="现金" value="cash" />
            <el-option label="银行转账" value="bank" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信" value="wechat" />
          </el-select>
        </el-form-item>
        <el-form-item label="付款账户" prop="account_id">
          <el-select v-model="paymentForm.account_id" placeholder="选择付款账户" style="width: 100%">
            <el-option v-for="a in accountList" :key="a.id" :label="a.account_name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="paymentForm.remark" type="textarea" :rows="3" placeholder="备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paymentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPayment" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="viewDialogVisible" title="应付详情" width="600px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="供应商名称">{{ currentRow?.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="关联单号">{{ currentRow?.biz_no }}</el-descriptions-item>
        <el-descriptions-item label="应付金额">¥{{ currentRow?.total_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="已付金额">¥{{ currentRow?.paid_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="未付金额">
          <span class="warning">¥{{ currentRow?.unpaid_amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="账龄">{{ currentRow?.aging_days }}天</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentRow?.status)" size="small">{{ getStatusText(currentRow?.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建日期">{{ currentRow?.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const accountList = ref([])
const currentRow = ref(null)
const paymentDialogVisible = ref(false)
const viewDialogVisible = ref(false)
const paymentFormRef = ref(null)

const searchForm = reactive({
  supplier: '',
  date_range: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const paymentForm = reactive({
  amount: 0,
  payment_method: '',
  account_id: '',
  remark: ''
})

const paymentRules = {
  amount: [{ required: true, message: '请输入付款金额', trigger: 'blur' }],
  payment_method: [{ required: true, message: '请选择付款方式', trigger: 'change' }],
  account_id: [{ required: true, message: '请选择付款账户', trigger: 'change' }]
}

// 模拟数据
const mockData = [
  { id: 1, supplier_name: '供应商A', biz_no: 'PO2024001', total_amount: 100000, paid_amount: 50000, unpaid_amount: 50000, aging_days: 10, status: 'pending', created_at: '2024-01-18' },
  { id: 2, supplier_name: '供应商B', biz_no: 'PO2024002', total_amount: 60000, paid_amount: 60000, unpaid_amount: 0, aging_days: 3, status: 'completed', created_at: '2024-01-12' },
  { id: 3, supplier_name: '供应商C', biz_no: 'PO2024003', total_amount: 150000, paid_amount: 80000, unpaid_amount: 70000, aging_days: 25, status: 'pending', created_at: '2024-01-08' },
  { id: 4, supplier_name: '供应商D', biz_no: 'PO2024004', total_amount: 45000, paid_amount: 0, unpaid_amount: 45000, aging_days: 40, status: 'overdue', created_at: '2023-12-25' },
  { id: 5, supplier_name: '供应商E', biz_no: 'PO2024005', total_amount: 80000, paid_amount: 40000, unpaid_amount: 40000, aging_days: 18, status: 'pending', created_at: '2024-01-14' }
]

const getAgingType = (days) => {
  if (days <= 15) return 'success'
  if (days <= 30) return 'warning'
  return 'danger'
}

const getStatusType = (status) => {
  const types = { pending: 'warning', completed: 'success', overdue: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { pending: '待付款', completed: '已结清', overdue: '已逾期' }
  return texts[status] || status
}

const fetchData = async () => {
  loading.value = true
  try {
    // 实际API调用
    // const res = await request.get('/finance/payables', {
    //   params: {
    //     page: pagination.page,
    //     page_size: pagination.pageSize,
    //     supplier: searchForm.supplier,
    //     start_date: searchForm.date_range?.[0],
    //     end_date: searchForm.date_range?.[1]
    //   }
    // })
    // if (res.code === 200) {
    //   tableData.value = res.data.list
    //   pagination.total = res.data.total
    // }

    // 模拟数据
    setTimeout(() => {
      tableData.value = mockData
      pagination.total = mockData.length
      loading.value = false
    }, 300)
  } catch (error) {
    console.error('获取应付数据失败:', error)
    ElMessage.error('获取应付数据失败')
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.supplier = ''
  searchForm.date_range = null
  pagination.page = 1
  fetchData()
}

// 导出
const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.supplier) params.append('keyword', searchForm.supplier)
  if (searchForm.date_range?.[0]) params.append('start_date', searchForm.date_range[0])
  if (searchForm.date_range?.[1]) params.append('end_date', searchForm.date_range[1])
  const token = localStorage.getItem('token') || ''
  window.open(`/api/finance/payables/export?${params.toString()}&token=${token}`, '_blank')
}

const handlePayment = (row) => {
  if (row.unpaid_amount <= 0) {
    ElMessage.warning('该订单已结清')
    return
  }
  currentRow.value = row
  Object.assign(paymentForm, {
    amount: row.unpaid_amount,
    payment_method: '',
    account_id: '',
    remark: ''
  })
  paymentDialogVisible.value = true
}

const handleView = (row) => {
  currentRow.value = row
  viewDialogVisible.value = true
}

const submitPayment = async () => {
  if (!paymentFormRef.value) return
  await paymentFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      // const res = await request.post('/finance/payables/payment', {
      //   payable_id: currentRow.value.id,
      //   ...paymentForm
      // })
      // if (res.code === 200) {
      //   ElMessage.success('付款成功')
      //   paymentDialogVisible.value = false
      //   fetchData()
      // }

      // 模拟提交
      setTimeout(() => {
        ElMessage.success('付款成功')
        paymentDialogVisible.value = false
        submitLoading.value = false
        fetchData()
      }, 500)
    } catch (error) {
      ElMessage.error('付款失败')
      submitLoading.value = false
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.payable-page {
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

  .amount {
    color: #409eff;
    font-weight: bold;
  }

  .positive {
    color: #67c23a;
    font-weight: bold;
  }

  .warning {
    color: #e6a23c;
    font-weight: bold;
  }
}
</style>
