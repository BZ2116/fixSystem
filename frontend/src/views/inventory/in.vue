<template>
  <div class="inventory-in-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>入库管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExportInbound" v-permission="'inventory-in:view'">导出</el-button>
            <el-button type="primary" :icon="Plus" @click="handleAdd" v-permission="'inventory-in:add'">新增入库</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="入库单号/供应商/采购单号"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="入库类型">
          <el-select v-model="searchForm.in_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="采购入库" :value="1" />
            <el-option label="退货入库" :value="2" />
            <el-option label="其他入库" :value="3" />
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
        <el-table-column prop="in_no" label="入库单号" width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.in_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="in_type" label="入库类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getInTypeType(row.in_type)" size="small">{{ getInTypeText(row.in_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_no" label="来源单号" width="150" />
        <el-table-column prop="supplier_name" label="供应商" min-width="150" />
        <el-table-column prop="warehouse_name" label="仓库" width="120" />
        <el-table-column prop="total_quantity" label="总数量" width="90" align="center" />
        <el-table-column prop="total_amount" label="总金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">详情</el-button>
            <el-button type="success" link size="small" @click="handleAudit(row)" v-if="row.status === 0" v-permission="'inventory-in:edit'">审核</el-button>
            <el-button type="danger" link size="small" @click="handleCancel(row)" v-if="row.status === 0" v-permission="'inventory-in:edit'">取消</el-button>
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

    <!-- 新增/编辑入库单弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑入库单' : '新增入库单'"
      width="950px"
      destroy-on-close
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="入库类型" prop="in_type">
              <el-select v-model="formData.in_type" placeholder="选择入库类型" style="width: 100%">
                <el-option label="采购入库" :value="1" />
                <el-option label="退货入库" :value="2" />
                <el-option label="其他入库" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="来源单号" prop="source_no">
              <el-input v-model="formData.source_no" placeholder="请输入来源单号" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="供应商" prop="supplier_id">
              <el-select v-model="formData.supplier_id" placeholder="选择供应商" filterable style="width: 100%">
                <el-option v-for="s in suppliers" :key="s.id" :label="s.supplier_name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="仓库" prop="warehouse_name">
              <el-input v-model="formData.warehouse_name" placeholder="请输入仓库名称" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="入库日期" prop="in_date">
              <el-date-picker
                v-model="formData.in_date"
                type="date"
                placeholder="选择日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">入库明细</el-divider>

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
          <el-table-column label="规格" width="100">
            <template #default="{ row }">
              <span>{{ row.specification || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="单位" width="80">
            <template #default="{ row }">
              <span>{{ row.unit || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="120">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.quantity" :min="1" :precision="0" style="width: 100%" @change="calculateItemAmount($index)" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" style="width: 100%" @change="calculateItemAmount($index)" />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.amount?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="amount-summary">
          <el-row :gutter="20">
            <el-col :span="6">
              <span>数量合计: <strong>{{ totalQuantity }}</strong></span>
            </el-col>
            <el-col :span="6">
              <span>金额合计: <strong>¥{{ totalAmount.toFixed(2) }}</strong></span>
            </el-col>
          </el-row>
        </div>

        <el-row :gutter="20" style="margin-top: 16px">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="备注信息" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="入库单详情" width="850px" destroy-on-close>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="入库单号">{{ currentOrder.in_no }}</el-descriptions-item>
        <el-descriptions-item label="入库类型">
          <el-tag :type="getInTypeType(currentOrder.in_type)">{{ getInTypeText(currentOrder.in_type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentOrder.status)">{{ getStatusText(currentOrder.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="来源单号">{{ currentOrder.source_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="供应商">
          {{ currentOrder.supplier_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="仓库">{{ currentOrder.warehouse_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="入库日期">{{ currentOrder.in_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentOrder.created_at }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">入库明细</el-divider>

      <el-table :data="currentOrder.items || []" border size="small">
        <el-table-column type="index" label="序号" width="50" align="center" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column prop="unit_price" label="单价" width="100" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="小计" width="100" align="right">
          <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
      </el-table>

      <div class="detail-summary">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="数量合计" :value="currentOrder.total_quantity || 0" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="金额合计" :value="currentOrder.total_amount || 0" :precision="2" prefix="¥" />
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
import request from '@/api/request'
import { getSupplierList } from '@/api/supplier'
import { getProductList } from '@/api/product'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const suppliers = ref([])
const products = ref([])

const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const currentOrder = ref({})

const searchForm = reactive({
  keyword: '',
  in_type: null,
  status: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  in_type: 1,
  source_no: '',
  supplier_id: null,
  warehouse_name: '',
  in_date: '',
  remark: '',
  items: []
})

const rules = {
  in_type: [{ required: true, message: '请选择入库类型', trigger: 'change' }],
  warehouse_name: [{ required: true, message: '请输入仓库名称', trigger: 'blur' }],
  in_date: [{ required: true, message: '请选择入库日期', trigger: 'change' }]
}

const totalQuantity = computed(() => {
  return formData.items.reduce((sum, item) => sum + (item.quantity || 0), 0)
})

const totalAmount = computed(() => {
  return formData.items.reduce((sum, item) => sum + (item.amount || 0), 0)
})

const getInTypeType = (type) => {
  const types = { 1: 'primary', 2: 'success', 3: 'info' }
  return types[type] || 'info'
}

const getInTypeText = (type) => {
  const texts = { 1: '采购入库', 2: '退货入库', 3: '其他入库' }
  return texts[type] || '未知'
}

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'primary', 2: 'success' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '待审核', 1: '已审核', 2: '已完成' }
  return texts[status] || '未知'
}

// 获取入库单列表
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      in_type: searchForm.in_type,
      status: searchForm.status
    }
    const res = await request.get('/inventory/in', { params })
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取入库单列表失败:', error)
    ElMessage.error('获取入库单列表失败')
  } finally {
    loading.value = false
  }
}

// 获取供应商列表
const fetchSuppliers = async () => {
  try {
    const res = await getSupplierList({ page_size: 1000 })
    if (res.code === 200) {
      suppliers.value = res.data.list
    }
  } catch (error) {
    console.error('获取供应商列表失败:', error)
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
  searchForm.in_type = null
  searchForm.status = null
  handleSearch()
}

// 新增入库单
const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    in_type: 1,
    source_no: '',
    supplier_id: null,
    warehouse_name: '',
    in_date: new Date().toISOString().split('T')[0],
    remark: '',
    items: []
  })
  dialogVisible.value = true
}

// 编辑入库单
const handleEdit = async (row) => {
  isEdit.value = true
  currentOrder.value = row
  try {
    // 调用详情API获取完整数据（包括items明细）
    const res = await request.get(`/inventory/in/${row.id}`)
    if (res.code === 200) {
      const detail = res.data
      Object.assign(formData, {
        in_type: detail.in_type,
        source_no: detail.source_no || '',
        supplier_id: detail.supplier_id ? Number(detail.supplier_id) : null,
        warehouse_name: detail.warehouse_name || '',
        in_date: detail.in_date || '',
        remark: detail.remark || '',
        items: (detail.items || []).map(item => ({
          ...item,
          product_id: item.product_id ? Number(item.product_id) : null
        }))
      })
    } else {
      // 降级使用列表行数据
      Object.assign(formData, {
        in_type: row.in_type,
        source_no: row.source_no || '',
        supplier_id: row.supplier_id ? Number(row.supplier_id) : null,
        warehouse_name: row.warehouse_name || '',
        in_date: row.in_date || '',
        remark: row.remark || '',
        items: row.items ? [...row.items.map(item => ({ ...item, product_id: item.product_id ? Number(item.product_id) : null }))] : []
      })
    }
  } catch (error) {
    console.error('获取入库单详情失败:', error)
    Object.assign(formData, {
      in_type: row.in_type,
      source_no: row.source_no || '',
      supplier_id: row.supplier_id ? Number(row.supplier_id) : null,
      warehouse_name: row.warehouse_name || '',
      in_date: row.in_date || '',
      remark: row.remark || '',
      items: row.items ? [...row.items.map(item => ({ ...item, product_id: item.product_id ? Number(item.product_id) : null }))] : []
    })
  }
  dialogVisible.value = true
}

// 查看详情
const handleView = async (row) => {
  try {
    const res = await request.get(`/inventory/in/${row.id}`)
    if (res.code === 200) {
      currentOrder.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('获取入库单详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

// 审核入库单
const handleAudit = (row) => {
  ElMessageBox.confirm('确定要审核该入库单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await request.post(`/inventory/in/${row.id}/audit`)
      if (res.code === 200) {
        ElMessage.success('审核成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('审核失败')
    }
  }).catch(() => {})
}

// 取消入库单
const handleCancel = (row) => {
  ElMessageBox.confirm('确定要取消该入库单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await request.delete(`/inventory/in/${row.id}`)
      if (res.code === 200) {
        ElMessage.success('取消成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('取消失败')
    }
  }).catch(() => {})
}

// 添加商品行
const addItem = () => {
  formData.items.push({
    product_id: null,
    product_name: '',
    specification: '',
    unit: '',
    quantity: 1,
    unit_price: 0,
    amount: 0
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
    formData.items[index].specification = product.specification
    formData.items[index].unit = product.unit
    formData.items[index].unit_price = product.purchase_price || 0
    calculateItemAmount(index)
  }
}

// 计算小计
const calculateItemAmount = (index) => {
  const item = formData.items[index]
  item.amount = (item.quantity || 0) * (item.unit_price || 0)
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
        in_type: formData.in_type,
        source_no: formData.source_no,
        supplier_id: formData.supplier_id,
        warehouse_name: formData.warehouse_name,
        in_date: formData.in_date,
        remark: formData.remark,
        total_quantity: totalQuantity.value,
        total_amount: totalAmount.value,
        items: formData.items
      }
      let res
      if (isEdit.value) {
        res = await request.put(`/inventory/in/${currentOrder.value.id}`, data)
      } else {
        res = await request.post('/inventory/in', data)
      }
      if (res.code === 200) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      ElMessage.error('操作失败')
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

// 导出入库单
const handleExportInbound = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.in_type != null) params.append('in_type', searchForm.in_type)
  if (searchForm.status != null) params.append('status', searchForm.status)
  const token = localStorage.getItem('token') || ''
  window.open(`/api/inbound/orders/export?${params.toString()}&token=${token}`, '_blank')
}

onMounted(() => {
  fetchData()
  fetchSuppliers()
  fetchProducts()
})
</script>

<style lang="scss" scoped>
.inventory-in-page {
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
      color: #f56c6c;
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
