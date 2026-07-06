<template>
  <div class="inventory-page">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 库存查询 -->
      <el-tab-pane label="库存查询" name="stock">
        <el-card shadow="never">
          <el-form :inline="true" :model="stockSearch" class="search-form">
            <el-form-item label="关键词">
              <el-input v-model="stockSearch.keyword" placeholder="商品名称/编码" clearable style="width: 200px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="fetchStock">搜索</el-button>
              <el-button type="success" :icon="Download" @click="handleExportStock" v-permission="'inventory:view'">导出</el-button>
            </el-form-item>
          </el-form>
          
          <el-table :data="stockData" stripe border v-loading="stockLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="product_code" label="商品编码" width="120" />
            <el-table-column prop="product_name" label="商品名称" min-width="150" />
            <el-table-column prop="warehouse_name" label="仓库" width="100" />
            <el-table-column prop="quantity" label="库存数量" width="100" align="right">
              <template #default="{ row }">
                <span :class="{ 'low-stock': row.quantity <= 0 }">{{ row.quantity }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="frozen_quantity" label="冻结数量" width="100" align="right" />
            <el-table-column prop="available_quantity" label="可用数量" width="100" align="right">
              <template #default="{ row }">
                <span :class="{ 'low-stock': row.available_quantity <= 0 }">{{ row.available_quantity }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="cost_price" label="成本价" width="100" align="right">
              <template #default="{ row }">¥{{ row.cost_price?.toFixed(2) || '0.00' }}</template>
            </el-table-column>
            <el-table-column prop="batch_no" label="批次号" width="100" />
          </el-table>
          
          <el-pagination
            v-model:current-page="stockPage.page"
            v-model:page-size="stockPage.pageSize"
            :total="stockPage.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            class="pagination"
            @size-change="fetchStock"
            @current-change="fetchStock"
          />
        </el-card>
      </el-tab-pane>
      
      <!-- 入库管理 -->
      <el-tab-pane label="入库管理" name="in">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>入库单列表</span>
              <el-button type="primary" :icon="Plus" @click="handleAddIn">新建入库单</el-button>
            </div>
          </template>
          
          <el-table :data="inData" stripe border v-loading="inLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="in_no" label="入库单号" width="150" />
            <el-table-column prop="in_type" label="入库类型" width="100">
              <template #default="{ row }">{{ inTypeMap[row.in_type] }}</template>
            </el-table-column>
            <el-table-column prop="supplier_name" label="供应商" width="150" />
            <el-table-column prop="warehouse_name" label="仓库" width="100" />
            <el-table-column prop="total_quantity" label="总数量" width="100" align="right" />
            <el-table-column prop="total_amount" label="总金额" width="120" align="right">
              <template #default="{ row }">¥{{ row.total_amount?.toFixed(2) || '0.00' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ statusMap[row.status] }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160" />
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="viewInOrder(row)">详情</el-button>
                <el-button type="success" link size="small" @click="auditInOrder(row)" v-if="row.status === 0">审核</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      
      <!-- 出库管理 -->
      <el-tab-pane label="出库管理" name="out">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>出库单列表</span>
              <el-button type="primary" :icon="Plus" @click="handleAddOut">新建出库单</el-button>
            </div>
          </template>
          
          <el-table :data="outData" stripe border v-loading="outLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="out_no" label="出库单号" width="150" />
            <el-table-column prop="out_type" label="出库类型" width="100">
              <template #default="{ row }">{{ outTypeMap[row.out_type] }}</template>
            </el-table-column>
            <el-table-column prop="customer_name" label="客户" width="150" />
            <el-table-column prop="warehouse_name" label="仓库" width="100" />
            <el-table-column prop="total_quantity" label="总数量" width="100" align="right" />
            <el-table-column prop="total_amount" label="总金额" width="120" align="right">
              <template #default="{ row }">¥{{ row.total_amount?.toFixed(2) || '0.00' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ statusMap[row.status] }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160" />
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="viewOutOrder(row)">详情</el-button>
                <el-button type="success" link size="small" @click="auditOutOrder(row)" v-if="row.status === 0">审核</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      
      <!-- 库存盘点 -->
      <el-tab-pane label="库存盘点" name="check">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>盘点单列表</span>
              <el-button type="primary" :icon="Plus" @click="handleAddCheck">新建盘点</el-button>
            </div>
          </template>
          
          <el-table :data="checkData" stripe border v-loading="checkLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="check_no" label="盘点单号" width="150" />
            <el-table-column prop="warehouse_name" label="仓库" width="100" />
            <el-table-column prop="check_date" label="盘点日期" width="120" />
            <el-table-column prop="total_quantity" label="商品数量" width="100" align="right" />
            <el-table-column prop="diff_quantity" label="差异数量" width="100" align="right">
              <template #default="{ row }">
                <span :class="{ 'diff-positive': row.diff_quantity > 0, 'diff-negative': row.diff_quantity < 0 }">
                  {{ row.diff_quantity }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="diff_amount" label="差异金额" width="120" align="right">
              <template #default="{ row }">
                <span :class="{ 'diff-positive': row.diff_amount > 0, 'diff-negative': row.diff_amount < 0 }">
                  ¥{{ row.diff_amount?.toFixed(2) || '0.00' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getCheckStatusType(row.status)">{{ checkStatusMap[row.status] }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 入库单对话框 -->
    <el-dialog v-model="inDialogVisible" title="新建入库单" width="800px" destroy-on-close>
      <el-form :model="inForm" :rules="inRules" ref="inFormRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="入库类型" prop="in_type">
              <el-select v-model="inForm.in_type" style="width: 100%">
                <el-option label="采购入库" :value="1" />
                <el-option label="退货入库" :value="2" />
                <el-option label="调拨入库" :value="3" />
                <el-option label="组装入库" :value="4" />
                <el-option label="其他入库" :value="5" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供应商">
              <el-select v-model="inForm.supplier_id" filterable placeholder="选择供应商" style="width: 100%">
                <el-option v-for="s in suppliers" :key="s.id" :label="s.supplier_name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">商品明细</el-divider>
        
        <el-table :data="inForm.items" border size="small">
          <el-table-column label="商品" min-width="200">
            <template #default="{ row, $index }">
              <el-autocomplete
                v-model="row.product_name"
                :fetch-suggestions="searchProduct"
                @select="(item) => selectProduct(item, $index, 'in')"
                placeholder="搜索商品"
                style="width: 100%"
              />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="100" align="right">
            <template #default="{ row }">¥{{ (row.quantity * row.unit_price).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="60" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeInItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-button type="primary" link :icon="Plus" @click="addInItem" class="mt-10">添加商品</el-button>
      </el-form>
      
      <template #footer>
        <el-button @click="inDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitInOrder" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 出库单对话框 -->
    <el-dialog v-model="outDialogVisible" title="新建出库单" width="800px" destroy-on-close>
      <el-form :model="outForm" :rules="outRules" ref="outFormRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="出库类型" prop="out_type">
              <el-select v-model="outForm.out_type" style="width: 100%">
                <el-option label="销售出库" :value="1" />
                <el-option label="维修领料" :value="2" />
                <el-option label="调拨出库" :value="3" />
                <el-option label="拆卸出库" :value="4" />
                <el-option label="其他出库" :value="5" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户">
              <el-select v-model="outForm.customer_id" filterable placeholder="选择客户" style="width: 100%">
                <el-option v-for="c in customers" :key="c.id" :label="c.customer_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">商品明细</el-divider>
        
        <el-table :data="outForm.items" border size="small">
          <el-table-column label="商品" min-width="200">
            <template #default="{ row, $index }">
              <el-autocomplete
                v-model="row.product_name"
                :fetch-suggestions="searchProduct"
                @select="(item) => selectProduct(item, $index, 'out')"
                placeholder="搜索商品"
                style="width: 100%"
              />
            </template>
          </el-table-column>
          <el-table-column label="库存" width="80" align="right">
            <template #default="{ row }">{{ row.stock || '-' }}</template>
          </el-table-column>
          <el-table-column label="数量" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeOutItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-button type="primary" link :icon="Plus" @click="addOutItem" class="mt-10">添加商品</el-button>
      </el-form>
      
      <template #footer>
        <el-button @click="outDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitOutOrder" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Download } from '@element-plus/icons-vue'
import request from '@/api/request'

const activeTab = ref('stock')

// 类型映射
const inTypeMap = { 1: '采购入库', 2: '退货入库', 3: '调拨入库', 4: '组装入库', 5: '其他入库' }
const outTypeMap = { 1: '销售出库', 2: '维修领料', 3: '调拨出库', 4: '拆卸出库', 5: '其他出库' }
const statusMap = { 0: '待审核', 1: '已审核', 2: '已完成' }
const checkStatusMap = { 0: '待盘点', 1: '盘点中', 2: '已完成' }

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'info', 2: 'success' }
  return types[status] || 'info'
}

const getCheckStatusType = (status) => {
  const types = { 0: 'info', 1: 'warning', 2: 'success' }
  return types[status] || 'info'
}

// 库存查询
const stockLoading = ref(false)
const stockData = ref([])
const stockSearch = reactive({ keyword: '' })
const stockPage = reactive({ page: 1, pageSize: 20, total: 0 })

// 入库管理
const inLoading = ref(false)
const inData = ref([])
const inDialogVisible = ref(false)
const inFormRef = ref(null)
const inForm = reactive({
  in_type: 1,
  supplier_id: null,
  items: []
})
const inRules = {
  in_type: [{ required: true, message: '请选择入库类型', trigger: 'change' }]
}

// 出库管理
const outLoading = ref(false)
const outData = ref([])
const outDialogVisible = ref(false)
const outFormRef = ref(null)
const outForm = reactive({
  out_type: 1,
  customer_id: null,
  items: []
})
const outRules = {
  out_type: [{ required: true, message: '请选择出库类型', trigger: 'change' }]
}

// 盘点管理
const checkLoading = ref(false)
const checkData = ref([])

// 基础数据
const suppliers = ref([])
const customers = ref([])
const submitLoading = ref(false)

// 获取库存
const fetchStock = async () => {
  stockLoading.value = true
  try {
    const res = await request.get('/inventory/stock', {
      params: { ...stockSearch, ...stockPage }
    })
    if (res.code === 200) {
      stockData.value = res.data.list
      stockPage.total = res.data.total
    }
  } finally {
    stockLoading.value = false
  }
}

// 导出库存
const handleExportStock = () => {
  const params = new URLSearchParams()
  if (stockSearch.keyword) params.append('keyword', stockSearch.keyword)
  const token = localStorage.getItem('token') || ''
  window.open(`/api/inventory/stock/export?${params.toString()}&token=${token}`, '_blank')
}

// 获取入库单
const fetchInList = async () => {
  inLoading.value = true
  try {
    const res = await request.get('/inventory/in')
    if (res.code === 200) {
      inData.value = res.data.list
    }
  } finally {
    inLoading.value = false
  }
}

// 获取出库单
const fetchOutList = async () => {
  outLoading.value = true
  try {
    const res = await request.get('/inventory/out')
    if (res.code === 200) {
      outData.value = res.data.list
    }
  } finally {
    outLoading.value = false
  }
}

// 获取盘点单
const fetchCheckList = async () => {
  checkLoading.value = true
  try {
    const res = await request.get('/inventory/check')
    if (res.code === 200) {
      checkData.value = res.data.list
    }
  } finally {
    checkLoading.value = false
  }
}

// 获取基础数据
const fetchSuppliers = async () => {
  try {
    const res = await request.get('/suppliers', { params: { page_size: 100 } })
    if (res.code === 200) suppliers.value = res.data.list
  } catch (e) {}
}

const fetchCustomers = async () => {
  try {
    const res = await request.get('/customers', { params: { page_size: 100 } })
    if (res.code === 200) customers.value = res.data.list
  } catch (e) {}
}

// 搜索商品
const searchProduct = async (queryString, cb) => {
  if (!queryString) { cb([]); return }
  try {
    const res = await request.get('/products', {
      params: { keyword: queryString, page_size: 20 }
    })
    if (res.code === 200) {
      cb(res.data.list.map(p => ({
        value: p.product_name,
        id: p.id,
        product_code: p.product_code,
        sale_price: p.sale_price,
        cost_price: p.cost_price,
        current_stock: p.current_stock
      })))
    }
  } catch (e) { cb([]) }
}

const selectProduct = (item, index, type) => {
  if (type === 'in') {
    inForm.items[index].product_id = item.id
    inForm.items[index].product_code = item.product_code
    inForm.items[index].unit_price = item.cost_price || 0
  } else {
    outForm.items[index].product_id = item.id
    outForm.items[index].product_code = item.product_code
    outForm.items[index].unit_price = item.sale_price || 0
    outForm.items[index].stock = item.current_stock
  }
}

// 入库操作
const handleAddIn = () => {
  inForm.in_type = 1
  inForm.supplier_id = null
  inForm.items = [{ product_id: null, product_name: '', product_code: '', quantity: 1, unit_price: 0 }]
  inDialogVisible.value = true
}

const addInItem = () => {
  inForm.items.push({ product_id: null, product_name: '', product_code: '', quantity: 1, unit_price: 0 })
}

const removeInItem = (index) => {
  if (inForm.items.length > 1) {
    inForm.items.splice(index, 1)
  }
}

const submitInOrder = async () => {
  if (!inFormRef.value) return
  await inFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      const supplier = suppliers.value.find(s => s.id === inForm.supplier_id)
      const res = await request.post('/inventory/in', {
        ...inForm,
        supplier_name: supplier?.supplier_name,
        items: inForm.items.filter(i => i.product_id)
      })
      if (res.code === 200) {
        ElMessage.success('创建成功')
        inDialogVisible.value = false
        fetchInList()
      }
    } finally {
      submitLoading.value = false
    }
  })
}

