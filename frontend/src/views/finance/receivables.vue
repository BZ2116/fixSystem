<template>
  <div class="receivables-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>应收管理</span>
          <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stat-row">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #409eff;">
                <el-icon><Wallet /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">应收总额</div>
                <div class="stat-value">¥{{ summaryData.total_receivable?.toFixed(2) || '0.00' }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #f56c6c;">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">逾期总额</div>
                <div class="stat-value danger">¥{{ summaryData.total_overdue?.toFixed(2) || '0.00' }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #e6a23c;">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">逾期笔数</div>
                <div class="stat-value warning">{{ summaryData.overdue_count || 0 }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #67c23a;">
                <el-icon><SuccessFilled /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">今日收款</div>
                <div class="stat-value positive">¥{{ summaryData.total_received_today?.toFixed(2) || '0.00' }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="往来单位">
          <el-select v-model="searchForm.customer_id" placeholder="选择客户" clearable filterable style="width: 180px">
            <el-option v-for="c in customerList" :key="c.id" :label="c.customer_name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="编号查询">
          <el-input v-model="searchForm.biz_no" placeholder="应收/关联单号/工单/接件" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option :label="'待收款'" :value="0" />
            <el-option :label="'部分收款'" :value="1" />
            <el-option :label="'已结清'" :value="2" />
            <el-option :label="'已取消'" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchData">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 操作按钮 -->
      <div class="toolbar">
        <el-button type="primary" :icon="Money" :disabled="selectedRows.length === 0" @click="handleBatchReceive">
          批量收款 ({{ selectedRows.length }})
        </el-button>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        stripe
        border
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" align="center" :selectable="canSelect" />
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="receivable_no" label="应收编号" width="150" />
        <el-table-column prop="related_no" label="关联单号" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleBizNoClick(row)">{{ row.related_no }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="related_type" label="关联类型" width="120" align="center">
          <template #default="{ row }">
            {{ getBizTypeText(row.related_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="total_amount" label="应收总额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ row.total_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="received_amount" label="已收金额" width="120" align="right">
          <template #default="{ row }">
            <span class="positive">¥{{ row.received_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remaining_amount" label="待收金额" width="120" align="right">
          <template #default="{ row }">
            <span class="warning">¥{{ row.remaining_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="到期日" width="110" align="center" />
        <el-table-column prop="overdue_days" label="逾期天数" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.overdue_days > 0" type="danger" size="small">逾期{{ row.overdue_days }}天</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="info" link size="small" @click="handleView(row)">详情</el-button>
            <el-button
              v-if="row.status === 0 || row.status === 1"
              type="primary"
              link
              size="small"
              @click="handleReceive(row)"
            >收款</el-button>
            <el-button type="success" link size="small" @click="handlePrint(row)">打印</el-button>
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

    <!-- 收款对话框 -->
    <el-dialog v-model="receiveDialogVisible" title="收款" width="500px" destroy-on-close>
      <el-form :model="receiveForm" :rules="receiveRules" ref="receiveFormRef" label-width="100px">
        <el-form-item label="应收编号">
          <span>{{ currentRow?.receivable_no }}</span>
        </el-form-item>
        <el-form-item label="客户名称">
          <span>{{ currentRow?.customer_name }}</span>
        </el-form-item>
        <el-form-item label="应收总额">
          <span class="amount">¥{{ currentRow?.total_amount?.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="已收金额">
          <span class="positive">¥{{ currentRow?.received_amount?.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="待收金额">
          <span class="warning">¥{{ currentRow?.remaining_amount?.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="收款账户">
          <el-select v-model="receiveForm.account_id" placeholder="请选择收款账户" clearable style="width: 100%">
            <el-option
              v-for="item in accountList"
              :key="item.id"
              :label="item.account_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="本次收款" prop="amount">
          <el-input-number v-model="receiveForm.amount" :min="0.01" :max="currentRow?.remaining_amount || 0" :precision="2" style="width: 100%" placeholder="请输入收款金额" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="receiveForm.remark" type="textarea" :rows="3" placeholder="请输入收款备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="receiveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReceive" :loading="submitLoading">确认收款</el-button>
      </template>
    </el-dialog>

    <!-- 批量收款对话框 -->
    <el-dialog v-model="batchReceiveDialogVisible" title="批量收款" width="500px" destroy-on-close>
      <el-form :model="batchReceiveForm" ref="batchReceiveFormRef" label-width="100px">
        <el-form-item label="已选应收">
          <span>已选 <strong>{{ selectedRows.length }}</strong> 条应收</span>
        </el-form-item>
        <el-form-item label="收款账户">
          <el-select v-model="batchReceiveForm.account_id" placeholder="请选择收款账户" clearable style="width: 100%">
            <el-option
              v-for="item in accountList"
              :key="item.id"
              :label="item.account_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="统一备注">
          <el-input v-model="batchReceiveForm.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchReceiveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitBatchReceive" :loading="submitLoading">确认批量收款</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="应收详情" width="650px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="应收编号">{{ detailData?.receivable_no }}</el-descriptions-item>
        <el-descriptions-item label="关联单号">{{ detailData?.related_no }}</el-descriptions-item>
        <el-descriptions-item label="关联类型">{{ getBizTypeText(detailData?.related_type) }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ detailData?.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="应收总额">
          <span class="amount">¥{{ detailData?.total_amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="已收金额">
          <span class="positive">¥{{ detailData?.received_amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="待收金额">
          <span class="warning">¥{{ detailData?.remaining_amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(detailData?.status)" size="small">{{ getStatusText(detailData?.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="到期日">{{ detailData?.due_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="逾期天数">
          <el-tag v-if="detailData?.overdue_days > 0" type="danger" size="small">逾期{{ detailData.overdue_days }}天</el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData?.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detailData?.updated_at }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detailData?.remark || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 打印对话框 -->
    <PrintDialog v-model:visible="printDialogVisible" template-type="receivable" :print-data="printData" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download, Wallet, Warning, Clock, SuccessFilled, Money } from '@element-plus/icons-vue'
import PrintDialog from '@/components/PrintDialog.vue'
import {
  getReceivableList,
  getReceivableDetail,
  receiveReceivable,
  exportReceivables,
  batchReceiveReceivables,
  getReceivablePrintData,
  getReceivableSummary,
  getAccountList
} from '@/api/finance'
import { getCustomerList } from '@/api/customer'

const loading = ref(false)
const submitLoading = ref(false)
const printLoading = ref(false)
const tableData = ref([])
const currentRow = ref(null)
const detailData = ref(null)
const printData = ref(null)
const selectedRows = ref([])
const accountList = ref([])
const receiveDialogVisible = ref(false)
const batchReceiveDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const printDialogVisible = ref(false)
const receiveFormRef = ref(null)
const batchReceiveFormRef = ref(null)

const summaryData = reactive({
  total_receivable: 0,
  total_overdue: 0,
  overdue_count: 0,
  total_received_today: 0
})

const searchForm = reactive({
  customer_id: null,
  biz_no: '',
  status: '',
  dateRange: null
})

const customerList = ref([])

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const receiveForm = reactive({
  amount: 0,
  account_id: '',
  remark: ''
})

const batchReceiveForm = reactive({
  account_id: '',
  remark: ''
})

const receiveRules = {
  amount: [
    { required: true, message: '请输入收款金额', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '收款金额必须大于0', trigger: 'blur' }
  ]
}

const getBizTypeText = (type) => {
  const types = {
    sales: '销售单',
    sale: '销售单',
    work_order: '工单',
    workorder: '工单',
    return_sale: '销售退货',
    return_work_order: '工单退货'
  }
  return types[type] || type || ''
}

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'primary', 2: 'success', 3: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '待收款', 1: '部分收款', 2: '已结清', 3: '已取消' }
  return texts[status] || (status ?? '')
}

const canSelect = (row) => {
  return row.status === 0 || row.status === 1
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const fetchSummary = async () => {
  try {
    const res = await getReceivableSummary()
    if (res.code === 200) {
      Object.assign(summaryData, res.data)
    }
  } catch (error) {
    console.error('获取统计汇总失败:', error)
  }
}

const fetchAccountList = async () => {
  try {
    const res = await getAccountList()
    if (res.code === 200) {
      accountList.value = res.data || []
    }
  } catch (error) {
    console.error('获取账户列表失败:', error)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      customer_id: searchForm.customer_id || undefined,
      keyword: searchForm.biz_no || undefined,
      status: searchForm.status !== '' && searchForm.status !== null ? searchForm.status : undefined,
      start_date: searchForm.dateRange?.[0] || undefined,
      end_date: searchForm.dateRange?.[1] || undefined
    }
    const res = await getReceivableList(params)
    if (res.code === 200) {
      tableData.value = res.data.list || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取应收数据失败:', error)
    ElMessage.error('获取应收数据失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.customer_id = null
  searchForm.biz_no = ''
  searchForm.status = ''
  searchForm.dateRange = null
  pagination.page = 1
  fetchData()
}

// 加载客户列表
const fetchCustomerList = async () => {
  try {
    const res = await getCustomerList({ page_size: 1000 })
    if (res.code === 200) {
      customerList.value = res.data.list || []
    }
  } catch (error) {
    console.error('获取客户列表失败:', error)
  }
}

const handleBizNoClick = (row) => {
  ElMessage.info(`跳转到关联单号: ${row.related_no}`)
}

const handleView = async (row) => {
  try {
    const res = await getReceivableDetail(row.id)
    if (res.code === 200) {
      detailData.value = res.data
      detailDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取应收详情失败:', error)
    ElMessage.error('获取应收详情失败')
  }
}

const handleReceive = (row) => {
  if (row.remaining_amount <= 0) {
    ElMessage.warning('该应收已结清，无需收款')
    return
  }
  currentRow.value = row
  Object.assign(receiveForm, {
    amount: row.remaining_amount,
    account_id: '',
    remark: ''
  })
  receiveDialogVisible.value = true
}

const submitReceive = async () => {
  if (!receiveFormRef.value) return
  await receiveFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const res = await receiveReceivable(currentRow.value.id, {
        received_amount: receiveForm.amount,
        account_id: receiveForm.account_id,
        remark: receiveForm.remark
      })
      if (res.code === 200) {
        ElMessage.success('收款成功')
        receiveDialogVisible.value = false
        fetchData()
        fetchSummary()
      }
    } catch (error) {
      console.error('收款失败:', error)
      ElMessage.error('收款失败')
    } finally {
      submitLoading.value = false
    }
  })
}

const handleBatchReceive = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择需要收款的记录')
    return
  }
  Object.assign(batchReceiveForm, {
    account_id: '',
    remark: ''
  })
  batchReceiveDialogVisible.value = true
}

const submitBatchReceive = async () => {
  submitLoading.value = true
  try {
    const items = selectedRows.value.map(row => ({
      id: row.id,
      amount: row.remaining_amount
    }))
    const res = await batchReceiveReceivables({
      items,
      account_id: batchReceiveForm.account_id,
      remark: batchReceiveForm.remark
    })
    if (res.code === 200) {
      ElMessage.success('批量收款成功')
      batchReceiveDialogVisible.value = false
      fetchData()
      fetchSummary()
    }
  } catch (error) {
    console.error('批量收款失败:', error)
    ElMessage.error('批量收款失败')
  } finally {
    submitLoading.value = false
  }
}

const handlePrint = async (row) => {
  printLoading.value = true
  try {
    const res = await getReceivablePrintData(row.id)
    if (res.code === 200) {
      const data = res.data
      // 构建收款记录HTML表格
      const records = data.records || []
      const recordsHtml = records.length > 0
        ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead style="background:#f5f5f5;">
              <tr>
                <th style="border:1px solid #ddd;padding:8px;">序号</th>
                <th style="border:1px solid #ddd;padding:8px;">收款金额</th>
                <th style="border:1px solid #ddd;padding:8px;">收款账户</th>
                <th style="border:1px solid #ddd;padding:8px;">备注</th>
                <th style="border:1px solid #ddd;padding:8px;">收款时间</th>
              </tr>
            </thead>
            <tbody>
              ${records.map((r, i) => `
                <tr>
                  <td style="border:1px solid #ddd;padding:8px;text-align:center;">${i + 1}</td>
                  <td style="border:1px solid #ddd;padding:8px;text-align:right;color:#67c23a;font-weight:bold;">¥${Number(r.received_amount || 0).toFixed(2)}</td>
                  <td style="border:1px solid #ddd;padding:8px;">${r.account_name || '-'}</td>
                  <td style="border:1px solid #ddd;padding:8px;">${r.remark || '-'}</td>
                  <td style="border:1px solid #ddd;padding:8px;">${r.created_at || '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>`
        : '<p style="color:#999;">暂无收款记录</p>'

      printData.value = {
        receivable_no: data.receivable?.receivable_no || row.receivable_no || '',
        customer_name: data.receivable?.customer_name || row.customer_name || '',
        related_no: data.receivable?.related_no || row.related_no || '',
        related_type: getBizTypeText(data.receivable?.related_type || row.related_type),
        total_amount: Number(data.receivable?.total_amount || row.total_amount || 0).toFixed(2),
        received_amount: Number(data.receivable?.received_amount || row.received_amount || 0).toFixed(2),
        remaining_amount: Number(data.receivable?.remaining_amount || row.remaining_amount || 0).toFixed(2),
        overdue_days: data.overdue_days || row.overdue_days || 0,
        due_date: data.receivable?.due_date || row.due_date || '-',
        status: getStatusText(data.receivable?.status ?? row.status),
        company_name: data.company_info?.name || '',
        company_phone: data.company_info?.phone || '',
        company_address: data.company_info?.address || '',
        records_detail: recordsHtml
      }
      printDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取打印数据失败:', error)
    ElMessage.error('获取打印数据失败')
  } finally {
    printLoading.value = false
  }
}

const handleExport = async () => {
  try {
    const res = await exportReceivables()
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '应收账款列表.xlsx'
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchData()
  fetchSummary()
  fetchAccountList()
  fetchCustomerList()
})
</script>

<style lang="scss" scoped>
.receivables-page {
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

  .positive {
    color: #67c23a;
    font-weight: bold;
  }

  .warning {
    color: #e6a23c;
    font-weight: bold;
  }

  .danger {
    color: #f56c6c;
    font-weight: bold;
  }

  .print-section {
    margin-bottom: 20px;

    h4 {
      margin-bottom: 10px;
      color: #303133;
    }
  }
}
</style>
