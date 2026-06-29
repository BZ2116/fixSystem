<template>
  <div class="reconciliation-page">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- Tab 1: 客户对账 -->
      <el-tab-pane label="客户对账" name="customer">
        <div class="filter-bar">
          <el-date-picker
            v-model="customerFilter.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 300px; margin-right: 10px"
          />
          <el-input
            v-model="customerFilter.keyword"
            placeholder="客户名称/编号"
            clearable
            style="width: 200px; margin-right: 10px"
          />
          <el-button type="primary" @click="searchCustomer">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </div>

        <el-table :data="customerList" v-loading="customerLoading" border stripe>
          <el-table-column prop="customer_name" label="客户名称" min-width="150" />
          <el-table-column prop="total_receivable" label="应收总额" width="120" align="right">
            <template #default="{ row }">
              <span class="text-primary">¥{{ formatMoney(row.total_receivable) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_received" label="已收总额" width="120" align="right">
            <template #default="{ row }">
              <span class="text-success">¥{{ formatMoney(row.total_received) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_remaining" label="未收总额" width="120" align="right">
            <template #default="{ row }">
              <span class="text-danger">¥{{ formatMoney(row.total_remaining) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="receivable_count" label="应收笔数" width="100" align="center" />
          <el-table-column prop="received_count" label="已结清笔数" width="110" align="center" />
          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="viewCustomerDetail(row)">查看明细</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination">
          <el-pagination
            v-model:current-page="customerPagination.page"
            v-model:page-size="customerPagination.pageSize"
            :total="customerPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadCustomerList"
            @current-change="loadCustomerList"
          />
        </div>
      </el-tab-pane>

      <!-- Tab 2: 供应商对账 -->
      <el-tab-pane label="供应商对账" name="supplier">
        <div class="filter-bar">
          <el-date-picker
            v-model="supplierFilter.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 300px; margin-right: 10px"
          />
          <el-input
            v-model="supplierFilter.keyword"
            placeholder="供应商名称/编号"
            clearable
            style="width: 200px; margin-right: 10px"
          />
          <el-button type="primary" @click="searchSupplier">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </div>

        <el-table :data="supplierList" v-loading="supplierLoading" border stripe>
          <el-table-column prop="supplier_name" label="供应商名称" min-width="150" />
          <el-table-column prop="total_payable" label="应付总额" width="120" align="right">
            <template #default="{ row }">
              <span class="text-primary">¥{{ formatMoney(row.total_payable) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_paid" label="已付总额" width="120" align="right">
            <template #default="{ row }">
              <span class="text-success">¥{{ formatMoney(row.total_paid) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_remaining" label="未付总额" width="120" align="right">
            <template #default="{ row }">
              <span class="text-danger">¥{{ formatMoney(row.total_remaining) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="payable_count" label="应付笔数" width="100" align="center" />
          <el-table-column prop="paid_count" label="已结清笔数" width="110" align="center" />
          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="viewSupplierDetail(row)">查看明细</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination">
          <el-pagination
            v-model:current-page="supplierPagination.page"
            v-model:page-size="supplierPagination.pageSize"
            :total="supplierPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadSupplierList"
            @current-change="loadSupplierList"
          />
        </div>
      </el-tab-pane>

      <!-- Tab 3: 账户对账 -->
      <el-tab-pane label="账户对账" name="account">
        <div class="filter-bar">
          <el-date-picker
            v-model="accountFilter.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 300px; margin-right: 10px"
          />
          <el-button type="primary" @click="searchAccount">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </div>

        <el-table :data="accountList" v-loading="accountLoading" border stripe>
          <el-table-column prop="account_name" label="账户名称" min-width="150" />
          <el-table-column prop="account_type" label="账户类型" width="120">
            <template #default="{ row }">
              {{ getAccountTypeName(row.account_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="opening_balance" label="期初余额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.opening_balance) }}
            </template>
          </el-table-column>
          <el-table-column prop="total_income" label="本期收入" width="120" align="right">
            <template #default="{ row }">
              <span class="text-success">¥{{ formatMoney(row.total_income) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_expense" label="本期支出" width="120" align="right">
            <template #default="{ row }">
              <span class="text-danger">¥{{ formatMoney(row.total_expense) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="closing_balance" label="期末余额" width="120" align="right">
            <template #default="{ row }">
              <span class="text-primary">¥{{ formatMoney(row.closing_balance) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="viewAccountDetail(row)">查看明细</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination">
          <el-pagination
            v-model:current-page="accountPagination.page"
            v-model:page-size="accountPagination.pageSize"
            :total="accountPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadAccountList"
            @current-change="loadAccountList"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 客户明细对话框 -->
    <el-dialog
      v-model="customerDetailVisible"
      title="客户对账明细"
      width="900px"
      destroy-on-close
    >
      <template v-if="customerDetail">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="客户名称">{{ customerDetail.customer_info?.name }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ customerDetail.customer_info?.contact }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ customerDetail.customer_info?.phone }}</el-descriptions-item>
          <el-descriptions-item label="对账期间" :span="3">
            {{ customerDetail.period?.start }} 至 {{ customerDetail.period?.end }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="summary-cards">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="summary-card">
                <div class="label">应收总额</div>
                <div class="value text-primary">¥{{ formatMoney(customerDetail.summary?.total_receivable) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-card income">
                <div class="label">已收总额</div>
                <div class="value">¥{{ formatMoney(customerDetail.summary?.total_received) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-card expense">
                <div class="label">未收总额</div>
                <div class="value">¥{{ formatMoney(customerDetail.summary?.total_remaining) }}</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="section-title">应收明细</div>
        <el-table :data="customerDetail.details" border stripe max-height="200">
          <el-table-column prop="receivable_no" label="应收编号" width="150" />
          <el-table-column prop="related_no" label="关联单号" width="150" />
          <el-table-column prop="amount" label="应收金额" width="100" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="received_amount" label="已收金额" width="100" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.received_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="remaining_amount" label="未收金额" width="100" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.remaining_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === '已结清' ? 'success' : 'warning'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160" />
        </el-table>

        <div class="section-title">收款记录</div>
        <el-table :data="customerDetail.records" border stripe max-height="200">
          <el-table-column prop="record_no" label="流水号" width="150" />
          <el-table-column prop="amount" label="收款金额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="account_name" label="收款账户" width="150" />
          <el-table-column prop="received_at" label="收款时间" width="160" />
          <el-table-column prop="remark" label="备注" min-width="150" />
        </el-table>
      </template>

      <template #footer>
        <el-button @click="customerDetailVisible = false">关闭</el-button>
        <el-button type="primary" @click="printCustomerDetail">打印</el-button>
        <el-button type="success" @click="exportCustomerDetail">导出</el-button>
      </template>
    </el-dialog>

    <!-- 打印对话框 -->
    <PrintDialog v-model:visible="printDialogVisible" :template-type="printTemplateType" :print-data="printData" />

    <!-- 供应商明细对话框 -->
    <el-dialog
      v-model="supplierDetailVisible"
      title="供应商对账明细"
      width="900px"
      destroy-on-close
    >
      <template v-if="supplierDetail">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="供应商名称">{{ supplierDetail.supplier_info?.name }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ supplierDetail.supplier_info?.contact }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ supplierDetail.supplier_info?.phone }}</el-descriptions-item>
          <el-descriptions-item label="对账期间" :span="3">
            {{ supplierDetail.period?.start }} 至 {{ supplierDetail.period?.end }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="summary-cards">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="summary-card">
                <div class="label">应付总额</div>
                <div class="value text-primary">¥{{ formatMoney(supplierDetail.summary?.total_payable) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-card income">
                <div class="label">已付总额</div>
                <div class="value">¥{{ formatMoney(supplierDetail.summary?.total_paid) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-card expense">
                <div class="label">未付总额</div>
                <div class="value">¥{{ formatMoney(supplierDetail.summary?.total_remaining) }}</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="section-title">应付明细</div>
        <el-table :data="supplierDetail.details" border stripe max-height="200">
          <el-table-column prop="payable_no" label="应付编号" width="150" />
          <el-table-column prop="related_no" label="关联单号" width="150" />
          <el-table-column prop="amount" label="应付金额" width="100" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="paid_amount" label="已付金额" width="100" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.paid_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="remaining_amount" label="未付金额" width="100" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.remaining_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === '已结清' ? 'success' : 'warning'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160" />
        </el-table>

        <div class="section-title">付款记录</div>
        <el-table :data="supplierDetail.records" border stripe max-height="200">
          <el-table-column prop="record_no" label="流水号" width="150" />
          <el-table-column prop="amount" label="付款金额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="account_name" label="付款账户" width="150" />
          <el-table-column prop="paid_at" label="付款时间" width="160" />
          <el-table-column prop="remark" label="备注" min-width="150" />
        </el-table>
      </template>

      <template #footer>
        <el-button @click="supplierDetailVisible = false">关闭</el-button>
        <el-button type="primary" @click="printSupplierDetail">打印</el-button>
        <el-button type="success" @click="exportSupplierDetail">导出</el-button>
      </template>
    </el-dialog>

    <!-- 账户明细对话框 -->
    <el-dialog
      v-model="accountDetailVisible"
      title="账户对账明细"
      width="900px"
      destroy-on-close
    >
      <template v-if="accountDetail">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="账户名称">{{ accountDetail.account_info?.name }}</el-descriptions-item>
          <el-descriptions-item label="账户类型">{{ getAccountTypeName(accountDetail.account_info?.type) }}</el-descriptions-item>
          <el-descriptions-item label="账户编号">{{ accountDetail.account_info?.account_no }}</el-descriptions-item>
          <el-descriptions-item label="对账期间" :span="3">
            {{ accountDetail.period?.start }} 至 {{ accountDetail.period?.end }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="summary-cards">
          <el-row :gutter="15">
            <el-col :span="6">
              <div class="summary-card">
                <div class="label">期初余额</div>
                <div class="value">¥{{ formatMoney(accountDetail.opening_balance) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card income">
                <div class="label">本期收入</div>
                <div class="value">¥{{ formatMoney(accountDetail.total_income) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card expense">
                <div class="label">本期支出</div>
                <div class="value">¥{{ formatMoney(accountDetail.total_expense) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card balance">
                <div class="label">期末余额</div>
                <div class="value">¥{{ formatMoney(accountDetail.closing_balance) }}</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="section-title">流水明细</div>
        <el-table :data="accountDetail.records" border stripe max-height="300">
          <el-table-column prop="type" label="类型" width="80">
            <template #default="{ row }">
              <el-tag :type="row.type === '收入' ? 'success' : 'danger'">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="100" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="before_balance" label="变动前余额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.before_balance) }}
            </template>
          </el-table-column>
          <el-table-column prop="after_balance" label="变动后余额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ formatMoney(row.after_balance) }}
            </template>
          </el-table-column>
          <el-table-column prop="related_type" label="关联类型" width="100" />
          <el-table-column prop="related_no" label="关联单号" width="130" />
          <el-table-column prop="remark" label="备注" min-width="120" />
          <el-table-column prop="created_at" label="时间" width="160" />
        </el-table>
      </template>

      <template #footer>
        <el-button @click="accountDetailVisible = false">关闭</el-button>
        <el-button type="primary" @click="printAccountDetail">打印</el-button>
        <el-button type="success" @click="exportAccountDetail">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import PrintDialog from '@/components/PrintDialog.vue'
import {
  getCustomerReconciliation,
  getCustomerReconciliationList,
  getSupplierReconciliation,
  getSupplierReconciliationList,
  getAccountReconciliation,
  getAccountReconciliationList
} from '@/api/reconciliation'

// Tab状态
const activeTab = ref('customer')

// 客户对账
const customerFilter = reactive({
  dateRange: [],
  keyword: ''
})
const customerList = ref([])
const customerLoading = ref(false)
const customerPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})
const customerDetailVisible = ref(false)
const customerDetail = ref(null)

// 供应商对账
const supplierFilter = reactive({
  dateRange: [],
  keyword: ''
})
const supplierList = ref([])
const supplierLoading = ref(false)
const supplierPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})
const supplierDetailVisible = ref(false)
const supplierDetail = ref(null)

// 账户对账
const accountFilter = reactive({
  dateRange: []
})
const accountList = ref([])
const accountLoading = ref(false)
const accountPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})
const accountDetailVisible = ref(false)
const accountDetail = ref(null)

// 打印相关
const printDialogVisible = ref(false)
const printTemplateType = ref('')
const printData = ref({})

// 账户类型映射
const accountTypeMap = {
  cash: '现金账户',
  bank: '银行账户',
  alipay: '支付宝',
  wechat: '微信',
  other: '其他'
}

// 格式化金额
const formatMoney = (value) => {
  if (value === null || value === undefined) return '0.00'
  return Number(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 获取账户类型名称
const getAccountTypeName = (type) => {
  return accountTypeMap[type] || type
}

// 加载客户对账列表
const loadCustomerList = async () => {
  customerLoading.value = true
  try {
    const params = {
      page: customerPagination.page,
      page_size: customerPagination.pageSize
    }
    if (customerFilter.dateRange && customerFilter.dateRange.length === 2) {
      params.start_date = customerFilter.dateRange[0]
      params.end_date = customerFilter.dateRange[1]
    }
    if (customerFilter.keyword) {
      params.keyword = customerFilter.keyword
    }
    const res = await getCustomerReconciliationList(params)
    if (res.code === 200) {
      customerList.value = res.data.items || []
      customerPagination.total = res.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载客户对账数据失败')
  } finally {
    customerLoading.value = false
  }
}

// 搜索客户
const searchCustomer = () => {
  customerPagination.page = 1
  loadCustomerList()
}

// 查看客户明细
const viewCustomerDetail = async (row) => {
  try {
    const params = { customer_id: row.customer_id }
    if (customerFilter.dateRange && customerFilter.dateRange.length === 2) {
      params.start_date = customerFilter.dateRange[0]
      params.end_date = customerFilter.dateRange[1]
    }
    const res = await getCustomerReconciliationList(params)
    if (res.code === 200) {
      customerDetail.value = res.data
      customerDetailVisible.value = true
    }
  } catch (error) {
    ElMessage.error('加载客户明细失败')
  }
}

// 加载供应商对账列表
const loadSupplierList = async () => {
  supplierLoading.value = true
  try {
    const params = {
      page: supplierPagination.page,
      page_size: supplierPagination.pageSize
    }
    if (supplierFilter.dateRange && supplierFilter.dateRange.length === 2) {
      params.start_date = supplierFilter.dateRange[0]
      params.end_date = supplierFilter.dateRange[1]
    }
    if (supplierFilter.keyword) {
      params.keyword = supplierFilter.keyword
    }
    const res = await getSupplierReconciliationList(params)
    if (res.code === 200) {
      supplierList.value = res.data.items || []
      supplierPagination.total = res.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载供应商对账数据失败')
  } finally {
    supplierLoading.value = false
  }
}

// 搜索供应商
const searchSupplier = () => {
  supplierPagination.page = 1
  loadSupplierList()
}

// 查看供应商明细
const viewSupplierDetail = async (row) => {
  try {
    const params = { supplier_id: row.supplier_id }
    if (supplierFilter.dateRange && supplierFilter.dateRange.length === 2) {
      params.start_date = supplierFilter.dateRange[0]
      params.end_date = supplierFilter.dateRange[1]
    }
    const res = await getSupplierReconciliationList(params)
    if (res.code === 200) {
      supplierDetail.value = res.data
      supplierDetailVisible.value = true
    }
  } catch (error) {
    ElMessage.error('加载供应商明细失败')
  }
}

// 加载账户对账列表
const loadAccountList = async () => {
  accountLoading.value = true
  try {
    const params = {
      page: accountPagination.page,
      page_size: accountPagination.pageSize
    }
    if (accountFilter.dateRange && accountFilter.dateRange.length === 2) {
      params.start_date = accountFilter.dateRange[0]
      params.end_date = accountFilter.dateRange[1]
    }
    const res = await getAccountReconciliation(params)
    if (res.code === 200) {
      accountList.value = res.data.items
      accountPagination.total = res.data.total
    }
  } catch (error) {
    ElMessage.error('加载账户对账数据失败')
  } finally {
    accountLoading.value = false
  }
}

// 搜索账户
const searchAccount = () => {
  accountPagination.page = 1
  loadAccountList()
}

// 查看账户明细
const viewAccountDetail = async (row) => {
  try {
    const params = { account_id: row.account_id }
    if (accountFilter.dateRange && accountFilter.dateRange.length === 2) {
      params.start_date = accountFilter.dateRange[0]
      params.end_date = accountFilter.dateRange[1]
    }
    const res = await getAccountReconciliationList(params)
    if (res.code === 200) {
      accountDetail.value = res.data
      accountDetailVisible.value = true
    }
  } catch (error) {
    ElMessage.error('加载账户明细失败')
  }
}

// 打印客户明细
const printCustomerDetail = () => {
  if (!customerDetail.value) {
    ElMessage.warning('暂无数据可打印')
    return
  }
  const d = customerDetail.value
  const info = d.customer_info || {}
  const summary = d.summary || {}

  // 构建应收明细HTML表格
  const detailsHtml = (d.details || []).length > 0
    ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:15px;">
        <thead style="background:#f5f5f5;">
          <tr>
            <th style="border:1px solid #ddd;padding:8px;">应收编号</th>
            <th style="border:1px solid #ddd;padding:8px;">关联单号</th>
            <th style="border:1px solid #ddd;padding:8px;">应收金额</th>
            <th style="border:1px solid #ddd;padding:8px;">已收金额</th>
            <th style="border:1px solid #ddd;padding:8px;">未收金额</th>
            <th style="border:1px solid #ddd;padding:8px;">状态</th>
            <th style="border:1px solid #ddd;padding:8px;">创建时间</th>
          </tr>
        </thead>
        <tbody>
          ${d.details.map(item => `
            <tr>
              <td style="border:1px solid #ddd;padding:8px;">${item.receivable_no || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.related_no || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.received_amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.remaining_amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.status || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.created_at || '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>`
    : '<p style="color:#999;">暂无应收明细</p>'

  // 构建收款记录HTML表格
  const recordsHtml = (d.records || []).length > 0
    ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:15px;">
        <thead style="background:#f5f5f5;">
          <tr>
            <th style="border:1px solid #ddd;padding:8px;">流水号</th>
            <th style="border:1px solid #ddd;padding:8px;">收款金额</th>
            <th style="border:1px solid #ddd;padding:8px;">收款账户</th>
            <th style="border:1px solid #ddd;padding:8px;">收款时间</th>
            <th style="border:1px solid #ddd;padding:8px;">备注</th>
          </tr>
        </thead>
        <tbody>
          ${d.records.map(item => `
            <tr>
              <td style="border:1px solid #ddd;padding:8px;">${item.record_no || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.account_name || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.received_at || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.remark || '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>`
    : '<p style="color:#999;">暂无收款记录</p>'

  printData.value = {
    customer_name: info.name || '-',
    contact: info.contact || '-',
    phone: info.phone || '-',
    period_start: d.period?.start || '-',
    period_end: d.period?.end || '-',
    total_receivable: formatMoney(summary.total_receivable),
    total_received: formatMoney(summary.total_received),
    total_remaining: formatMoney(summary.total_remaining),
    details_html: detailsHtml,
    records_html: recordsHtml
  }
  printTemplateType.value = 'customer_reconciliation'
  printDialogVisible.value = true
}

// 导出客户明细
const exportCustomerDetail = () => {
  if (!customerDetail.value || customerDetail.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  // 生成CSV内容
  const headers = ['日期', '单号', '类型', '应收金额', '已收金额', '余额']
  const rows = customerDetail.value.map(item => [
    item.date || '',
    item.orderNo || '',
    item.type || '',
    Number(item.receivableAmount || 0).toFixed(2),
    Number(item.receivedAmount || 0).toFixed(2),
    Number(item.balance || 0).toFixed(2)
  ])
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `客户对账单_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 打印供应商明细
const printSupplierDetail = () => {
  if (!supplierDetail.value) {
    ElMessage.warning('暂无数据可打印')
    return
  }
  const d = supplierDetail.value
  const info = d.supplier_info || {}
  const summary = d.summary || {}

  // 构建应付明细HTML表格
  const detailsHtml = (d.details || []).length > 0
    ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:15px;">
        <thead style="background:#f5f5f5;">
          <tr>
            <th style="border:1px solid #ddd;padding:8px;">应付编号</th>
            <th style="border:1px solid #ddd;padding:8px;">关联单号</th>
            <th style="border:1px solid #ddd;padding:8px;">应付金额</th>
            <th style="border:1px solid #ddd;padding:8px;">已付金额</th>
            <th style="border:1px solid #ddd;padding:8px;">未付金额</th>
            <th style="border:1px solid #ddd;padding:8px;">状态</th>
            <th style="border:1px solid #ddd;padding:8px;">创建时间</th>
          </tr>
        </thead>
        <tbody>
          ${d.details.map(item => `
            <tr>
              <td style="border:1px solid #ddd;padding:8px;">${item.payable_no || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.related_no || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.paid_amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.remaining_amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.status || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.created_at || '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>`
    : '<p style="color:#999;">暂无应付明细</p>'

  // 构建付款记录HTML表格
  const recordsHtml = (d.records || []).length > 0
    ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:15px;">
        <thead style="background:#f5f5f5;">
          <tr>
            <th style="border:1px solid #ddd;padding:8px;">流水号</th>
            <th style="border:1px solid #ddd;padding:8px;">付款金额</th>
            <th style="border:1px solid #ddd;padding:8px;">付款账户</th>
            <th style="border:1px solid #ddd;padding:8px;">付款时间</th>
            <th style="border:1px solid #ddd;padding:8px;">备注</th>
          </tr>
        </thead>
        <tbody>
          ${d.records.map(item => `
            <tr>
              <td style="border:1px solid #ddd;padding:8px;">${item.record_no || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.account_name || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.paid_at || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.remark || '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>`
    : '<p style="color:#999;">暂无付款记录</p>'

  printData.value = {
    supplier_name: info.name || '-',
    contact: info.contact || '-',
    phone: info.phone || '-',
    period_start: d.period?.start || '-',
    period_end: d.period?.end || '-',
    total_payable: formatMoney(summary.total_payable),
    total_paid: formatMoney(summary.total_paid),
    total_remaining: formatMoney(summary.total_remaining),
    details_html: detailsHtml,
    records_html: recordsHtml
  }
  printTemplateType.value = 'supplier_reconciliation'
  printDialogVisible.value = true
}

// 导出供应商明细
const exportSupplierDetail = () => {
  if (!supplierDetail.value || supplierDetail.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const headers = ['日期', '单号', '类型', '应付金额', '已付金额', '余额']
  const rows = supplierDetail.value.map(item => [
    item.date || '',
    item.orderNo || '',
    item.type || '',
    Number(item.payableAmount || 0).toFixed(2),
    Number(item.paidAmount || 0).toFixed(2),
    Number(item.balance || 0).toFixed(2)
  ])
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `供应商对账单_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 打印账户明细
const printAccountDetail = () => {
  if (!accountDetail.value) {
    ElMessage.warning('暂无数据可打印')
    return
  }
  const d = accountDetail.value
  const info = d.account_info || {}

  // 构建流水明细HTML表格
  const recordsHtml = (d.records || []).length > 0
    ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:15px;">
        <thead style="background:#f5f5f5;">
          <tr>
            <th style="border:1px solid #ddd;padding:8px;">类型</th>
            <th style="border:1px solid #ddd;padding:8px;">金额</th>
            <th style="border:1px solid #ddd;padding:8px;">变动前余额</th>
            <th style="border:1px solid #ddd;padding:8px;">变动后余额</th>
            <th style="border:1px solid #ddd;padding:8px;">关联类型</th>
            <th style="border:1px solid #ddd;padding:8px;">关联单号</th>
            <th style="border:1px solid #ddd;padding:8px;">备注</th>
            <th style="border:1px solid #ddd;padding:8px;">时间</th>
          </tr>
        </thead>
        <tbody>
          ${d.records.map(item => `
            <tr>
              <td style="border:1px solid #ddd;padding:8px;">${item.type || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.amount)}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.before_balance)}</td>
              <td style="border:1px solid #ddd;padding:8px;text-align:right;">¥${formatMoney(item.after_balance)}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.related_type || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.related_no || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.remark || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.created_at || '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>`
    : '<p style="color:#999;">暂无流水明细</p>'

  printData.value = {
    account_name: info.name || '-',
    account_type: getAccountTypeName(info.type),
    account_no: info.account_no || '-',
    period_start: d.period?.start || '-',
    period_end: d.period?.end || '-',
    opening_balance: formatMoney(d.opening_balance),
    total_income: formatMoney(d.total_income),
    total_expense: formatMoney(d.total_expense),
    closing_balance: formatMoney(d.closing_balance),
    records_html: recordsHtml
  }
  printTemplateType.value = 'account_reconciliation'
  printDialogVisible.value = true
}

// 导出账户明细
const exportAccountDetail = () => {
  if (!accountDetail.value || accountDetail.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const headers = ['日期', '类型', '收入', '支出', '余额', '备注']
  const rows = accountDetail.value.map(item => [
    item.date || '',
    item.type || '',
    Number(item.income || 0).toFixed(2),
    Number(item.expense || 0).toFixed(2),
    Number(item.balance || 0).toFixed(2),
    item.remark || ''
  ])
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `账户对账单_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 初始化
onMounted(() => {
  loadCustomerList()
})
</script>

<style lang="scss" scoped>
.reconciliation-page {
  .filter-bar {
    margin-bottom: 20px;
  }

  .summary-cards {
    margin-bottom: 20px;

    .summary-card {
      padding: 15px;
      background: #f5f7fa;
      border-radius: 8px;
      text-align: center;

      .label {
        font-size: 14px;
        color: #909399;
        margin-bottom: 8px;
      }

      .value {
        font-size: 24px;
        font-weight: bold;
      }

      &.income .value {
        color: #67c23a;
      }

      &.expense .value {
        color: #f56c6c;
      }

      &.balance .value {
        color: #409eff;
      }
    }
  }

  .section-title {
    font-size: 16px;
    font-weight: bold;
    margin: 20px 0 15px;
    padding-left: 10px;
    border-left: 4px solid #409eff;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .text-primary {
    color: #409eff;
  }

  .text-success {
    color: #67c23a;
  }

  .text-danger {
    color: #f56c6c;
  }
}
</style>
