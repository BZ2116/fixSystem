<template>
  <div class="product-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>商品管理</span>
          <div>
            <el-button type="success" :icon="Upload" @click="handleImport" style="margin-right: 10px">导入</el-button>
            <el-button type="warning" :icon="Download" @click="handleExport" style="margin-right: 10px">导出</el-button>
            <el-button type="success" @click="handlePrintBarcode" style="margin-right: 10px">打印条码</el-button>
            <el-button type="primary" :icon="Plus" @click="handleAdd">新增商品</el-button>
          </div>
        </div>
        <!-- 批量操作工具栏 -->
        <div v-if="selectedProducts.length > 0" class="batch-toolbar">
          <el-dropdown split-button type="primary" @click="handleBatchCategory">
            批量修改分类
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleBatchPrice">批量价格</el-dropdown-item>
                <el-dropdown-item @click="handleBatchStockWarning">批量库存预警</el-dropdown-item>
                <el-dropdown-item @click="handleBatchSort">批量排序</el-dropdown-item>
                <el-dropdown-item divided @click="handleBatchEnable">批量启用</el-dropdown-item>
                <el-dropdown-item @click="handleBatchDisable">批量禁用</el-dropdown-item>
                <el-dropdown-item divided @click="handleBatchDelete" style="color: #f56c6c">批量删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-tag type="info" style="margin-left: 10px">已选择 {{ selectedProducts.length }} 项</el-tag>
        </div>
      </template>
      
      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="商品名称/拼音/条码/编码" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="searchForm.category_id" placeholder="选择分类" clearable style="width: 150px">
            <el-option v-for="item in categoryList" :key="item.id" :label="item.category_name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="product_code" label="商品编码" width="130" />
        <el-table-column prop="barcode" label="条码" width="130" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="unit_name" label="单位" width="80" />
        <el-table-column prop="purchase_price" label="采购价" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.purchase_price?.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column prop="sale_price" label="销售价" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.sale_price?.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column prop="current_stock" label="库存" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.current_stock <= row.min_stock ? 'danger' : 'success'" size="small">
              {{ row.current_stock }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-button type="success" link @click="handlePrintSingle(row)">打印条码</el-button>
            <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">删除</el-button>
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
    
    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="商品名称" prop="product_name">
              <el-input v-model="form.product_name" placeholder="请输入商品名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="条码" prop="barcode">
              <el-input v-model="form.barcode" placeholder="请输入条码" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="商品分类" prop="category_id">
              <el-select v-model="form.category_id" placeholder="选择分类" style="width: 100%" clearable>
                <el-option v-for="item in categoryList" :key="item.id" :label="item.category_name" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品牌" prop="brand">
              <el-input v-model="form.brand" placeholder="请输入品牌" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="规格型号" prop="specification">
              <el-input v-model="form.specification" placeholder="请输入规格型号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="商品编码" prop="product_code">
              <el-input v-model="form.product_code" :placeholder="form.id ? '' : '自动生成'" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 多单位设置 -->
        <el-divider content-position="left">
          多单位设置
          <el-button type="primary" link size="small" :icon="Plus" @click="addUnit" style="margin-left: 10px">添加单位</el-button>
        </el-divider>
        <el-table :data="form.units" border size="small" v-if="form.units.length > 0" style="margin-bottom: 16px">
          <el-table-column label="单位" min-width="150">
            <template #default="{ row }">
              <el-select v-model="row.unit_id" placeholder="选择单位" filterable style="width: 100%">
                <el-option v-for="u in unitList" :key="u.id" :label="u.unit_name" :value="u.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="换算率" width="160">
            <template #default="{ row }">
              <el-input-number v-model="row.conversion_rate" :min="0.001" :precision="3" :controls="false" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="默认" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.is_default" :true-value="1" :false-value="0" @change="handleDefaultChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeUnit($index)" :disabled="form.units.length <= 1">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂未设置多单位" :image-size="40" />
        
        <el-divider />
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="采购价" prop="purchase_price">
              <el-input-number v-model="form.purchase_price" :min="0" :precision="4" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="销售价" prop="sale_price">
              <el-input-number v-model="form.sale_price" :min="0" :precision="4" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="成本价" prop="cost_price">
              <el-input-number v-model="form.cost_price" :min="0" :precision="4" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="最低库存" prop="min_stock">
              <el-input-number v-model="form.min_stock" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最高库存" prop="max_stock">
              <el-input-number v-model="form.max_stock" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="导入商品" width="500px">
      <el-upload
        ref="uploadRef"
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".xlsx,.xls"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">支持 .xlsx, .xls 格式文件</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImportSubmit">导入</el-button>
      </template>
    </el-dialog>

    <!-- 条码打印对话框 -->
    <LabelPrintDialog
      v-model:visible="barcodePrintVisible"
      label-type="product"
      :label-data="barcodePrintProducts"
    />
    
    <!-- 批量操作对话框 -->
    <BatchOperationDialog
      v-model="batchDialogVisible"
      :operation-type="batchOperationType"
      :selected-count="selectedProducts.length"
      :category-options="categoryList"
      :loading="batchLoading"
      @confirm="handleBatchConfirm"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus, Search, Refresh, Edit, Delete, Upload, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getProductList, createProduct, updateProduct, deleteProduct, getProductDetail,
  importProducts, exportProducts, getProductCategories, getProductUnits
} from '@/api/product'
import LabelPrintDialog from '@/components/LabelPrintDialog.vue'
import BatchOperationDialog from '@/components/BatchOperationDialog.vue'
import {
  batchUpdateCategory,
  batchUpdatePrice,
  batchUpdateStockWarning,
  batchUpdateSort,
  batchDisable,
  batchEnable,
  batchDelete
} from '@/utils/batchOperations'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增商品')
const formRef = ref()
const importDialogVisible = ref(false)
const uploadRef = ref()
const importFile = ref(null)

