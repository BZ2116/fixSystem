<template>
  <div class="payment-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>付款管理</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增付款</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="供应商">
          <el-input v-model="searchForm.supplier" placeholder="供应商名称" clearable />
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
        <el-table-column prop="related_no" label="付款单号" width="180" />
        <el-table-column prop="supplier_name" label="供应商" min-width="150">
          <template #default="{ row }">
            {{ row.supplier_name || '没有数据' }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="付款金额" width="120" align="right">
          <template #default="{ row }">
            <span class="negative">¥{{ Number(row.amount || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="account_name" label="付款账户" min-width="150">
          <template #default="{ row }">
            {{ row.account_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="付款日期" width="160">
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

    <!-- 新增/编辑付款弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增付款" width="500px" destroy-on-close>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="供应商" prop="supplier_id">
          <el-select v-model="form.supplier_id" placeholder="选择供应商" style="width: 100%" filterable>
            <el-option v-for="s in supplierList" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联应付" prop="payable_id">
          <el-select v-model="form.payable_id" placeholder="选择关联应付单" style="width: 100%" clearable>
            <el-option v-for="p in payableList" :key="p.id" :label="p.biz_no" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="付款金额" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="付款方式" prop="payment_method">
          <el-select v-model="form.payment_method" placeholder="选择付款方式" style="width: 100%">
            <el-option label="现金" value="cash" />
            <el-option label="银行转账" value="bank" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信" value="wechat" />
          </el-select>
        </el-form-item>
        <el-form-item label="付款账户" prop="account_id">
          <el-select v-model="form.account_id" placeholder="选择付款账户" style="width: 100%">
            <el-option v-for="a in accountList" :key="a.id" :label="a.account_name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="付款日期" prop="payment_date">
          <el-date-picker v-model="form.payment_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
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
    <el-dialog v-model="viewDialogVisible" title="付款详情" width="600px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="付款单号">{{ currentRow?.payment_no }}</el-descriptions-item>
        <el-descriptions-item label="供应商">{{ currentRow?.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="付款金额">
          <span class="negative">¥{{ currentRow?.amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="付款方式">{{ getPaymentMethodText(currentRow?.payment_method) }}</el-descriptions-item>
        <el-descriptions-item label="付款账户">{{ currentRow?.account_name }}</el-descriptions-item>
        <el-descriptions-item label="付款日期">{{ currentRow?.payment_date }}</el-descriptions-item>
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
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const accountList = ref([])
const supplierList = ref([])
const payableList = ref([])
const currentRow = ref(null)
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const formRef = ref(null)

const searchForm = reactive({
  supplier: '',
  date_range: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  supplier_id: '',
  payable_id: '',
  amount: 0,
  payment_method: '',
  account_id: '',
  payment_date: new Date().toISOString().split('T')[0],
  remark: ''
})

const rules = {
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  amount: [{ required: true, message: '请输入付款金额', trigger: 'blur' }],
  payment_method: [{ required: true, message: '请选择付款方式', trigger: 'change' }],
  account_id: [{ required: true, message: '请选择付款账户', trigger: 'change' }],
  payment_date: [{ required: true, message: '请选择付款日期', trigger: 'change' }]
}

// 模拟数据
const mockData = [
  { id: 1, payment_no: 'PM2024001', supplier_name: '供应商A', amount: 50000, payment_method: 'bank', account_name: '中国银行', payment_date: '2024-01-20', operator_name: '张三', remark: '货款', created_at: '2024-01-20 10:30:00' },
  { id: 2, payment_no: 'PM2024002', supplier_name: '供应商B', amount: 60000, payment_method: 'bank', account_name: '工商银行', payment_date: '2024-01-18', operator_name: '李四', remark: '', created_at: '2024-01-18 14:20:00' },
  { id: 3, payment_no: 'PM2024003', supplier_name: '供应商C', amount: 80000, payment_method: 'alipay', account_name: '支付宝', payment_date: '2024-01-15', operator_name: '张三', remark: '预付款', created_at: '2024-01-15 09:15:00' },
  { id: 4, payment_no: 'PM2024004', supplier_name: '供应商A', amount: 25000, payment_method: 'cash', account_name: '现金', payment_date: '2024-01-12', operator_name: '王五', remark: '', created_at: '2024-01-12 16:45:00' },
  { id: 5, payment_no: 'PM2024005', supplier_name: '供应商D', amount: 40000, payment_method: 'bank', account_name: '建设银行', payment_date: '2024-01-10', operator_name: '李四', remark: '尾款', created_at: '2024-01-10 11:00:00' }
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
        record_type: 2, // 支出
        keyword: searchForm.supplier,
        start_date: searchForm.date_range?.[0],
        end_date: searchForm.date_range?.[1]
      }
    })
    if (res.code === 200) {
      tableData.value = res.data.list || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取付款数据失败:', error)
    ElMessage.error('获取付款数据失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.supplier = ''
  searchForm.date_range = null
  pagination.page = 1
  fetchData()
}

const handleAdd = () => {
  Object.assign(form, {
    supplier_id: '',
    payable_id: '',
    amount: 0,
    payment_method: '',
    account_id: '',
    payment_date: new Date().toISOString().split('T')[0],
    remark: ''
  })
  dialogVisible.value = true
}

const handleView = (row) => {
  currentRow.value = row
  viewDialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该付款记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // const res = await request.delete(`/finance/payments/${row.id}`)
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
      // const res = await request.post('/finance/payments', form)
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
.payment-page {
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

  .negative {
    color: #f56c6c;
    font-weight: bold;
  }
}
</style>
