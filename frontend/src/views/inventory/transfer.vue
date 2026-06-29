<template>
  <div class="inventory-transfer-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>调拨管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
            <el-button type="primary" :icon="Plus" @click="handleAdd">新建调拨单</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="调拨单号"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="调拨类型">
          <el-select v-model="searchForm.transfer_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="同价调拨" value="same_price" />
            <el-option label="变价调拨" value="change_price" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="待审核" :value="0" />
            <el-option label="已审核" :value="1" />
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
        <el-table-column prop="transfer_no" label="调拨单号" width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.transfer_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="transfer_type" label="调拨类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.transfer_type === 'same_price' ? '' : 'warning'" size="small">
              {{ row.transfer_type === 'same_price' ? '同价' : '变价' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="from_warehouse_name" label="调出仓库" width="130" />
        <el-table-column prop="to_warehouse_name" label="调入仓库" width="130" />
        <el-table-column prop="total_quantity" label="商品数量" width="100" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handler" label="经手人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">详情</el-button>
            <el-button type="success" link size="small" @click="handleAudit(row)" v-if="row.status === 0">审核</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)" v-if="row.status === 0">删除</el-button>
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

    <!-- 新建调拨单弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建调拨单"
      width="1000px"
      destroy-on-close
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="调拨类型" prop="transfer_type">
              <el-radio-group v-model="formData.transfer_type" @change="onTransferTypeChange">
                <el-radio :label="'same_price'">同价调拨</el-radio>
                <el-radio :label="'change_price'">变价调拨</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="调出仓库" prop="from_warehouse_id">
              <el-select
                v-model="formData.from_warehouse_id"
                placeholder="选择调出仓库"
                filterable
                style="width: 100%"
                @change="onFromWarehouseChange"
              >
                <el-option v-for="w in warehouses" :key="w.id" :label="w.warehouse_name" :value="w.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="调入仓库" prop="to_warehouse_id">
              <el-select
                v-model="formData.to_warehouse_id"
                placeholder="选择调入仓库"
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="w in filteredToWarehouses"
                  :key="w.id"
                  :label="w.warehouse_name"
                  :value="w.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="经手人" prop="handler">
              <el-input v-model="formData.handler" placeholder="请输入经手人" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="备注信息" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">商品明细</el-divider>

        <div class="items-header">
          <el-button type="primary" size="small" :icon="Plus" @click="addItem">添加商品</el-button>
        </div>

        <el-table :data="formData.items" border size="small" class="items-table">
          <el-table-column type="index" label="序号" width="50" align="center" />
          <el-table-column label="商品" min-width="180">
            <template #default="{ row, $index }">
              <el-select
                v-model="row.product_id"
                placeholder="选择商品"
                filterable
                @change="(val) => onProductChange(val, $index)"
                style="width: 100%"
              >
                <el-option v-for="p in products" :key="p.id" :label="p.product_name" :value="p.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" :precision="0" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="调出成本价" width="130">
            <template #default="{ row }">
              <el-input-number
                v-model="row.from_cost_price"
                :min="0"
                :precision="2"
                :disabled="formData.transfer_type === 'same_price'"
                style="width: 100%"
              />
            </template>
          </el-table-column>
          <el-table-column v-if="formData.transfer_type === 'change_price'" label="调入成本价" width="130">
            <template #default="{ row }">
              <el-input-number v-model="row.to_cost_price" :min="0" :precision="2" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="amount-summary">
          <span>商品数量合计: <strong>{{ totalQuantity }}</strong></span>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="调拨单详情" width="900px" destroy-on-close>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="调拨单号">{{ currentOrder.transfer_no }}</el-descriptions-item>
        <el-descriptions-item label="调拨类型">
          <el-tag :type="currentOrder.transfer_type === 'same_price' ? '' : 'warning'" size="small">
            {{ currentOrder.transfer_type === 'same_price' ? '同价调拨' : '变价调拨' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentOrder.status)" size="small">{{ getStatusText(currentOrder.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="调出仓库">{{ currentOrder.from_warehouse_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="调入仓库">{{ currentOrder.to_warehouse_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="经手人">{{ currentOrder.handler || '-' }}</el-descriptions-item>
        <el-descriptions-item label="商品数量">{{ currentOrder.total_quantity || 0 }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentOrder.created_at }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">商品明细</el-divider>

      <el-table :data="currentOrder.items || []" border size="small">
        <el-table-column type="index" label="序号" width="50" align="center" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="product_code" label="商品编码" width="130" />
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column prop="from_cost_price" label="调出成本价" width="120" align="right">
          <template #default="{ row }">
            {{ row.from_cost_price != null ? '¥' + row.from_cost_price.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column v-if="currentOrder.transfer_type === 'change_price'" prop="to_cost_price" label="调入成本价" width="120" align="right">
          <template #default="{ row }">
            {{ row.to_cost_price != null ? '¥' + row.to_cost_price.toFixed(2) : '-' }}
          </template>
        </el-table-column>
      </el-table>

      <div class="detail-summary">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="商品数量合计" :value="currentOrder.total_quantity || 0" />
          </el-col>
        </el-row>
      </div>

      <el-divider content-position="left">备注</el-divider>
      <p>{{ currentOrder.remark || '无' }}</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download } from '@element-plus/icons-vue'
import { getTransferList, getTransferDetail, createTransfer, auditTransfer, deleteTransfer, getWarehouseList } from '@/api/inventory'
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
  transfer_type: '',
  status: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  transfer_type: 'same_price',
  from_warehouse_id: null,
  to_warehouse_id: null,
  handler: '',
  remark: '',
  items: []
})

const rules = {
  transfer_type: [{ required: true, message: '请选择调拨类型', trigger: 'change' }],
  from_warehouse_id: [{ required: true, message: '请选择调出仓库', trigger: 'change' }],
  to_warehouse_id: [{ required: true, message: '请选择调入仓库', trigger: 'change' }],
  handler: [{ required: true, message: '请输入经手人', trigger: 'blur' }]
}

// 过滤后的调入仓库列表（排除调出仓库）
const filteredToWarehouses = computed(() => {
  return warehouses.value.filter(w => w.id !== formData.from_warehouse_id)
})

// 商品数量合计
const totalQuantity = computed(() => {
  return formData.items.reduce((sum, item) => sum + (item.quantity || 0), 0)
})

// 状态标签颜色
const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'primary', 2: 'success' }
  return types[status] || 'info'
}

