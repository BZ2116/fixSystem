<template>
  <div class="inventory-logs-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>库存变动明细</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="商品名称/编码"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="仓库">
          <el-select v-model="searchForm.warehouse_id" placeholder="全部" clearable filterable style="width: 140px">
            <el-option v-for="w in warehouses" :key="w.id" :label="w.warehouse_name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="变动类型">
          <el-select v-model="searchForm.change_type" placeholder="全部" clearable style="width: 120px">
            <el-option label="入库" value="in" />
            <el-option label="出库" value="out" />
            <el-option label="调整" value="adjust" />
            <el-option label="调拨" value="transfer" />
          </el-select>
        </el-form-item>
        <el-form-item label="单据类型">
          <el-select v-model="searchForm.bill_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="采购入库" value="purchase_in" />
            <el-option label="销售出库" value="sale_out" />
            <el-option label="维修领料" value="repair_out" />
            <el-option label="退货入库" value="return_in" />
            <el-option label="调拨" value="transfer" />
            <el-option label="盘点调整" value="check_adjust" />
            <el-option label="成本调价" value="cost_adjust" />
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
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="product_code" label="商品编码" width="130" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="warehouse_name" label="仓库名称" width="120" />
        <el-table-column prop="change_type" label="变动类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getChangeTypeTag(row.change_type)" size="small">{{ getChangeTypeText(row.change_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="bill_type" label="单据类型" width="110" align="center">
          <template #default="{ row }">
            {{ getBillTypeText(row.bill_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="bill_no" label="单据号" width="160" />
        <el-table-column prop="quantity" label="变动数量" width="100" align="center">
          <template #default="{ row }">
            <span :class="row.quantity > 0 ? 'text-success' : 'text-danger'">
              {{ row.quantity > 0 ? '+' : '' }}{{ row.quantity }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="before_quantity" label="变动前数量" width="110" align="center" />
        <el-table-column prop="after_quantity" label="变动后数量" width="110" align="center" />
        <el-table-column prop="cost_price" label="成本价" width="100" align="right">
          <template #default="{ row }">
            {{ row.cost_price != null ? '¥' + row.cost_price.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="变动金额" width="110" align="right">
          <template #default="{ row }">
            <span v-if="row.amount != null" :class="row.amount > 0 ? 'text-success' : row.amount < 0 ? 'text-danger' : ''">
              {{ row.amount > 0 ? '+' : '' }}{{ row.amount.toFixed(2) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="partner_name" label="往来单位" min-width="130">
          <template #default="{ row }">
            {{ row.partner_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="100" />
        <el-table-column prop="created_at" label="操作时间" width="170" />
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import { getInventoryLogs, exportInventoryLogs, getWarehouseList } from '@/api/inventory'

const loading = ref(false)
const tableData = ref([])
const warehouses = ref([])

const searchForm = reactive({
  keyword: '',
  warehouse_id: null,
  change_type: '',
  bill_type: '',
  dateRange: []
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 变动类型标签颜色
const getChangeTypeTag = (type) => {
  const map = { in: 'success', out: 'danger', adjust: 'warning', transfer: 'info' }
  return map[type] || 'info'
}

// 变动类型文本
const getChangeTypeText = (type) => {
  const map = { in: '入库', out: '出库', adjust: '调整', transfer: '调拨' }
  return map[type] || '未知'
}

// 单据类型文本
const getBillTypeText = (type) => {
  const map = {
    purchase_in: '采购入库',
    sale_out: '销售出库',
    repair_out: '维修领料',
    return_in: '退货入库',
    transfer: '调拨',
    check_adjust: '盘点调整',
    cost_adjust: '成本调价'
  }
  return map[type] || type || '-'
}

// 获取库存变动列表
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      warehouse_id: searchForm.warehouse_id,
      change_type: searchForm.change_type,
      bill_type: searchForm.bill_type
    }
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_date = searchForm.dateRange[0]
      params.end_date = searchForm.dateRange[1]
    }
    const res = await getInventoryLogs(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取库存变动列表失败:', error)
    ElMessage.error('获取库存变动列表失败')
  } finally {
    loading.value = false
  }
}

// 获取仓库列表
const fetchWarehouses = async () => {
  try {
    const res = await getWarehouseList({ page_size: 1000 })
    if (res.code === 200) {
      warehouses.value = res.data.list || res.data || []
    }
  } catch (error) {
    console.error('获取仓库列表失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

// 重置搜索
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.warehouse_id = null
  searchForm.change_type = ''
  searchForm.bill_type = ''
  searchForm.dateRange = []
  handleSearch()
}

// 导出
const handleExport = async () => {
  try {
    const res = await exportInventoryLogs()
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `库存变动明细_${new Date().toISOString().split('T')[0]}.xlsx`
    link.click()
    URL.revokeObjectURL(link.href)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 分页
const handleSizeChange = (val) => {
  pagination.pageSize = val
  fetchData()
}

const handlePageChange = (val) => {
  pagination.page = val
  fetchData()
}

onMounted(() => {
  fetchData()
  fetchWarehouses()
})
</script>

<style lang="scss" scoped>
.inventory-logs-page {
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

  .text-success {
    color: #67c23a;
    font-weight: 500;
  }

  .text-danger {
    color: #f56c6c;
    font-weight: 500;
  }
}
</style>