// 分类和单位列表
const categoryList = ref([])
const unitList = ref([])

// 默认单位选项（当接口未返回数据时使用）
const defaultUnitOptions = [
  '个', '台', '套', '件', '箱', '包', '米', '根', '条', '张',
  '块', '片', '只', '对', '把', '支', '瓶', '盒', '卷',
  '公斤', '克', '升', '毫升'
]

const searchForm = reactive({
  keyword: '',
  category_id: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  id: null,
  product_name: '',
  barcode: '',
  category_id: null,
  category_name: '',
  brand: '',
  specification: '',
  product_code: '',
  purchase_price: 0,
  sale_price: 0,
  cost_price: 0,
  min_stock: 0,
  max_stock: 100,
  remark: '',
  units: []
})

const formRules = {
  product_name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getProductList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      category_id: searchForm.category_id
    })
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取商品列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 将树形分类列表转换为带层级缩进的扁平列表（后端返回的是树形结构）
const flattenCategories = (tree, level = 0) => {
  const result = []
  tree.forEach(item => {
    const prefix = level > 0 ? '　'.repeat(level) + '└─ ' : ''
    result.push({
      id: item.id,
      category_name: prefix + item.category_name,
      parent_id: item.parent_id,
      sort_order: item.sort_order
    })
    // 递归展开子分类
    if (item.children && item.children.length > 0) {
      result.push(...flattenCategories(item.children, level + 1))
    }
  })
  return result
}

