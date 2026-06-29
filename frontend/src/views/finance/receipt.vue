<template>
  <div class="receipt-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>收款管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
            <el-button type="primary" :icon="Plus" @click="handleAdd">新增收款</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="客户">
          <el-input v-model="searchForm.customer" placeholder="客户名称" clearable />
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
          <el-button type="primary" :icon="Search" @click="fetchData">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="related_no" label="收款单号" width="180" />
        <el-table-column prop="customer_name" label="客户" min-width="150">
          <template #default="{ row }">
            {{ row.customer_name || '没有数据' }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="收款金额" width="120" align="right">
          <template #default="{ row }">
            <span class="positive">¥{{ Number(row.amount || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="account_name" label="收款账户" min-width="150">
          <template #default="{ row }">
            {{ row.account_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="收款日期" width="160">
          <template #default="{ row }">
            {{ row.created_at ? row.created_at.substring(0, 10) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="操作人" width="100">
          <template #default="{ row }">
            {{ row.created_by_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="info" link size="small" @click="handleView(row)">查看</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑收款弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增收款" width="500px" destroy-on-close>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="客户" prop="customer_id">
          <el-select v-model="form.customer_id" placeholder="选择客户" style="width: 100%" filterable>
            <el-option v-for="c in customerList" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联应收" prop="receivable_id">
          <el-select v-model="form.receivable_id" placeholder="选择关联应收单" style="width: 100%" clearable>
            <el-option v-for="r in receivableList" :key="r.id" :label="r.biz_no" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款金额" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="收款方式" prop="payment_method">
          <el-select v-model="form.payment_method" placeholder="选择收款方式" style="width: 100%">
            <el-option label="现金" value="cash" />
            <el-option label="银行转账" value="bank" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信" value="wechat" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款账户" prop="account_id">
          <el-select v-model="form.account_id" placeholder="选择收款账户" style="width: 100%">
            <el-option v-for="a in accountList" :key="a.id" :label="a.account_name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款日期" prop="receipt_date">
          <el-date-picker v-model="form.receipt_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="viewDialogVisible" title="收款详情" width="600px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="收款单号">{{ currentRow?.receipt_no }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ currentRow?.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="收款金额">
          <span class="positive">¥{{ currentRow?.amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="收款方式">{{ getPaymentMethodText(currentRow?.payment_method) }}</el-descriptions-item>
        <el-descriptions-item label="收款账户">{{ currentRow?.account_name }}</el-descriptions-item>
        <el-descriptions-item label="收款日期">{{ currentRow?.receipt_date }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentRow?.operator_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentRow?.created_at }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentRow?.remark }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download } from '@element-plus/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const accountList = ref([])
const customerList = ref([])
const receivableList = ref([])
const currentRow = ref(null)
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const formRef = ref(null)

const searchForm = reactive({
  customer: '',
  date_range: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  customer_id: '',
  receivable_id: '',
  amount: 0,
  payment_method: '',
  account_id: '',
  receipt_date: new Date().toISOString().split('T')[0],
  remark: ''
})

const rules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  amount: [{ required: true, message: '请输入收款金额', trigger: 'blur' }],
  payment_method: [{ required: true, message: '请选择收款方式', trigger: 'change' }],
  account_id: [{ required: true, message: '请选择收款账户', trigger: 'change' }],
  receipt_date: [{ required: true, message: '请选择收款日期', trigger: 'change' }]
}

// 模拟数据
const mockData = [
  { id: 1, receipt_no: 'RC2024001', customer_name: '客户A', amount: 20000, payment_method: 'bank', account_name: '中国银行', receipt_date: '2024-01-20', operator_name: '张三', remark: '货款', created_at: '2024-01-20 10:30:00' },
  { id: 2, receipt_no: 'RC2024002', customer_name: '客户B', amount: 80000, payment_method: 'alipay', account_name: '支付宝', receipt_date: '2024-01-18', operator_name: '李四', remark: '', created_at: '2024-01-18 14:20:00' },
  { id: 3, receipt_no: 'RC2024003', customer_name: '客户C', amount: 50000, payment_method: 'wechat', account_name: '微信', receipt_date: '2024-01-15', operator_name: '张三', remark: '预付款', created_at: '2024-01-15 09:15:00' },
  { id: 4, receipt_no: 'RC2024004', customer_name: '客户A', amount: 15000, payment_method: 'cash', account_name: '现金', receipt_date: '2024-01-12', operator_name: '王五', remark: '', created_at: '2024-01-12 16:45:00' },
  { id: 5, receipt_no: 'RC2024005', customer_name: '客户D', amount: 35000, payment_method: 'bank', account_name: '工商银行', receipt_date: '2024-01-10', operator_name: '李四', remark: '尾款', created_at: '2024-01-10 11:00:00' }
]

const getPaymentMethodText = (method) => {
  const methods = { cash: '现金', bank: '银行转账', alipay: '支付宝', wechat: '微信' }
  return methods[method] || method
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/finance/records', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        record_type: 1, // 收入
        keyword: searchForm.customer,
        start_date: searchForm.date_range?.[0],
        end_date: searchForm.date_range?.[1]
      }
    })
    if (res.code === 200) {
      tableData.value = res.data.list || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取收款数据失败:', error)
    ElMessage.error('获取收款数据失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.customer = ''
  searchForm.date_range = null
  pagination.page = 1
  fetchData()
}

// 导出
const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.customer) params.append('keyword', searchForm.customer)
  if (searchForm.date_range?.[0]) params.append('start_date', searchForm.date_range[0])
  if (searchForm.date_range?.[1]) params.append('end_date', searchForm.date_range[1])
  const token = localStorage.getItem('token') || ''
  window.open(`/api/sales/receipts/export?${params.toString()}&token=${token}`, '_blank')
}

const handleAdd = () => {
  Object.assign(form, {
    customer_id: '',
    receivable_id: '',
    amount: 0,
    payment_method: '',
    account_id: '',
    receipt_date: new Date().toISOString().split('T')[0],
    remark: ''
  })
  dialogVisible.value = true
}

const handleView = (row) => {
  currentRow.value = row
  viewDialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该收款记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // const res = await request.delete(`/finance/receipts/${row.id}`)
      // if (res.code === 200) {
      //   ElMessage.success('删除成功')
      //   fetchData()
      // }

      // 模拟删除
      ElMessage.success('删除成功')
      fetchData()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      // const res = await request.post('/finance/receipts', form)
      // if (res.code === 200) {
      //   ElMessage.success('创建成功')
      //   dialogVisible.value = false
      //   fetchData()
      // }

      // 模拟提交
      setTimeout(() => {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        submitLoading.value = false
        fetchData()
      }, 500)
    } catch (error) {
      ElMessage.error('创建失败')
      submitLoading.value = false
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.receipt-page {
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

  .positive {
    color: #67c23a;
    font-weight: bold;
  }
}
</style>
