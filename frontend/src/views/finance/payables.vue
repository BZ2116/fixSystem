<template>
  <div class="payables-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>应付管理</span>
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
                <div class="stat-label">应付总额</div>
                <div class="stat-value">¥{{ summaryData.total_payable?.toFixed(2) || '0.00' }}</div>
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
                <div class="stat-label">今日付款</div>
                <div class="stat-value positive">¥{{ summaryData.total_paid_today?.toFixed(2) || '0.00' }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="往来单位">
          <el-select v-model="searchForm.supplier_id" placeholder="选择供应商" clearable filterable style="width: 180px">
            <el-option v-for="s in supplierList" :key="s.id" :label="s.supplier_name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="编号查询">
          <el-input v-model="searchForm.biz_no" placeholder="应付/关联单号/工单/接件" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option :label="'待付款'" :value="0" />
            <el-option :label="'部分付款'" :value="1" />
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
        <el-button type="primary" :icon="Money" :disabled="selectedRows.length === 0" @click="handleBatchPay">
          批量付款 ({{ selectedRows.length }})
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
        <el-table-column prop="payable_no" label="应付编号" width="150" />
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
        <el-table-column prop="supplier_name" label="供应商名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="total_amount" label="应付总额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ row.total_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="paid_amount" label="已付金额" width="120" align="right">
          <template #default="{ row }">
            <span class="positive">¥{{ row.paid_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remaining_amount" label="待付金额" width="120" align="right">
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
              @click="handlePay(row)"
            >付款</el-button>
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

    <!-- 付款对话框 -->
    <el-dialog v-model="payDialogVisible" title="付款" width="500px" destroy-on-close>
      <el-form :model="payForm" :rules="payRules" ref="payFormRef" label-width="100px">
        <el-form-item label="应付编号">
          <span>{{ currentRow?.payable_no }}</span>
        </el-form-item>
        <el-form-item label="供应商名称">
          <span>{{ currentRow?.supplier_name }}</span>
        </el-form-item>
        <el-form-item label="应付总额">
          <span class="amount">¥{{ currentRow?.total_amount?.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="已付金额">
          <span class="positive">¥{{ currentRow?.paid_amount?.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="待付金额">
          <span class="warning">¥{{ currentRow?.remaining_amount?.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="付款账户">
          <el-select v-model="payForm.account_id" placeholder="请选择付款账户" clearable style="width: 100%">
            <el-option
              v-for="item in accountList"
              :key="item.id"
              :label="item.account_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="本次付款" prop="amount">
          <el-input-number v-model="payForm.amount" :min="0.01" :max="currentRow?.remaining_amount || 0" :precision="2" style="width: 100%" placeholder="请输入付款金额" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="payForm.remark" type="textarea" :rows="3" placeholder="请输入付款备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPay" :loading="submitLoading">确认付款</el-button>
      </template>
    </el-dialog>

    <!-- 批量付款对话框 -->
    <el-dialog v-model="batchPayDialogVisible" title="批量付款" width="500px" destroy-on-close>
      <el-form :model="batchPayForm" ref="batchPayFormRef" label-width="100px">
        <el-form-item label="已选应付">
          <span>已选 <strong>{{ selectedRows.length }}</strong> 条应付</span>
        </el-form-item>
        <el-form-item label="付款账户">
          <el-select v-model="batchPayForm.account_id" placeholder="请选择付款账户" clearable style="width: 100%">
            <el-option
              v-for="item in accountList"
              :key="item.id"
              :label="item.account_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="统一备注">
          <el-input v-model="batchPayForm.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchPayDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitBatchPay" :loading="submitLoading">确认批量付款</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="应付详情" width="650px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="应付编号">{{ detailData?.payable_no }}</el-descriptions-item>
        <el-descriptions-item label="关联单号">{{ detailData?.related_no }}</el-descriptions-item>
        <el-descriptions-item label="关联类型">{{ getBizTypeText(detailData?.related_type) }}</el-descriptions-item>
        <el-descriptions-item label="供应商名称">{{ detailData?.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="应付总额">
          <span class="amount">¥{{ detailData?.total_amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="已付金额">
          <span class="positive">¥{{ detailData?.paid_amount?.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="待付金额">
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
    <PrintDialog v-model:visible="printDialogVisible" template-type="payable" :print-data="printData" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download, Wallet, Warning, Clock, SuccessFilled, Money } from '@element-plus/icons-vue'
import PrintDialog from '@/components/PrintDialog.vue'
import {
  getPayableList,
  getPayableDetail,
  payPayable,
  exportPayables,
  batchPayPayables,
  getPayablePrintData,
  getPayableSummary,
  getAccountList
} from '@/api/finance'
import { getSupplierList } from '@/api/supplier'

const loading = ref(false)
const submitLoading = ref(false)
const printLoading = ref(false)
const tableData = ref([])
const currentRow = ref(null)
const detailData = ref(null)
const printData = ref(null)
const selectedRows = ref([])
const accountList = ref([])
const payDialogVisible = ref(false)
const batchPayDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const printDialogVisible = ref(false)
const payFormRef = ref(null)
const batchPayFormRef = ref(null)

const summaryData = reactive({
  total_payable: 0,
  total_overdue: 0,
  overdue_count: 0,
  total_paid_today: 0
})

const searchForm = reactive({
  supplier_id: null,
  biz_no: '',
  status: '',
  dateRange: null
})

const supplierList = ref([])

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const payForm = reactive({
  amount: 0,
  account_id: '',
  remark: ''
})

const batchPayForm = reactive({
  account_id: '',
  remark: ''
})

const payRules = {
  amount: [
    { required: true, message: '请输入付款金额', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '付款金额必须大于0', trigger: 'blur' }
  ]
}

const getBizTypeText = (type) => {
  const types = {
    purchase: '采购单',
    work_order: '工单',
    workorder: '工单',
    return_purchase: '采购退货',
    return_work_order: '工单退货'
  }
  return types[type] || type || ''
}

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'primary', 2: 'success', 3: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '待付款', 1: '部分付款', 2: '已结清', 3: '已取消' }
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
    const res = await getPayableSummary()
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
      supplier_id: searchForm.supplier_id || undefined,
      keyword: searchForm.biz_no || undefined,
      status: searchForm.status !== '' && searchForm.status !== null ? searchForm.status : undefined,
      start_date: searchForm.dateRange?.[0] || undefined,
      end_date: searchForm.dateRange?.[1] || undefined
    }
    const res = await getPayableList(params)
    if (res.code === 200) {
      tableData.value = res.data.list || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取应付数据失败:', error)
    ElMessage.error('获取应付数据失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.supplier_id = null
  searchForm.biz_no = ''
  searchForm.status = ''
  searchForm.dateRange = null
  pagination.page = 1
  fetchData()
}

// 加载供应商列表
const fetchSupplierList = async () => {
  try {
    const res = await getSupplierList({ page_size: 1000 })
    if (res.code === 200) {
      supplierList.value = res.data.list || []
    }
  } catch (error) {
    console.error('获取供应商列表失败:', error)
  }
}

const handleBizNoClick = (row) => {
  ElMessage.info(`跳转到关联单号: ${row.related_no}`)
}

const handleView = async (row) => {
  try {
    const res = await getPayableDetail(row.id)
    if (res.code === 200) {
      detailData.value = res.data
      detailDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取应付详情失败:', error)
    ElMessage.error('获取应付详情失败')
  }
}

const handlePay = (row) => {
  if (row.remaining_amount <= 0) {
    ElMessage.warning('该应付已结清，无需付款')
    return
  }
  currentRow.value = row
  Object.assign(payForm, {
    amount: row.remaining_amount,
    account_id: '',
    remark: ''
  })
  payDialogVisible.value = true
}

const submitPay = async () => {
  if (!payFormRef.value) return
  await payFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const res = await payPayable(currentRow.value.id, {
        paid_amount: payForm.amount,
        account_id: payForm.account_id,
        remark: payForm.remark
      })
      if (res.code === 200) {
        ElMessage.success('付款成功')
        payDialogVisible.value = false
        fetchData()
        fetchSummary()
      }
    } catch (error) {
      console.error('付款失败:', error)
      ElMessage.error('付款失败')
    } finally {
      submitLoading.value = false
    }
  })
}

const handleBatchPay = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择需要付款的记录')
    return
  }
  Object.assign(batchPayForm, {
    account_id: '',
    remark: ''
  })
  batchPayDialogVisible.value = true
}

const submitBatchPay = async () => {
  submitLoading.value = true
  try {
    const items = selectedRows.value.map(row => ({
      id: row.id,
      amount: row.remaining_amount
    }))
    const res = await batchPayPayables({
      items,
      account_id: batchPayForm.account_id,
      remark: batchPayForm.remark
    })
    if (res.code === 200) {
      ElMessage.success('批量付款成功')
      batchPayDialogVisible.value = false
      fetchData()
      fetchSummary()
    }
  } catch (error) {
    console.error('批量付款失败:', error)
    ElMessage.error('批量付款失败')
  } finally {
    submitLoading.value = false
  }
}

const handlePrint = async (row) => {
  printLoading.value = true
  try {
    const res = await getPayablePrintData(row.id)
    if (res.code === 200) {
      const data = res.data
      // 构建付款记录HTML表格
      const records = data.records || []
      const recordsHtml = records.length > 0
        ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead style="background:#f5f5f5;">
              <tr>
                <th style="border:1px solid #ddd;padding:8px;">序号</th>
                <th style="border:1px solid #ddd;padding:8px;">付款金额</th>
                <th style="border:1px solid #ddd;padding:8px;">付款账户</th>
                <th style="border:1px solid #ddd;padding:8px;">备注</th>
                <th style="border:1px solid #ddd;padding:8px;">付款时间</th>
              </tr>
            </thead>
            <tbody>
              ${records.map((r, i) => `
                <tr>
                  <td style="border:1px solid #ddd;padding:8px;text-align:center;">${i + 1}</td>
                  <td style="border:1px solid #ddd;padding:8px;text-align:right;color:#67c23a;font-weight:bold;">¥${Number(r.paid_amount || 0).toFixed(2)}</td>
                  <td style="border:1px solid #ddd;padding:8px;">${r.account_name || '-'}</td>
                  <td style="border:1px solid #ddd;padding:8px;">${r.remark || '-'}</td>
                  <td style="border:1px solid #ddd;padding:8px;">${r.created_at || '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>`
        : '<p style="color:#999;">暂无付款记录</p>'

      printData.value = {
        payable_no: data.payable?.payable_no || row.payable_no || '',
        supplier_name: data.payable?.supplier_name || row.supplier_name || '',
        related_no: data.payable?.related_no || row.related_no || '',
        related_type: getBizTypeText(data.payable?.related_type || row.related_type),
        total_amount: Number(data.payable?.total_amount || row.total_amount || 0).toFixed(2),
        paid_amount: Number(data.payable?.paid_amount || row.paid_amount || 0).toFixed(2),
        remaining_amount: Number(data.payable?.remaining_amount || row.remaining_amount || 0).toFixed(2),
        overdue_days: data.overdue_days || row.overdue_days || 0,
        due_date: data.payable?.due_date || row.due_date || '-',
        status: getStatusText(data.payable?.status ?? row.status),
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
    const res = await exportPayables()
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '应付账款列表.xlsx'
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
  fetchSupplierList()
})
</script>

<style lang="scss" scoped>
.payables-page {
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