const viewInOrder = async (row) => {
  try {
    const res = await request.get(`/inventory/in/${row.id}`)
    if (res.code === 200) {
      ElMessageBox.alert(
        `<pre>${JSON.stringify(res.data, null, 2)}</pre>`,
        '入库单详情',
        { dangerouslyUseHTMLString: true }
      )
    }
  } catch (e) {}
}

const auditInOrder = async (row) => {
  try {
    await ElMessageBox.confirm('确认审核该入库单？审核后将自动入库。', '提示', { type: 'warning' })
    const res = await request.post(`/inventory/in/${row.id}/audit`, {})
    if (res.code === 200) {
      ElMessage.success('审核成功')
      fetchInList()
      fetchStock()
    }
  } catch (e) {}
}

// 出库操作
const handleAddOut = () => {
  outForm.out_type = 1
  outForm.customer_id = null
  outForm.items = [{ product_id: null, product_name: '', product_code: '', quantity: 1, unit_price: 0, stock: 0 }]
  outDialogVisible.value = true
}

const addOutItem = () => {
  outForm.items.push({ product_id: null, product_name: '', product_code: '', quantity: 1, unit_price: 0, stock: 0 })
}

const removeOutItem = (index) => {
  if (outForm.items.length > 1) {
    outForm.items.splice(index, 1)
  }
}

