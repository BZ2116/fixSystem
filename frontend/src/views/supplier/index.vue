<template>
  <div class="supplier-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>供应商管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" v-permission="'supplier:view'" @click="handleExport">导出</el-button>
            <el-button type="warning" :icon="Upload" v-permission="'supplier:add'" @click="handleImport">导入</el-button>
            <el-button type="primary" :icon="Plus" v-permission="'supplier:add'" @click="handleAdd">新增供应商</el-button>
          </div>
        </div>
        <!-- 批量操作工具栏 -->
        <div v-if="selectedSuppliers.length > 0" class="batch-toolbar">
          <el-button type="danger" v-permission="'supplier:delete'" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
          <el-tag type="info" style="margin-left: 10px">已选择 {{ selectedSuppliers.length }} 项</el-tag>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="供应商名称/拼音/电话" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="外修合作">
          <el-select v-model="searchForm.is_repair_partner" placeholder="全部" clearable>
            <el-option label="是" :value="1" />
            <el-option label="否" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="supplier_code" label="供应商编码" width="120" />
        <el-table-column prop="supplier_name" label="供应商名称" min-width="150" />
        <el-table-column prop="contact_name" label="联系人" width="100" />
        <el-table-column prop="phone" label="联系电话" width="120" />
        <el-table-column prop="is_repair_partner" label="外修合作" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_repair_partner ? 'success' : 'info'" size="small">
              {{ row.is_repair_partner ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_purchase_amount" label="累计采购" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.total_purchase_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_repair_amount" label="累计外修" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.total_repair_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link :icon="Edit" v-permission="'supplier:edit'" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link :icon="Delete" v-permission="'supplier:delete'" @click="handleDelete(row)">删除</el-button>
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑供应商' : '新增供应商'" width="600px" destroy-on-close>
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="供应商编码" prop="supplier_code">
              <el-input v-model="formData.supplier_code" :placeholder="isEdit ? '' : '自动生成'" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供应商名称" prop="supplier_name">
              <el-input v-model="formData.supplier_name" placeholder="供应商名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系人" prop="contact_name">
              <el-input v-model="formData.contact_name" placeholder="联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="phone">
              <el-input v-model="formData.phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="外修合作">
              <el-switch v-model="formData.is_repair_partner" :active-value="1" :inactive-value="0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="formData.status" :active-value="1" :inactive-value="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="地址">
          <el-input v-model="formData.address" placeholder="地址" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="导入供应商" width="500px">
      <el-upload
        ref="uploadRef"
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".xlsx,.xls,.csv"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx, .xls, .csv 格式文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importLoading">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, Delete, Upload, Download } from '@element-plus/icons-vue'
import { getSupplierList, createSupplier, updateSupplier, deleteSupplier, batchDeleteSuppliers, importSuppliers, exportSuppliers } from '@/api/supplier'

const loading = ref(false)
const submitLoading = ref(false)
const importLoading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const uploadRef = ref(null)
const currentRow = ref(null)
const importFile = ref(null)

const searchForm = reactive({
  keyword: '',
  is_repair_partner: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  supplier_code: '',
  supplier_name: '',
  contact_name: '',
  phone: '',
  address: '',
  is_repair_partner: 0,
  status: 1,
  remark: ''
})

const rules = {
  supplier_name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
  contact_name: [{ required: true, message: '请输入联系人', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    const res = await getSupplierList(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取供应商列表失败:', error)
    ElMessage.error('获取供应商列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.is_repair_partner = null
  handleSearch()
}

const handleAdd = () => {
  isEdit.value = false
  currentRow.value = null
  Object.assign(formData, {
    supplier_code: '',
    supplier_name: '',
    contact_name: '',
    phone: '',
    address: '',
    is_repair_partner: 0,
    status: 1,
    remark: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  currentRow.value = row
  Object.assign(formData, {
    supplier_code: row.supplier_code,
    supplier_name: row.supplier_name,
    contact_name: row.contact_name,
    phone: row.phone,
    address: row.address,
    is_repair_partner: row.is_repair_partner,
    status: row.status,
    remark: row.remark
  })
  dialogVisible.value = true
}

const selectedSuppliers = ref([])

const handleSelectionChange = (selection) => {
  selectedSuppliers.value = selection
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该供应商吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteSupplier(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleBatchDelete = async () => {
  if (selectedSuppliers.value.length === 0) {
    ElMessage.warning('请先选择要删除的供应商')
    return
  }
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedSuppliers.value.length} 个供应商吗？`, '批量删除', {
      type: 'warning'
    })
    const ids = selectedSuppliers.value.map(item => item.id)
    const res = await batchDeleteSuppliers(ids)
    if (res.code === 200) {
      ElMessage.success('批量删除成功')
      selectedSuppliers.value = []
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
    }
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      let res
      if (isEdit.value) {
        res = await updateSupplier(currentRow.value.id, formData)
      } else {
        res = await createSupplier(formData)
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
  importFile.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const handleFileChange = (file) => {
  importFile.value = file.raw
}

const submitImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  importLoading.value = true
  try {
    const res = await importSuppliers(importFile.value)
    if (res.code === 200) {
      ElMessage.success('导入成功')
      importDialogVisible.value = false
      fetchData()
    }
  } catch (error) {
    ElMessage.error('导入失败')
  } finally {
    importLoading.value = false
  }
}

const handleExport = async () => {
  try {
    const response = await exportSuppliers()
    const blob = response.data
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `供应商列表_${new Date().toISOString().split('T')[0]}.xlsx`
    link.click()
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.supplier-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      gap: 10px;
    }
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
}
</style>
