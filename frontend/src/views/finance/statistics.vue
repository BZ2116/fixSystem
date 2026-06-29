<template>
  <div class="statistics-page">
    <!-- 顶部筛选栏 -->
    <el-form :inline="true" class="filter-bar">
      <el-form-item label="开始日期">
        <el-date-picker
          v-model="filter.startDate"
          type="date"
          placeholder="选择开始日期"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      <el-form-item label="结束日期">
        <el-date-picker
          v-model="filter.endDate"
          type="date"
          placeholder="选择结束日期"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- Tab 1: 营收统计 -->
      <el-tab-pane label="营收统计" name="revenue">
        <!-- 汇总卡片 -->
        <el-row :gutter="20" class="stat-row">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #409eff;">
                  <el-icon><Money /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">销售总额</div>
                  <div class="stat-value">{{ revenueData.summary.salesAmount || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #67c23a;">
                  <el-icon><DocumentChecked /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">工单总额</div>
                  <div class="stat-value">{{ revenueData.summary.workOrderAmount || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #8e44ad;">
                  <el-icon><TrendCharts /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">总营收</div>
                  <div class="stat-value">{{ revenueData.summary.totalRevenue || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #e6a23c;">
                  <el-icon><CircleCheck /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">已回款</div>
                  <div class="stat-value">{{ revenueData.summary.receivedAmount || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 趋势图表 -->
        <div class="chart-area">图表区域 - 营收趋势</div>

        <!-- 数据表格 -->
        <div class="section-title">营收明细</div>
        <el-table :data="revenueData.trend" border>
          <el-table-column prop="date" label="日期" />
          <el-table-column prop="salesAmount" label="销售额" />
          <el-table-column prop="workOrderAmount" label="工单额" />
          <el-table-column prop="totalRevenue" label="总营收" />
          <el-table-column prop="receivedAmount" label="回款额" />
        </el-table>
      </el-tab-pane>

      <!-- Tab 2: 员工业绩 -->
      <el-tab-pane label="员工业绩" name="employee">
        <!-- 汇总卡片 -->
        <el-row :gutter="20" class="stat-row">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #409eff;">
                  <el-icon><User /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">员工总数</div>
                  <div class="stat-value">{{ employeeData.summary.totalEmployees || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #67c23a;">
                  <el-icon><Money /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">销售总额</div>
                  <div class="stat-value">{{ employeeData.summary.totalSalesAmount || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #8e44ad;">
                  <el-icon><DocumentChecked /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">工单总额</div>
                  <div class="stat-value">{{ employeeData.summary.totalWorkOrderAmount || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #e6a23c;">
                  <el-icon><TrendCharts /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">总业绩</div>
                  <div class="stat-value">{{ employeeData.summary.totalPerformance || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 员工业绩表格 -->
        <div class="section-title">员工业绩排行</div>
        <el-table :data="employeeData.details" border>
          <el-table-column label="排名" width="80" align="center">
            <template #default="{ $index }">
              <div class="rank" :class="getRankClass($index)">{{ $index + 1 }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="employeeName" label="员工姓名" />
          <el-table-column prop="department" label="部门" />
          <el-table-column prop="salesCount" label="销售单数" />
          <el-table-column prop="salesAmount" label="销售额" />
          <el-table-column prop="workOrderCount" label="工单数" />
          <el-table-column prop="workOrderAmount" label="工单额" />
          <el-table-column prop="totalPerformance" label="总业绩" />
        </el-table>
      </el-tab-pane>

      <!-- Tab 3: 客户业绩 -->
      <el-tab-pane label="客户业绩" name="customer">
        <!-- 汇总卡片 -->
        <el-row :gutter="20" class="stat-row">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #409eff;">
                  <el-icon><OfficeBuilding /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">客户总数</div>
                  <div class="stat-value">{{ customerData.summary.totalCustomers || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #67c23a;">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">订单总数</div>
                  <div class="stat-value">{{ customerData.summary.totalOrders || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #8e44ad;">
                  <el-icon><Money /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">订单总额</div>
                  <div class="stat-value">{{ customerData.summary.totalOrderAmount || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #e6a23c;">
                  <el-icon><CircleCheck /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">已回款</div>
                  <div class="stat-value">{{ customerData.summary.receivedAmount || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- TOP客户表格 -->
        <div class="section-title">TOP客户</div>
        <el-table :data="customerData.topCustomers" border>
          <el-table-column label="排名" width="80" align="center">
            <template #default="{ $index }">
              <div class="rank" :class="getRankClass($index)">{{ $index + 1 }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="customerName" label="客户名称" />
          <el-table-column prop="orderCount" label="订单数" />
          <el-table-column prop="orderAmount" label="订单总额" />
          <el-table-column prop="receivedAmount" label="已回款" />
          <el-table-column prop="unreceivedAmount" label="未回款" />
        </el-table>
      </el-tab-pane>

      <!-- Tab 4: 产品业绩 -->
      <el-tab-pane label="产品业绩" name="product">
        <!-- 汇总卡片 -->
        <el-row :gutter="20" class="stat-row">
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #409eff;">
                  <el-icon><Goods /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">产品种类</div>
                  <div class="stat-value">{{ productData.summary.totalCategories || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #67c23a;">
                  <el-icon><ShoppingCart /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">销售数量</div>
                  <div class="stat-value">{{ productData.summary.totalSalesQuantity || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon" style="background: #8e44ad;">
                  <el-icon><Money /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">销售金额</div>
                  <div class="stat-value">{{ productData.summary.totalSalesAmount || 0 }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 分类统计表格 -->
        <div class="section-title">分类统计</div>
        <el-table :data="productData.categoryStats" border>
          <el-table-column prop="categoryName" label="分类名称" />
          <el-table-column prop="productCount" label="产品数" />
          <el-table-column prop="salesQuantity" label="销售数量" />
          <el-table-column prop="salesAmount" label="销售金额" />
        </el-table>

        <!-- TOP产品表格 -->
        <div class="section-title">TOP产品</div>
        <el-table :data="productData.topProducts" border>
          <el-table-column label="排名" width="80" align="center">
            <template #default="{ $index }">
              <div class="rank" :class="getRankClass($index)">{{ $index + 1 }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="productName" label="产品名称" />
          <el-table-column prop="category" label="分类" />
          <el-table-column prop="salesQuantity" label="销售数量" />
          <el-table-column prop="salesAmount" label="销售金额" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Download,
  Money,
  DocumentChecked,
  TrendCharts,
  CircleCheck,
  User,
  OfficeBuilding,
  Document,
  Goods,
  ShoppingCart
} from '@element-plus/icons-vue'
import {
  getRevenueStatistics,
  getEmployeeStatistics,
  getCustomerStatistics,
  getProductStatistics
} from '@/api/statistics'

// 筛选条件 - 默认当月
const now = new Date()
const currentMonth = now.getMonth()
const currentYear = now.getFullYear()
const firstDay = new Date(currentYear, currentMonth, 1)
const lastDay = new Date(currentYear, currentMonth + 1, 0)
const formatDate = (d) => d.toISOString().slice(0, 10)

const filter = reactive({
  startDate: formatDate(firstDay),
  endDate: formatDate(lastDay)
})

// 当前激活的Tab
const activeTab = ref('revenue')

// 营收统计数据
const revenueData = reactive({
  summary: {},
  trend: []
})

// 员工业绩数据
const employeeData = reactive({
  summary: {},
  details: []
})

// 客户业绩数据
const customerData = reactive({
  summary: {},
  topCustomers: []
})

// 产品业绩数据
const productData = reactive({
  summary: {},
  topProducts: [],
  categoryStats: []
})

// 获取排名样式类
const getRankClass = (index) => {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return 'rank-other'
}

// 加载营收统计
const loadRevenueData = async () => {
  try {
    const res = await getRevenueStatistics({
      start_date: filter.startDate,
      end_date: filter.endDate
    })
    if (res.code === 200) {
      revenueData.summary = res.data.summary || {}
      revenueData.trend = res.data.trend || []
    }
  } catch (error) {
    ElMessage.error('加载营收统计失败')
  }
}

// 加载员工业绩
const loadEmployeeData = async () => {
  try {
    const res = await getEmployeeStatistics({
      start_date: filter.startDate,
      end_date: filter.endDate
    })
    if (res.code === 200) {
      employeeData.summary = res.data.summary || {}
      employeeData.details = res.data.details || []
    }
  } catch (error) {
    ElMessage.error('加载员工业绩失败')
  }
}

// 加载客户业绩
const loadCustomerData = async () => {
  try {
    const res = await getCustomerStatistics({
      start_date: filter.startDate,
      end_date: filter.endDate
    })
    if (res.code === 200) {
      customerData.summary = res.data.summary || {}
      customerData.topCustomers = res.data.top_customers || []
    }
  } catch (error) {
    ElMessage.error('加载客户业绩失败')
  }
}

// 加载产品业绩
const loadProductData = async () => {
  try {
    const res = await getProductStatistics({
      start_date: filter.startDate,
      end_date: filter.endDate
    })
    if (res.code === 200) {
      productData.summary = res.data.summary || {}
      productData.topProducts = res.data.top_products || []
      productData.categoryStats = res.data.category_stats || []
    }
  } catch (error) {
    ElMessage.error('加载产品业绩失败')
  }
}

// 刷新按钮
const handleRefresh = () => {
  handleTabChange(activeTab.value)
}

// 导出按钮
const handleExport = () => {
  let headers = []
  let rows = []
  let filename = ''
  
  switch (activeTab.value) {
    case 'revenue':
      filename = '营收统计'
      headers = ['日期', '销售额', '工单额', '总营收', '回款额']
      rows = revenueData.trend.map(item => [
        item.date || '',
        Number(item.salesAmount || 0).toFixed(2),
        Number(item.workOrderAmount || 0).toFixed(2),
        Number(item.totalRevenue || 0).toFixed(2),
        Number(item.receivedAmount || 0).toFixed(2)
      ])
      break
    case 'employee':
      filename = '员工业绩'
      headers = ['员工姓名', '部门', '销售订单数', '销售总额', '工单数', '工单总额', '总业绩']
      rows = employeeData.list.map(item => [
        item.user_name || '',
        item.department || '',
        item.sales_count || 0,
        Number(item.sales_amount || 0).toFixed(2),
        item.workorder_count || 0,
        Number(item.workorder_amount || 0).toFixed(2),
        Number(item.total_amount || 0).toFixed(2)
      ])
      break
    case 'customer':
      filename = '客户业绩'
      headers = ['客户名称', '销售订单数', '销售总额', '工单数', '工单总额', '总消费', '排名']
      rows = customerData.list.map((item, index) => [
        item.customer_name || '',
        item.sales_count || 0,
        Number(item.sales_amount || 0).toFixed(2),
        item.workorder_count || 0,
        Number(item.workorder_amount || 0).toFixed(2),
        Number(item.total_amount || 0).toFixed(2),
        index + 1
      ])
      break
    case 'product':
      filename = '产品业绩'
      headers = ['产品名称', '规格', '销售数量', '销售金额', '利润']
      rows = productData.list.map(item => [
        item.product_name || '',
        item.specification || '',
        item.sales_quantity || 0,
        Number(item.sales_amount || 0).toFixed(2),
        Number(item.profit || 0).toFixed(2)
      ])
      break
  }
  
  if (rows.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  
  const csvContent = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// Tab切换
const handleTabChange = (tabName) => {
  switch (tabName) {
    case 'revenue':
      loadRevenueData()
      break
    case 'employee':
      loadEmployeeData()
      break
    case 'customer':
      loadCustomerData()
      break
    case 'product':
      loadProductData()
      break
  }
}

// 初始化
onMounted(() => {
  loadRevenueData()
})
</script>

<style scoped lang="scss">
.statistics-page {
  .filter-bar {
    margin-bottom: 20px;
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

  .chart-area {
    height: 300px;
    background: #f5f7fa;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #909399;
    margin-bottom: 20px;
  }

  .section-title {
    font-size: 16px;
    font-weight: bold;
    margin: 20px 0 15px;
    padding-left: 10px;
    border-left: 4px solid #409eff;
  }

  .rank {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;

    &.rank-1 {
      background: #ffd700;
      color: #fff;
    }

    &.rank-2 {
      background: #c0c0c0;
      color: #fff;
    }

    &.rank-3 {
      background: #cd7f32;
      color: #fff;
    }

    &.rank-other {
      background: #e4e7ed;
      color: #606266;
    }
  }
}
</style>
