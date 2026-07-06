<template>
  <div class="inventory-cost-adjust-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>成本调价</span>
          <div class="header-actions">
            <el-button type="primary" :icon="Plus" @click="handleAdd" v-permission="'cost-adjust:add'">新建调价单</el-button>
            <el-button :icon="Download" @click="handleExport" v-permission="'cost-adjust:view'">导出</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="调价单号/商品名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="待审核" :value="0" />
            <el-option label="已审核" :value="1" />
            <el-option label="已取消" :value="2" />
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
            style="width: 260px"
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
        <el-table-column prop="adjust_no" label="调价单号" width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.adjust_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="warehouse_name" label="仓库名称" width="130" />
        <el-table-column prop="product_code" label="商品编码" width="130" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="old_cost" label="原成本价" width="110" align="right">
          <template #default="{ row }">
            ¥{{ row.old_cost?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="new_cost" label="新成本价" width="110" align="right">
          <template #default="{ row }">
            ¥{{ row.new_cost?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="调整数量" width="100" align="center" />
        <el-table-column prop="adjust_amount" label="调整金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="{ 'amount-up': row.adjust_amount > 0, 'amount-down': row.adjust_amount < 0 }">
              ¥{{ row.adjust_amount?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" label="创建人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">详情</el-button>
            <el-button type="success" link size="small" @click="handleAudit(row)" v-if="row.status === 0" v-permission="'cost-adjust:edit'">审核</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)" v-if="row.status === 0" v-permission="'cost-adjust:edit'">删除</el-button>
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

    <!-- 新建调价单弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建调价单"
      width="650px"
      destroy-on-close
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="仓库" prop="warehouse_id">
          <el-select
            v-model="formData.warehouse_id"
            placeholder="选择仓库"
            filterable
            style="width: 100%"
            @change="onWarehouseChange"
          >
            <el-option v-for="w in warehouses" :key="w.id" :label="w.warehouse_name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="商品" prop="product_id">
          <el-select
            v-model="formData.product_id"
            placeholder="选择商品"
            filterable
            style="width: 100%"
            @change="onProductChange"
          >
            <el-option v-for="p in products" :key="p.id" :label="`${p.product_code} - ${p.product_name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="原成本价">
              <el-input v-model="formData.old_cost" disabled placeholder="选择商品后自动填充" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="当前库存">
              <el-input v-model="formData.stock_quantity" disabled placeholder="选择商品后自动填充" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="新成本价" prop="new_cost">
              <el-input-number
                v-model="formData.new_cost"
                :min="0"
                :precision="2"
                :step="0.01"
                style="width: 100%"
                @change="calculateAdjustAmount"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="调整数量" prop="quantity">
              <el-input-number
                v-model="formData.quantity"
                :min="1"
                :precision="0"
                style="width: 100%"
                @change="calculateAdjustAmount"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="调整金额">
          <el-input :model-value="adjustAmountDisplay" disabled />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="备注信息" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="调价单详情" width="700px" destroy-on-close>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="调价单号">{{ currentOrder.adjust_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentOrder.status)">{{ getStatusText(currentOrder.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="仓库">{{ currentOrder.warehouse_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="商品编码">{{ currentOrder.product_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="商品名称">{{ currentOrder.product_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ currentOrder.created_by || '-' }}</el-descriptions-item>
        <el-descriptions-item label="原成本价">¥{{ currentOrder.old_cost?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="新成本价">¥{{ currentOrder.new_cost?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="调整数量">{{ currentOrder.quantity }}</el-descriptions-item>
        <el-descriptions-item label="调整金额">
          <span :class="{ 'amount-up': currentOrder.adjust_amount > 0, 'amount-down': currentOrder.adjust_amount < 0 }">
            ¥{{ currentOrder.adjust_amount?.toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentOrder.created_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">{{ currentOrder.audit_at || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">备注</el-divider>
      <p>{{ currentOrder.remark || '无' }}</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download } from '@element-plus/icons-vue'
import {
  getCostAdjustList,
  getCostAdjustDetail,
  createCostAdjust,
  auditCostAdjust,
  deleteCostAdjust,
  exportCostAdjust,
  getWarehouseList
} from '@/api/inventory'
import { getProductList } from '@/api/product'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const warehouses = ref([])
const products = ref([])

const dialogVisible = ref(false)
const detailVisible = ref(false)
const formRef = ref(null)
const currentOrder = ref({})

const searchForm = reactive({
  keyword: '',
  status: null,
  dateRange: []
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  warehouse_id: null,
  product_id: null,
  old_cost: '',
  stock_quantity: '',
  new_cost: null,
  quantity: null,
  remark: ''
})

const rules = {
  warehouse_id: [{ required: true, message: '请选择仓库', trigger: 'change' }],
  product_id: [{ required: true, message: '请选择商品', trigger: 'change' }],
  new_cost: [{ required: true, message: '请输入新成本价', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入调整数量', trigger: 'blur' }]
}

// 调整金额自动计算
const adjustAmount = computed(() => {
  const oldCost = parseFloat(formData.old_cost) || 0
  const newCost = formData.new_cost || 0
  const quantity = formData.quantity || 0
  return (newCost - oldCost) * quantity
})

const adjustAmountDisplay = computed(() => {
  const amount = adjustAmount.value
  const prefix = amount >= 0 ? '+' : ''
  return `${prefix}¥${amount.toFixed(2)}`
})

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'success', 2: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '待审核', 1: '已审核', 2: '已取消' }
  return texts[status] || '未知'
}

// 获取调价单列表
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      status: searchForm.status
    }
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_date = searchForm.dateRange[0]
      params.end_date = searchForm.dateRange[1]
    }
    const res = await getCostAdjustList(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取成本调价列表失败:', error)
    ElMessage.error('获取成本调价列表失败')
  } finally {
    loading.value = false
  }
}

// 获取仓库列表
const fetchWarehouses = async () => {
  try {
    const res = await getWarehouseList({ page_size: 1000 })
    if (res.code === 200) {
      warehouses.value = res.data.list
    }
  } catch (error) {
    console.error('获取仓库列表失败:', error)
  }
}

// 获取商品列表
const fetchProducts = async () => {
  try {
    const res = await getProductList({ page_size: 1000 })
    if (res.code === 200) {
      products.value = res.data.list
    }
  } catch (error) {
    console.error('获取商品列表失败:', error)
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
  searchForm.status = null
  searchForm.dateRange = []
  handleSearch()
}

// 新建调价单
const handleAdd = () => {
  Object.assign(formData, {
    warehouse_id: null,
    product_id: null,
    old_cost: '',
    stock_quantity: '',
    new_cost: null,
    quantity: null,
    remark: ''
  })
  dialogVisible.value = true
}

// 仓库选择变更
const onWarehouseChange = () => {
  // 切换仓库时清空商品相关信息
  formData.product_id = null
  formData.old_cost = ''
  formData.stock_quantity = ''
  formData.new_cost = null
  formData.quantity = null
}

// 商品选择变更
const onProductChange = (productId) => {
  const product = products.value.find(p => p.id === productId)
  if (product) {
    formData.old_cost = product.cost_price ? product.cost_price.toFixed(2) : '0.00'
    formData.stock_quantity = product.stock_quantity || 0
    formData.quantity = product.stock_quantity || 1
    calculateAdjustAmount()
  }
}

// 计算调整金额
const calculateAdjustAmount = () => {
  // adjustAmount 是 computed，自动更新
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const data = {
        warehouse_id: formData.warehouse_id,
        product_id: formData.product_id,
        old_cost: parseFloat(formData.old_cost) || 0,
        new_cost: formData.new_cost,
        quantity: formData.quantity,
        adjust_amount: adjustAmount.value,
        remark: formData.remark
      }
      const res = await createCostAdjust(data)
      if (res.code === 200) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      ElMessage.error('创建失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 查看详情
const handleView = async (row) => {
  try {
    const res = await getCostAdjustDetail(row.id)
    if (res.code === 200) {
      currentOrder.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('获取调价单详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

// 审核调价单
const handleAudit = (row) => {
  ElMessageBox.confirm('确定要审核该调价单吗？审核后商品成本价将更新。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await auditCostAdjust(row.id)
      if (res.code === 200) {
        ElMessage.success('审核成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('审核失败')
    }
  }).catch(() => {})
}

// 删除调价单
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该调价单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteCostAdjust(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 导出
const handleExport = async () => {
  try {
    const res = await exportCostAdjust()
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `成本调价_${new Date().toISOString().split('T')[0]}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
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
  fetchProducts()
})
</script>

<style lang="scss" scoped>
.inventory-cost-adjust-page {
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

  .amount-up {
    color: #f56c6c;
    font-weight: 500;
  }

  .amount-down {
    color: #67c23a;
    font-weight: 500;
  }
}
</style>