const fetchCategories = async () => {
  try {
    const res = await getProductCategories()
    if (res.code === 200) {
      // 后端返回树形结构，转换为带层级缩进的扁平列表
      categoryList.value = flattenCategories(res.data || [])
    }
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const fetchUnits = async () => {
  try {
    const res = await getProductUnits()
    if (res.code === 200 && res.data && res.data.length > 0) {
      unitList.value = res.data
    } else {
      // 接口无数据时使用默认单位列表
      unitList.value = defaultUnitOptions.map((name, index) => ({
        id: index + 1,
        unit_name: name
      }))
    }
  } catch (error) {
    console.error('获取单位失败，使用默认单位列表:', error)
    unitList.value = defaultUnitOptions.map((name, index) => ({
      id: index + 1,
      unit_name: name
    }))
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.category_id = null
  handleSearch()
}

const handleAdd = () => {
  dialogTitle.value = '新增商品'
  dialogVisible.value = true
  addUnit()
}

const handleEdit = async (row) => {
  dialogTitle.value = '编辑商品'
  try {
    // 调用详情API获取完整数据（包括units）
    const res = await getProductDetail(row.id)
    if (res.code === 200) {
      const detail = res.data
      Object.assign(form, {
        id: detail.id,
        product_name: detail.product_name || '',
        barcode: detail.barcode || '',
        category_id: detail.category_id || null,
        category_name: detail.category_name || '',
        brand: detail.brand || '',
        specification: detail.specification || '',
        product_code: detail.product_code || '',
        purchase_price: detail.purchase_price || 0,
        sale_price: detail.sale_price || 0,
        cost_price: detail.cost_price || 0,
        min_stock: detail.min_stock || 0,
        max_stock: detail.max_stock || 100,
        remark: detail.remark || '',
        units: detail.units && detail.units.length > 0 ? detail.units.map(u => ({
          unit_id: u.unit_id || null,
          unit_name: u.unit_name || '',
          conversion_rate: u.conversion_rate || 1,
          is_default: u.is_default || 0
        })) : []
      })
      if (!form.units || form.units.length === 0) {
        addUnit()
      }
      dialogVisible.value = true
    }
  } catch (error) {
    console.error('获取商品详情失败:', error)
    // 降级：使用列表行数据
    Object.assign(form, row)
    if (!form.units || form.units.length === 0) {
      addUnit()
    }
    dialogVisible.value = true
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', { type: 'warning' })
    const res = await deleteProduct(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

const addUnit = () => {
  form.units.push({
    unit_id: null,
    conversion_rate: 1,
    is_default: form.units.length === 0 ? 1 : 0
  })
}

const removeUnit = (index) => {
  if (form.units.length <= 1) {
    ElMessage.warning('至少需要保留一个单位')
    return
  }
  const wasDefault = form.units[index].is_default === 1
  form.units.splice(index, 1)
  // 如果删除的是默认单位，重新设置第一个为默认
  if (wasDefault && form.units.length > 0) {
    form.units[0].is_default = 1
  }
}

// 处理默认单位变更
const handleDefaultChange = (changedRow) => {
  if (changedRow.is_default === 1) {
    // 将其他单位设为非默认
    form.units.forEach(u => {
      if (u !== changedRow) {
        u.is_default = 0
      }
    })
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    // 验证单位
    if (form.units.some(u => !u.unit_id)) {
      ElMessage.error('请选择单位')
      return
    }
    
    // 设置分类名称
    const category = categoryList.value.find(c => c.id === form.category_id)
    if (category) form.category_name = category.category_name
    
    try {
      const submitData = { ...form }
      // 处理多单位数据
      if (submitData.units && submitData.units.length > 0) {
        submitData.units = submitData.units.map(u => ({
          unit_id: u.unit_id,
          unit_name: unitList.value.find(item => item.id === u.unit_id)?.unit_name || '',
          conversion_rate: u.conversion_rate || 1,
          is_default: u.is_default || 0
        }))
      }
      
      let res
      if (form.id) {
        res = await updateProduct(form.id, submitData)
      } else {
        res = await createProduct(submitData)
      }
      
      if (res.code === 200) {
        ElMessage.success(dialogTitle.value + '成功')
        dialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      console.error('操作失败:', error)
      ElMessage.error('保存失败：' + (error.message || '未知错误'))
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    id: null,
    product_name: '',
    barcode: '',
    category_id: null,
    category_name: '',
    brand: '',
    specification: '',
    product_code: '',
    purchase_price: 0,
    sale_price: 0,
    cost_price: 0,
    min_stock: 0,
    max_stock: 100,
    remark: '',
    units: []
  })
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  fetchData()
}

const handlePageChange = (val) => {
  pagination.page = val
  fetchData()
}

const handleImport = () => {
  importDialogVisible.value = true
}

const handleFileChange = (file) => {
  importFile.value = file.raw
}

const handleImportSubmit = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  try {
    const res = await importProducts(importFile.value)
    if (res.code === 200) {
      ElMessage.success('导入成功')
      importDialogVisible.value = false
      fetchData()
    }
  } catch (error) {
    console.error('导入失败:', error)
  }
}

const handleExport = async () => {
  try {
    const response = await exportProducts()
    const blob = response.data
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '商品列表.xlsx'
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// ==================== 条码打印功能 ====================
const selectedProducts = ref([])

const handleSelectionChange = (selection) => {
  selectedProducts.value = selection
}

const barcodePrintVisible = ref(false)
const barcodePrintProducts = ref([])

// 批量打印条码
const handlePrintBarcode = () => {
  if (selectedProducts.value.length === 0) {
    ElMessage.warning('请先勾选要打印条码的商品')
    return
  }
  barcodePrintProducts.value = [...selectedProducts.value]
  barcodePrintVisible.value = true
}

// 单条打印条码
const handlePrintSingle = (row) => {
  barcodePrintProducts.value = [row]
  barcodePrintVisible.value = true
}

// ==================== 批量操作功能 ====================
const batchDialogVisible = ref(false)
const batchOperationType = ref('')
const batchLoading = ref(false)

// 打开批量操作对话框
const openBatchDialog = (type) => {
  if (selectedProducts.value.length === 0) {
    ElMessage.warning('请先勾选要操作的商品')
    return
  }
  batchOperationType.value = type
  batchDialogVisible.value = true
}

// 批量操作按钮处理
const handleBatchCategory = () => openBatchDialog('category')
const handleBatchPrice = () => openBatchDialog('price')
const handleBatchStockWarning = () => openBatchDialog('stock_warning')
const handleBatchSort = () => openBatchDialog('sort')
const handleBatchDisable = () => openBatchDialog('disable')
const handleBatchEnable = () => openBatchDialog('enable')
const handleBatchDelete = () => openBatchDialog('delete')

// 批量操作确认
const handleBatchConfirm = async (type, data) => {
  batchLoading.value = true
  try {
    let success = false
    switch (type) {
      case 'category':
        success = await batchUpdateCategory(selectedProducts.value, data.category_id, categoryList.value.find(c => c.id === data.category_id)?.category_name)
        break
      case 'price':
        success = await batchUpdatePrice(selectedProducts.value, data)
        break
      case 'stock_warning':
        success = await batchUpdateStockWarning(selectedProducts.value, data.min_stock, data.max_stock)
        break
      case 'sort':
        success = await batchUpdateSort(selectedProducts.value, data.sort_order)
        break
      case 'disable':
        success = await batchDisable(selectedProducts.value)
        break
      case 'enable':
        success = await batchEnable(selectedProducts.value)
        break
      case 'delete':
        success = await batchDelete(selectedProducts.value)
        break
    }
    if (success) {
      batchDialogVisible.value = false
      fetchData()
      selectedProducts.value = []
    }
  } finally {
    batchLoading.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchCategories()
  fetchUnits()
})
</script>

<style lang="scss" scoped>
.product-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .batch-toolbar {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #ebeef5;
    display: flex;
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
  
  .unit-row {
    margin-bottom: 10px;
  }
}
</style>