// 状态文本
const getStatusText = (status) => {
  const texts = { 0: '待审核', 1: '已审核', 2: '已完成' }
  return texts[status] || '未知'
}

// 获取调拨单列表
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      transfer_type: searchForm.transfer_type,
      status: searchForm.status
    }
    const res = await getTransferList(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取调拨单列表失败:', error)
    ElMessage.error('获取调拨单列表失败')
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
  searchForm.transfer_type = ''
  searchForm.status = null
  handleSearch()
}

// 导出
const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.transfer_type) params.append('transfer_type', searchForm.transfer_type)
  if (searchForm.status != null) params.append('status', searchForm.status)
  const token = localStorage.getItem('token') || ''
  window.open(`/api/transfer/orders/export?${params.toString()}&token=${token}`, '_blank')
}

// 新建调拨单
const handleAdd = () => {
  Object.assign(formData, {
    transfer_type: 'same_price',
    from_warehouse_id: null,
    to_warehouse_id: null,
    handler: '',
    remark: '',
    items: []
  })
  dialogVisible.value = true
}

// 查看详情
const handleView = async (row) => {
  try {
    const res = await getTransferDetail(row.id)
    if (res.code === 200) {
      currentOrder.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('获取调拨单详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

// 审核调拨单
const handleAudit = (row) => {
  ElMessageBox.confirm('确定要审核该调拨单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await auditTransfer(row.id)
      if (res.code === 200) {
        ElMessage.success('审核成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('审核失败')
    }
  }).catch(() => {})
}

// 删除调拨单
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该调拨单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteTransfer(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 调拨类型变更
const onTransferTypeChange = () => {
  // 切换类型时清空商品明细，避免数据不一致
  formData.items = []
}

// 调出仓库变更时，如果当前调入仓库与调出仓库相同则清空
const onFromWarehouseChange = () => {
  if (formData.to_warehouse_id === formData.from_warehouse_id) {
    formData.to_warehouse_id = null
  }
}

// 添加商品行
const addItem = () => {
  formData.items.push({
    product_id: null,
    product_name: '',
    product_code: '',
    quantity: 1,
    from_cost_price: 0,
    to_cost_price: 0
  })
}

// 删除商品行
const removeItem = (index) => {
  formData.items.splice(index, 1)
}

// 商品选择变更
const onProductChange = (productId, index) => {
  const product = products.value.find(p => p.id === productId)
  if (product) {
    formData.items[index].product_name = product.product_name
    formData.items[index].product_code = product.product_code || ''
    formData.items[index].from_cost_price = product.purchase_price || 0
    // 同价调拨时，调入成本价等于调出成本价
    if (formData.transfer_type === 'same_price') {
      formData.items[index].to_cost_price = formData.items[index].from_cost_price
    } else {
      formData.items[index].to_cost_price = 0
    }
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (formData.items.length === 0) {
      ElMessage.warning('请至少添加一个商品')
      return
    }

    submitLoading.value = true
    try {
      const data = {
        transfer_type: formData.transfer_type,
        from_warehouse_id: formData.from_warehouse_id,
        to_warehouse_id: formData.to_warehouse_id,
        handler: formData.handler,
        remark: formData.remark,
        total_quantity: totalQuantity.value,
        items: formData.items
      }
      const res = await createTransfer(data)
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
.inventory-transfer-page {
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

  .items-header {
    margin-bottom: 10px;
  }

  .items-table {
    margin-bottom: 15px;
  }

  .amount-summary {
    margin-top: 15px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;
    text-align: right;

    strong {
      color: #409eff;
      font-size: 16px;
    }
  }

  .detail-summary {
    margin-top: 20px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 4px;
  }
}
</style>