const submitOutOrder = async () => {
  if (!outFormRef.value) return
  await outFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      const customer = customers.value.find(c => c.id === outForm.customer_id)
      const res = await request.post('/inventory/out', {
        ...outForm,
        customer_name: customer?.customer_name,
        items: outForm.items.filter(i => i.product_id)
      })
      if (res.code === 200) {
        ElMessage.success('创建成功')
        outDialogVisible.value = false
        fetchOutList()
      }
    } finally {
      submitLoading.value = false
    }
  })
}

const viewOutOrder = async (row) => {
  try {
    const res = await request.get(`/inventory/out/${row.id}`)
    if (res.code === 200) {
      ElMessageBox.alert(
        `<pre>${JSON.stringify(res.data, null, 2)}</pre>`,
        '出库单详情',
        { dangerouslyUseHTMLString: true }
      )
    }
  } catch (e) {}
}

const auditOutOrder = async (row) => {
  try {
    await ElMessageBox.confirm('确认审核该出库单？审核后将自动出库。', '提示', { type: 'warning' })
    const res = await request.post(`/inventory/out/${row.id}/audit`, {})
    if (res.code === 200) {
      ElMessage.success('审核成功')
      fetchOutList()
      fetchStock()
    }
  } catch (e) {}
}

// 盘点操作
const handleAddCheck = async () => {
  try {
    await ElMessageBox.confirm('确认创建新的盘点单？将自动获取当前库存数据。', '提示', { type: 'info' })
    const res = await request.post('/inventory/check', {})
    if (res.code === 200) {
      ElMessage.success('盘点单创建成功')
      fetchCheckList()
    }
  } catch (e) {}
}

onMounted(() => {
  fetchStock()
  fetchInList()
  fetchOutList()
  fetchCheckList()
  fetchSuppliers()
  fetchCustomers()
})
</script>

<style lang="scss" scoped>
.inventory-page {
  .search-form {
    margin-bottom: 20px;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .low-stock {
    color: #f56c6c;
    font-weight: bold;
  }
  
  .diff-positive { color: #67c23a; }
  .diff-negative { color: #f56c6c; }
  
  .mt-10 { margin-top: 10px; }
}
</style>
