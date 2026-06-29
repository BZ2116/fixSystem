<template>
  <div class="quote-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>报价管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExportQuote">导出</el-button>
            <el-button type="primary" :icon="Plus" @click="handleAdd">新增报价</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="报价单号/客户名称" clearable style="width: 220px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="(text, code) in statusMap" :key="code" :label="text" :value="parseInt(code)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchData">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading" @row-click="handleView">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="quote_no" label="报价单号" width="150">
          <template #default="{ row }">
            <el-link type="primary" @click.stop="handleView(row)">{{ row.quote_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户名称" min-width="120" />
        <el-table-column prop="contact_name" label="联系人" width="100" />
        <el-table-column prop="quote_date" label="报价日期" width="120" />
        <el-table-column prop="valid_until" label="有效期至" width="120" />
        <el-table-column prop="total_amount" label="总金额" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.total_amount">¥{{ row.total_amount.toFixed(2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="handleView(row)">查看</el-button>
            <el-button type="info" link size="small" @click.stop="handlePrint(row)">打印</el-button>
            <el-button type="warning" link size="small" @click.stop="handleEdit(row)" v-if="row.status === 0">编辑</el-button>
            <el-button type="success" link size="small" @click.stop="handleConfirm(row)" v-if="row.status === 0">确认</el-button>
            <el-button type="primary" link size="small" @click.stop="handleToWorkOrder(row)" v-if="row.status === 1">转工单</el-button>
            <el-button type="primary" link size="small" @click.stop="handleToReceive(row)" v-if="row.status === 1">转接件</el-button>
            <el-button type="primary" link size="small" @click.stop="handleToSales(row)" v-if="row.status === 1">转销售</el-button>
            <el-button type="danger" link size="small" @click.stop="handleDelete(row)" v-if="row.status === 0 || row.status === 2">删除</el-button>
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

    <!-- 新增/编辑报价对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" destroy-on-close>
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-divider content-position="left">基本信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户" prop="customer_name">
              <el-autocomplete
                v-model="formData.customer_name"
                :fetch-suggestions="searchCustomer"
                placeholder="输入客户名称或电话搜索"
                @select="onCustomerSelect"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="formData.contact_name" placeholder="联系人" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="报价日期" prop="quote_date">
              <el-date-picker v-model="formData.quote_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="有效期至" prop="valid_until">
              <el-date-picker v-model="formData.valid_until" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
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

        <el-divider content-position="left">报价明细</el-divider>

        <el-table :data="formData.items" border size="small" class="detail-table">
          <el-table-column label="商品选择" width="80" align="center">
            <template #default="{ row, $index }">
              <el-button type="primary" link size="small" @click="openProductSelector($index)">
                <el-icon><Search /></el-icon> 选择
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="商品名称" min-width="120">
            <template #default="{ row }">
              <el-input v-model="row.product_name" placeholder="商品名称" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="规格" width="100">
            <template #default="{ row }">
              <el-input v-model="row.spec" placeholder="规格" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="品牌" width="100">
            <template #default="{ row }">
              <el-input v-model="row.brand" placeholder="品牌" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="70">
            <template #default="{ row }">
              <el-input v-model="row.unit" placeholder="单位" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="80">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" @change="calcSubtotal(row)" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" controls-position="right" @change="calcSubtotal(row)" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="100" align="right">
            <template #default="{ row }">
              <span>¥{{ (row.subtotal || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeItem($index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-button type="primary" link @click="addItem" class="add-item-btn">
          <el-icon><Plus /></el-icon> 添加明细行
        </el-button>

        <el-row justify="end" class="total-row">
          <el-col :span="6">
            <el-statistic title="总金额" :value="totalAmount" :precision="2" prefix="¥" />
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 报价详情对话框 -->
    <el-dialog v-model="detailVisible" title="报价详情" width="1000px" destroy-on-close>
      <div style="display: flex; gap: 20px;">
        <!-- 左侧主内容 -->
        <div style="flex: 1;">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="报价单号">{{ currentOrder.quote_no }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(currentOrder.status)">{{ currentOrder.status_text }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="客户名称">{{ currentOrder.customer_name }}</el-descriptions-item>
            <el-descriptions-item label="联系人">{{ currentOrder.contact_name || '无' }}</el-descriptions-item>
            <el-descriptions-item label="联系电话">{{ currentOrder.phone || currentOrder.customer_phone || '无' }}</el-descriptions-item>
            <el-descriptions-item label="报价日期">{{ currentOrder.quote_date }}</el-descriptions-item>
            <el-descriptions-item label="地址" :span="2">{{ currentOrder.address || '无' }}</el-descriptions-item>
            <el-descriptions-item label="有效期至">{{ currentOrder.valid_until || '无' }}</el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">{{ currentOrder.remark || '无' }}</el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">报价明细</el-divider>

          <el-table :data="currentOrder.items || []" size="small" border>
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="product_name" label="商品名称" min-width="150" show-overflow-tooltip />
            <el-table-column prop="spec" label="规格" width="100" />
            <el-table-column prop="brand" label="品牌" width="100" />
            <el-table-column prop="unit" label="单位" width="60" align="center" />
            <el-table-column prop="quantity" label="数量" width="70" align="center" />
            <el-table-column prop="unit_price" label="单价" width="100" align="right">
              <template #default="{ row }">¥{{ Number(row.unit_price || 0).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="subtotal" label="小计" width="100" align="right">
              <template #default="{ row }">¥{{ Number(row.subtotal || 0).toFixed(2) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!currentOrder.items || currentOrder.items.length === 0" description="暂无明细" :image-size="40" />
        </div>

        <!-- 右侧汇总 -->
        <div style="width: 200px;">
          <el-card shadow="never">
            <el-statistic title="总金额" :value="Number(currentOrder.total_amount || 0)" :precision="2" prefix="¥" />
            <el-divider />
            <p style="font-size: 13px; color: #606266;">人工费：¥{{ Number(currentOrder.labor_cost || 0).toFixed(2) }}</p>
            <p style="font-size: 13px; color: #606266;">材料费：¥{{ Number(currentOrder.material_cost || 0).toFixed(2) }}</p>
            <p style="font-size: 13px; color: #606266;">其他费用：¥{{ Number(currentOrder.other_cost || 0).toFixed(2) }}</p>
          </el-card>
        </div>
      </div>
    </el-dialog>

    <!-- 商品选择对话框 -->
    <el-dialog v-model="productSelectorVisible" title="选择商品" width="800px" destroy-on-close>
      <el-form :inline="true" :model="productSearchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="productSearchForm.keyword" placeholder="商品名称/编码/型号" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="productSearchForm.category_id" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="cat in productCategories" :key="cat.id" :label="cat.category_name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchProducts">搜索</el-button>
          <el-button :icon="Refresh" @click="resetProductSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="productList" stripe border v-loading="productLoading" @row-click="selectProduct">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="product_code" label="商品编码" width="120" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column prop="unit_name" label="单位" width="70" />
        <el-table-column prop="sale_price" label="售价" width="100" align="right">
          <template #default="{ row }">¥{{ row.sale_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="stock_quantity" label="库存" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.stock_quantity > 0 ? 'success' : 'danger'" size="small">
              {{ row.stock_quantity || 0 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="selectProduct(row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="productPagination.page"
        v-model:page-size="productPagination.pageSize"
        :total="productPagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @size-change="fetchProducts"
        @current-change="fetchProducts"
      />

      <template #footer>
        <el-button @click="productSelectorVisible = false">取消</el-button>
      </template>
    </el-dialog>

    <PrintDialog
      v-model:visible="printDialogVisible"
      template-type="quote"
      :print-data="printData"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Delete, Download } from '@element-plus/icons-vue'
import request from '@/api/request'
import { getQuoteList, getQuoteDetail, createQuote, updateQuote, deleteQuote, confirmQuote, toWorkOrder, toReceive, toSales } from '@/api/quote'
import PrintDialog from '@/components/PrintDialog.vue'

// 状态映射
const statusMap = {
  0: '待确认',
  1: '已确认',
  2: '已失效',
  3: '已转工单',
  4: '已转接件',
  5: '已转销售'
}

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])

// 打印相关
const printDialogVisible = ref(false)
const printData = ref({})

const searchForm = reactive({
  keyword: '',
  status: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新增报价')
const detailVisible = ref(false)

const formRef = ref(null)
const currentOrder = ref({})
const isEdit = ref(false)

// 创建空明细行
const createEmptyItem = () => ({
  product_name: '',
  spec: '',
  brand: '',
  unit: '',
  quantity: 1,
  unit_price: 0,
  subtotal: 0
})

const formData = reactive({
  customer_id: null,
  customer_name: '',
  contact_name: '',
  quote_date: '',
  valid_until: '',
  remark: '',
  items: [createEmptyItem()]
})

// 客户搜索
const searchCustomer = async (queryString, cb) => {
  if (!queryString) { cb([]); return }
  try {
    const res = await request.get('/customers', { params: { keyword: queryString, page_size: 10 } })
    if (res.code === 200) {
      const results = res.data.list.map(c => ({
        value: c.customer_name,
        id: c.id,
        contact: c.contact_name,
        phone: c.phone
      }))
      cb(results)
    } else {
      cb([])
    }
  } catch (error) { cb([]) }
}

const onCustomerSelect = (item) => {
  formData.customer_id = item.id
  formData.customer_name = item.value
  if (item.contact) formData.contact_name = item.contact
}

const rules = {
  customer_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  quote_date: [{ required: true, message: '请选择报价日期', trigger: 'change' }],
  valid_until: [{ required: true, message: '请选择有效期', trigger: 'change' }]
}

// 商品选择相关
const productSelectorVisible = ref(false)
const productLoading = ref(false)
const productList = ref([])
const productCategories = ref([])
const currentItemIndex = ref(0)

const productSearchForm = reactive({
  keyword: '',
  category_id: null
})

const productPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 打开商品选择器
const openProductSelector = (index) => {
  currentItemIndex.value = index
  productSelectorVisible.value = true
  fetchProducts()
  fetchProductCategories()
}

// 获取商品列表
const fetchProducts = async () => {
  productLoading.value = true
  try {
    const res = await request.get('/products', {
      params: {
        keyword: productSearchForm.keyword,
        category_id: productSearchForm.category_id,
        page: productPagination.page,
        page_size: productPagination.pageSize
      }
    })
    if (res.code === 200) {
      productList.value = res.data.list
      productPagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取商品列表失败:', error)
  } finally {
    productLoading.value = false
  }
}

// 获取商品分类（树形结构转扁平列表）
const fetchProductCategories = async () => {
  try {
    const res = await request.get('/product/categories')
    if (res.code === 200) {
      // 将树形结构转为扁平列表
      const flatten = (nodes, result = []) => {
        if (!nodes) return result
        nodes.forEach(node => {
          result.push({ id: node.id, category_name: node.category_name })
          if (node.children && node.children.length > 0) {
            flatten(node.children, result)
          }
        })
        return result
      }
      productCategories.value = flatten(res.data)
    }
  } catch (error) {
    console.error('获取商品分类失败:', error)
  }
}

// 重置商品搜索
const resetProductSearch = () => {
  productSearchForm.keyword = ''
  productSearchForm.category_id = null
  productPagination.page = 1
  fetchProducts()
}

// 选择商品
const selectProduct = (product) => {
  const item = formData.items[currentItemIndex.value]
  item.product_name = product.product_name
  item.spec = product.specification || ''
  item.brand = product.brand || ''
  item.unit = product.unit_name || '个'
  item.unit_price = product.sale_price || 0
  item.subtotal = item.quantity * item.unit_price
  productSelectorVisible.value = false
  ElMessage.success('已选择商品：' + product.product_name)
}

// 状态标签颜色映射
const getStatusType = (status) => {
  const types = {
    0: 'warning',    // 待确认
    1: 'success',    // 已确认
    2: 'info',       // 已失效
    3: 'primary',    // 已转工单
    4: 'primary',    // 已转接件
    5: 'primary'     // 已转销售
  }
  return types[status] || 'info'
}

// 计算小计
const calcSubtotal = (row) => {
  row.subtotal = (row.quantity || 0) * (row.unit_price || 0)
}

// 总金额自动汇总
const totalAmount = computed(() => {
  return formData.items.reduce((sum, item) => {
    return sum + (item.subtotal || 0)
  }, 0)
})

// 添加明细行
const addItem = () => {
  formData.items.push(createEmptyItem())
}

// 删除明细行
const removeItem = (index) => {
  if (formData.items.length <= 1) {
    ElMessage.warning('至少保留一条明细')
    return
  }
  formData.items.splice(index, 1)
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      status: searchForm.status
    }
    const res = await getQuoteList(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取报价列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 新增
const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增报价'
  Object.assign(formData, {
    customer_name: '',
    contact_name: '',
    quote_date: '',
    valid_until: '',
    remark: '',
    items: [createEmptyItem()]
  })
  dialogVisible.value = true
}

// 编辑
const handleEdit = async (row) => {
  try {
    const res = await getQuoteList({ id: row.id })
    if (res.code === 200) {
      const detail = res.data.list?.[0] || res.data
      isEdit.value = true
      dialogTitle.value = '编辑报价'
      Object.assign(formData, {
        customer_id: detail.customer_id || null,
        customer_name: detail.customer_name,
        contact_name: detail.contact_name,
        quote_date: detail.quote_date,
        valid_until: detail.valid_until,
        remark: detail.remark,
        items: (detail.items && detail.items.length > 0) ? detail.items : [createEmptyItem()]
      })
      currentOrder.value = detail
      dialogVisible.value = true
    }
  } catch (error) {
    console.error('获取报价详情失败:', error)
  }
}

// 查看详情
const handleView = async (row) => {
  console.log('查看报价详情, row:', row)
  try {
    const res = await getQuoteDetail(row.id)
    console.log('报价详情返回:', res)
    if (res && res.code === 200 && res.data) {
      currentOrder.value = res.data
      detailVisible.value = true
      console.log('对话框已打开, currentOrder:', currentOrder.value)
    } else {
      ElMessage.warning('获取报价详情失败：数据格式错误')
    }
  } catch (error) {
    console.error('获取报价详情失败:', error)
    ElMessage.error('获取报价详情失败：' + (error.message || '未知错误'))
  }
}

const handlePrint = async (row) => {
  try {
    const res = await getQuoteDetail(row.id)
    if (res && res.code === 200 && res.data) {
      const data = res.data
      let itemsHtml = ''
      if (data.items && data.items.length > 0) {
        itemsHtml = '<table class="print-table"><thead><tr><th>商品</th><th>规格</th><th>单位</th><th>数量</th><th>单价</th><th>金额</th></tr></thead><tbody>' +
          data.items.map(item => `<tr><td>${item.product_name || ''}</td><td>${item.specification || item.spec || ''}</td><td>${item.unit || ''}</td><td>${item.quantity || 0}</td><td>${(item.unit_price || item.price || 0).toFixed(2)}</td><td>${(item.subtotal || item.amount || 0).toFixed(2)}</td></tr>`).join('') +
          '</tbody></table>'
      }
      printData.value = {
        order_no: data.quote_no || '',
        order_date: data.quote_date || '',
        customer_name: data.customer_name || '',
        customer_phone: data.phone || data.customer_phone || '',
        customer_address: data.address || '',
        total_amount: (data.total_amount || 0).toFixed(2),
        items_detail: itemsHtml,
        remark: data.remark || '',
        status_name: data.status_text || '',
        operator_name: data.operator_name || '',
        valid_until: data.valid_until || ''
      }
      printDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取打印数据失败:', error)
    ElMessage.error('获取打印数据失败')
  }
}

// 确认报价
const handleConfirm = (row) => {
  ElMessageBox.confirm('确认该报价单？确认后将不可修改。', '确认报价', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await confirmQuote(row.id)
      if (res.code === 200) {
        ElMessage.success('报价已确认')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('确认操作失败')
    }
  }).catch(() => {})
}

// 转工单
const handleToWorkOrder = (row) => {
  ElMessageBox.confirm('确认将该报价单转为工单？', '转工单确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await toWorkOrder(row.id)
      if (res.code === 200) {
        ElMessage.success('已成功转为工单')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('转工单操作失败')
    }
  }).catch(() => {})
}

// 转接件
const handleToReceive = (row) => {
  ElMessageBox.confirm('确认将该报价单转为接件单？', '转接件确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await toReceive(row.id)
      if (res.code === 200) {
        ElMessage.success('已成功转为接件单')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('转接件操作失败')
    }
  }).catch(() => {})
}

// 转销售
const handleToSales = (row) => {
  ElMessageBox.confirm('确认将该报价单转为销售单？', '转销售确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await toSales(row.id)
      if (res.code === 200) {
        ElMessage.success('已成功转为销售单')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('转销售操作失败')
    }
  }).catch(() => {})
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm('确认删除该报价单？此操作不可撤销。', '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteQuote(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('删除操作失败')
    }
  }).catch(() => {})
}

// 重置搜索
const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.status = null
  fetchData()
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 校验明细行
    const hasEmptyItem = formData.items.some(item => !item.product_name)
    if (hasEmptyItem) {
      ElMessage.warning('请填写完整的明细信息')
      return
    }

    submitLoading.value = true
    try {
      const submitData = {
        ...formData,
        total_amount: totalAmount.value
      }
      let res
      if (isEdit.value) {
        res = await updateQuote(currentOrder.value.id, submitData)
      } else {
        res = await createQuote(submitData)
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

// 导出报价单
const handleExportQuote = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.status != null) params.append('status', searchForm.status)
  const token = localStorage.getItem('token') || ''
  window.open(`/api/quotes/export?${params.toString()}&token=${token}`, '_blank')
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.quote-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .detail-table {
    margin-bottom: 10px;
  }

  .add-item-btn {
    margin-bottom: 16px;
  }

  .total-row {
    margin-top: 10px;
    padding: 10px 0;
    border-top: 1px solid #ebeef5;
  }
}
</style>
