<template>
  <div class="inventory-check-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>库存盘点</span>
          <div class="header-actions">
            <el-button type="primary" :icon="Plus" @click="handleAdd">新增盘点单</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="盘点单号/仓库/货架"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="待盘点" :value="0" />
            <el-option label="盘点中" :value="1" />
            <el-option label="已完成" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="check_no" label="盘点单号" width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.check_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="warehouse_name" label="盘点仓库" min-width="120" />
        <el-table-column prop="shelf_name" label="盘点货架" min-width="120">
          <template #default="{ row }">
            {{ row.shelf_name || '全部货架' }}
          </template>
        </el-table-column>
        <el-table-column prop="check_date" label="盘点日期" width="110" />
        <el-table-column prop="total_items" label="盘点商品数" width="100" align="center" />
        <el-table-column prop="profit_items" label="盘盈数" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.profit_items > 0" style="color: #67c23a; font-weight: bold">+{{ row.profit_items }}</span>
            <span v-else>0</span>
          </template>
        </el-table-column>
        <el-table-column prop="loss_items" label="盘亏数" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.loss_items > 0" style="color: #f56c6c; font-weight: bold">-{{ row.loss_items }}</span>
            <span v-else>0</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">详情</el-button>
            <el-button type="warning" link size="small" @click="handleEdit(row)" v-if="row.status < 2">盘点录入</el-button>
            <el-button type="success" link size="small" @click="handleComplete(row)" v-if="row.status < 2">完成盘点</el-button>
            <el-button type="info" link size="small" @click="handleDiffReport(row)" v-if="row.status === 2">差异报表</el-button>
            <el-button type="danger" link size="small" @click="handleCancel(row)" v-if="row.status < 2">取消</el-button>
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
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 新增盘点单弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增盘点单" width="600px" destroy-on-close>
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="盘点仓库" prop="warehouse_id">
          <el-select v-model="formData.warehouse_id" placeholder="请选择仓库" style="width: 100%" @change="onWarehouseChange">
            <el-option v-for="w in warehouseList" :key="w.id" :label="w.warehouse_name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="盘点货架">
          <el-select v-model="formData.shelf_id" placeholder="全部货架（不选则盘点整个仓库）" clearable style="width: 100%">
            <el-option v-for="s in shelfList" :key="s.id" :label="s.shelf_name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="盘点日期" prop="check_date">
          <el-date-picker
            v-model="formData.check_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="备注信息" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">创建并加载库存</el-button>
      </template>
    </el-dialog>

    <!-- 盘点录入弹窗 -->
    <el-dialog v-model="checkVisible" title="盘点录入" width="1000px" destroy-on-close>
      <div class="check-info">
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="盘点单号">{{ currentOrder.check_no }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ currentOrder.warehouse_name }}</el-descriptions-item>
          <el-descriptions-item label="货架">{{ currentOrder.shelf_name || '全部' }}</el-descriptions-item>
          <el-descriptions-item label="商品数">{{ checkItems.length }} 种</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="check-actions">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            请逐一核对实物数量并录入实盘数，系统自动计算差异数。所有账面有库存的配件已全部列出，防止漏盘。
          </template>
        </el-alert>
      </div>

      <el-table :data="checkItems" border size="small" v-loading="checkLoading" max-height="500" style="margin-top: 15px">
        <el-table-column type="index" label="序号" width="50" align="center" fixed="left" />
        <el-table-column prop="product_code" label="商品编码" width="120" fixed="left" />
        <el-table-column prop="product_name" label="商品名称" min-width="180" fixed="left" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="unit_name" label="单位" width="60" align="center" />
        <el-table-column prop="system_quantity" label="账面数量" width="100" align="center">
          <template #default="{ row }">
            <span>{{ Number(row.system_quantity || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="实盘数量" width="130" fixed="right">
          <template #default="{ row, $index }">
            <el-input-number
              v-model="row.actual_quantity"
              :min="0"
              :precision="2"
              :step="1"
              controls-position="right"
              style="width: 100%"
              @change="calculateDiff($index)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="diff_quantity" label="差异数" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <span :style="{ color: getDiffColor(row.diff_quantity), fontWeight: 'bold' }">
              {{ Number(row.diff_quantity || 0) > 0 ? '+' : '' }}{{ Number(row.diff_quantity || 0).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="备注" width="150" fixed="right">
          <template #default="{ row }">
            <el-input v-model="row.remark" placeholder="备注" size="small" />
          </template>
        </el-table-column>
      </el-table>

      <div class="check-summary">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <span class="label">盘点商品</span>
              <span class="value">{{ checkItems.length }}</span>
              <span class="unit">种</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item profit">
              <span class="label">盘盈</span>
              <span class="value">{{ profitCount }}</span>
              <span class="unit">项</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item loss">
              <span class="label">盘亏</span>
              <span class="value">{{ lossCount }}</span>
              <span class="unit">项</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <span class="label">正常</span>
              <span class="value">{{ normalCount }}</span>
              <span class="unit">项</span>
            </div>
          </el-col>
        </el-row>
      </div>

      <template #footer>
        <el-button @click="checkVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCheckItems" :loading="checkSubmitLoading">保存盘点数据</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="盘点单详情" width="1000px" destroy-on-close>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="盘点单号">{{ currentOrder.check_no }}</el-descriptions-item>
        <el-descriptions-item label="盘点仓库">{{ currentOrder.warehouse_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="盘点货架">{{ currentOrder.shelf_name || '全部货架' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentOrder.status)">{{ getStatusText(currentOrder.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="盘点日期">{{ currentOrder.check_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentOrder.created_at }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">盘点明细</el-divider>

      <el-table :data="currentOrder.items || []" border size="small" max-height="400">
        <el-table-column type="index" label="序号" width="50" align="center" />
        <el-table-column prop="product_code" label="商品编码" width="120" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="unit_name" label="单位" width="60" align="center" />
        <el-table-column prop="system_quantity" label="账面数量" width="90" align="center" />
        <el-table-column prop="actual_quantity" label="实盘数量" width="90" align="center" />
        <el-table-column prop="diff_quantity" label="差异数" width="90" align="center">
          <template #default="{ row }">
            <span :style="{ color: getDiffColor(row.diff_quantity), fontWeight: 'bold' }">
              {{ Number(row.diff_quantity || 0) > 0 ? '+' : '' }}{{ Number(row.diff_quantity || 0).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="diff_amount" label="差异金额" width="100" align="right">
          <template #default="{ row }">
            <span :style="{ color: getDiffColor(row.diff_quantity) }">
              ¥{{ Number(row.diff_amount || 0).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" />
      </el-table>

      <div class="detail-summary">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="盘盈项数" :value="currentOrder.profit_items || 0" value-style="color: #67c23a" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="盘亏项数" :value="currentOrder.loss_items || 0" value-style="color: #f56c6c" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="差异金额" :value="currentOrder.diff_amount || 0" prefix="¥" :precision="2" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="盘点商品" :value="currentOrder.total_items || 0" suffix="种" />
          </el-col>
        </el-row>
      </div>

      <el-divider content-position="left">备注</el-divider>
      <p>{{ currentOrder.remark || '无' }}</p>
    </el-dialog>

    <!-- 差异报表弹窗 -->
    <el-dialog v-model="diffReportVisible" title="盘点差异报表" width="1000px" destroy-on-close>
      <div class="report-header">
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="盘点单号">{{ diffReport.order_info?.check_no }}</el-descriptions-item>
          <el-descriptions-item label="仓库">{{ diffReport.order_info?.warehouse_name }}</el-descriptions-item>
          <el-descriptions-item label="货架">{{ diffReport.order_info?.shelf_name || '全部' }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ diffReport.order_info?.check_date }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="report-summary">
        <el-row :gutter="15">
          <el-col :span="3">
            <div class="summary-item">
              <span class="label">总计</span>
              <span class="value">{{ diffReport.summary?.total_items || 0 }}</span>
            </div>
          </el-col>
          <el-col :span="3">
            <div class="summary-item profit">
              <span class="label">盘盈</span>
              <span class="value">{{ diffReport.summary?.profit_count || 0 }}</span>
            </div>
          </el-col>
          <el-col :span="3">
            <div class="summary-item loss">
              <span class="label">盘亏</span>
              <span class="value">{{ diffReport.summary?.loss_count || 0 }}</span>
            </div>
          </el-col>
          <el-col :span="3">
            <div class="summary-item">
              <span class="label">正常</span>
              <span class="value">{{ diffReport.summary?.normal_count || 0 }}</span>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="summary-item profit">
              <span class="label">盘盈金额</span>
              <span class="value">¥{{ Number(diffReport.summary?.total_profit_amount || 0).toFixed(2) }}</span>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="summary-item loss">
              <span class="label">盘亏金额</span>
              <span class="value">¥{{ Number(diffReport.summary?.total_loss_amount || 0).toFixed(2) }}</span>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 盘盈列表 -->
      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="盘盈明细" name="profit">
          <el-table :data="diffReport.profit_items || []" border size="small" max-height="300">
            <el-table-column type="index" label="序号" width="50" align="center" />
            <el-table-column prop="product_code" label="商品编码" width="120" />
            <el-table-column prop="product_name" label="商品名称" min-width="150" />
            <el-table-column prop="specification" label="规格" width="100" />
            <el-table-column prop="system_quantity" label="账面数量" width="90" align="center" />
            <el-table-column prop="actual_quantity" label="实盘数量" width="90" align="center" />
            <el-table-column prop="diff_quantity" label="差异数" width="90" align="center">
              <template #default="{ row }">
                <span style="color: #67c23a; font-weight: bold">+{{ Number(row.diff_quantity || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="diff_amount" label="差异金额" width="100" align="right">
              <template #default="{ row }">
                <span style="color: #67c23a">¥{{ Number(row.diff_amount || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>

        <el-collapse-item title="盘亏明细" name="loss">
          <el-table :data="diffReport.loss_items || []" border size="small" max-height="300">
            <el-table-column type="index" label="序号" width="50" align="center" />
            <el-table-column prop="product_code" label="商品编码" width="120" />
            <el-table-column prop="product_name" label="商品名称" min-width="150" />
            <el-table-column prop="specification" label="规格" width="100" />
            <el-table-column prop="system_quantity" label="账面数量" width="90" align="center" />
            <el-table-column prop="actual_quantity" label="实盘数量" width="90" align="center" />
            <el-table-column prop="diff_quantity" label="差异数" width="90" align="center">
              <template #default="{ row }">
                <span style="color: #f56c6c; font-weight: bold">{{ Number(row.diff_quantity || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="diff_amount" label="差异金额" width="100" align="right">
              <template #default="{ row }">
                <span style="color: #f56c6c">¥{{ Number(row.diff_amount || 0).toFixed(2) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>

        <el-collapse-item title="正常项" name="normal">
          <el-table :data="diffReport.normal_items || []" border size="small" max-height="300">
            <el-table-column type="index" label="序号" width="50" align="center" />
            <el-table-column prop="product_code" label="商品编码" width="120" />
            <el-table-column prop="product_name" label="商品名称" min-width="150" />
            <el-table-column prop="specification" label="规格" width="100" />
            <el-table-column prop="system_quantity" label="账面数量" width="90" align="center" />
            <el-table-column prop="actual_quantity" label="实盘数量" width="90" align="center" />
          </el-table>
        </el-collapse-item>
      </el-collapse>

      <template #footer>
        <el-button type="success" :icon="Download" @click="handleExportDiff">导出Excel报表</el-button>
        <el-button @click="diffReportVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download } from '@element-plus/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const submitLoading = ref(false)
const checkLoading = ref(false)
const checkSubmitLoading = ref(false)
const tableData = ref([])

const dialogVisible = ref(false)
const checkVisible = ref(false)
const detailVisible = ref(false)
const diffReportVisible = ref(false)
const formRef = ref(null)
const currentOrder = ref({})
const checkItems = ref([])
const warehouseList = ref([])
const shelfList = ref([])
const diffReport = ref({})
const activeCollapse = ref(['profit', 'loss'])

const searchForm = reactive({
  keyword: '',
  status: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  warehouse_id: null,
  warehouse_name: '',
  shelf_id: null,
  shelf_name: '',
  check_date: '',
  remark: ''
})

const rules = {
  warehouse_id: [{ required: true, message: '请选择盘点仓库', trigger: 'change' }],
  check_date: [{ required: true, message: '请选择盘点日期', trigger: 'change' }]
}

const profitCount = computed(() => {
  return checkItems.value.filter(item => Number(item.diff_quantity || 0) > 0).length
})

const lossCount = computed(() => {
  return checkItems.value.filter(item => Number(item.diff_quantity || 0) < 0).length
})

const normalCount = computed(() => {
  return checkItems.value.filter(item => Number(item.diff_quantity || 0) === 0).length
})

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: '', 2: 'success' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '待盘点', 1: '盘点中', 2: '已完成' }
  return texts[status] || '未知'
}

const getDiffColor = (diff) => {
  if (Number(diff || 0) > 0) return '#67c23a'
  if (Number(diff || 0) < 0) return '#f56c6c'
  return '#909399'
}

// 获取盘点单列表
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword || undefined,
      status: searchForm.status !== null && searchForm.status !== '' ? searchForm.status : undefined
    }
    const res = await request.get('/inventory/check', { params })
    if (res.code === 200) {
      tableData.value = res.data.list || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取盘点单列表失败:', error)
    ElMessage.error('获取盘点单列表失败')
  } finally {
    loading.value = false
  }
}

// 获取仓库列表
const fetchWarehouses = async () => {
  try {
    const res = await request.get('/warehouses')
    if (res.code === 200) {
      warehouseList.value = res.data || []
      // 如果没有仓库数据，添加默认仓库
      if (warehouseList.value.length === 0) {
        warehouseList.value = [{ id: 1, warehouse_name: '主仓库' }]
      }
    }
  } catch (error) {
    console.error('获取仓库列表失败:', error)
    warehouseList.value = [{ id: 1, warehouse_name: '主仓库' }]
  }
}

// 获取货架列表
const fetchShelves = async (warehouseId) => {
  try {
    const params = warehouseId ? { warehouse_id: warehouseId } : {}
    const res = await request.get('/shelves', { params })
    if (res.code === 200) {
      shelfList.value = res.data || []
    }
  } catch (error) {
    console.error('获取货架列表失败:', error)
    shelfList.value = []
  }
}

// 仓库选择变更
const onWarehouseChange = (val) => {
  const w = warehouseList.value.find(item => item.id === val)
  if (w) {
    formData.warehouse_name = w.warehouse_name
  }
  formData.shelf_id = null
  formData.shelf_name = ''
  fetchShelves(val)
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

// 重置搜索
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.status = null
  handleSearch()
}

// 新增盘点单
const handleAdd = () => {
  Object.assign(formData, {
    warehouse_id: null,
    warehouse_name: '',
    shelf_id: null,
    shelf_name: '',
    check_date: new Date().toISOString().split('T')[0],
    remark: ''
  })
  shelfList.value = []
  dialogVisible.value = true
}

// 查看详情
const handleView = async (row) => {
  try {
    const res = await request.get(`/inventory/check/${row.id}`)
    if (res.code === 200) {
      currentOrder.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('获取盘点单详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

// 盘点录入
const handleEdit = async (row) => {
  currentOrder.value = row
  checkLoading.value = true
  try {
    const res = await request.get(`/inventory/check/${row.id}/items`)
    if (res.code === 200) {
      checkItems.value = res.data || []
      checkVisible.value = true
    }
  } catch (error) {
    console.error('获取盘点数据失败:', error)
    ElMessage.error('获取盘点数据失败')
  } finally {
    checkLoading.value = false
  }
}

// 完成盘点
const handleComplete = (row) => {
  ElMessageBox.confirm('确定要完成该盘点单吗？完成后将自动修正系统库存。', '确认完成', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await request.post(`/inventory/check/${row.id}/complete`)
      if (res.code === 200) {
        ElMessage.success('盘点完成，库存已更新')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('操作失败')
    }
  }).catch(() => {})
}

// 取消盘点单
const handleCancel = (row) => {
  ElMessageBox.confirm('确定要取消该盘点单吗？', '确认取消', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await request.delete(`/inventory/check/${row.id}`)
      if (res.code === 200) {
        ElMessage.success('取消成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('取消失败')
    }
  }).catch(() => {})
}

// 差异报表
const handleDiffReport = async (row) => {
  try {
    const res = await request.get(`/inventory/check/${row.id}/diff-report`)
    if (res.code === 200) {
      diffReport.value = res.data
      diffReportVisible.value = true
    }
  } catch (error) {
    console.error('获取差异报表失败:', error)
    ElMessage.error('获取差异报表失败')
  }
}

// 导出差异报表
const handleExportDiff = () => {
  const checkId = currentOrder.value.id
  if (!checkId) {
    ElMessage.warning('无法获取盘点单ID')
    return
  }
  // 下载文件
  const token = localStorage.getItem('token') || ''
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  const url = `${baseUrl}/inventory/check/diff-report/export?check_id=${checkId}&token=${token}`
  window.open(url, '_blank')
}

// 提交盘点单表单
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const res = await request.post('/inventory/check', formData)
      if (res.code === 200) {
        ElMessage.success('创建成功，已自动加载库存商品')
        dialogVisible.value = false
        fetchData()
        // 自动打开盘点录入
        if (res.data?.id) {
          const newRow = { id: res.data.id, check_no: res.data.check_no, ...formData }
          handleEdit(newRow)
        }
      }
    } catch (error) {
      ElMessage.error('创建失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 计算盈亏
const calculateDiff = (index) => {
  const item = checkItems.value[index]
  item.diff_quantity = Number(item.actual_quantity || 0) - Number(item.system_quantity || 0)
  item.diff_amount = Number(item.diff_quantity || 0) * Number(item.cost_price || 0)
}

// 保存盘点数据
const saveCheckItems = async () => {
  if (checkItems.value.length === 0) {
    ElMessage.warning('没有盘点数据')
    return
  }

  checkSubmitLoading.value = true
  try {
    const res = await request.put(`/inventory/check/${currentOrder.value.id}/items`, {
      items: checkItems.value
    })
    if (res.code === 200) {
      ElMessage.success('盘点数据保存成功')
      checkVisible.value = false
      fetchData()
    }
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    checkSubmitLoading.value = false
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
.inventory-check-page {
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

  .check-info {
    margin-bottom: 15px;
  }

  .check-actions {
    margin-bottom: 10px;
  }

  .check-summary {
    margin-top: 15px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;

    .summary-item {
      text-align: center;
      padding: 8px;

      .label {
        display: block;
        font-size: 12px;
        color: #909399;
        margin-bottom: 4px;
      }

      .value {
        font-size: 20px;
        font-weight: bold;
        color: #303133;
      }

      .unit {
        font-size: 12px;
        color: #909399;
        margin-left: 2px;
      }

      &.profit .value {
        color: #67c23a;
      }

      &.loss .value {
        color: #f56c6c;
      }
    }
  }

  .detail-summary {
    margin-top: 20px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 4px;
  }

  .report-header {
    margin-bottom: 15px;
  }

  .report-summary {
    margin-bottom: 15px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;

    .summary-item {
      text-align: center;
      padding: 6px;

      .label {
        display: block;
        font-size: 12px;
        color: #909399;
        margin-bottom: 2px;
      }

      .value {
        font-size: 16px;
        font-weight: bold;
        color: #303133;
      }

      &.profit .value {
        color: #67c23a;
      }

      &.loss .value {
        color: #f56c6c;
      }
    }
  }
}
</style>
