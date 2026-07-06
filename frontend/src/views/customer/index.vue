<template>
  <div class="customer-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>客户管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" v-permission="'customer:view'" @click="handleExport">导出</el-button>
            <el-button type="warning" :icon="Upload" v-permission="'customer:add'" @click="handleImport">导入</el-button>
            <el-button type="primary" :icon="Plus" v-permission="'customer:add'" @click="handleAdd">新增客户</el-button>
          </div>
        </div>
        <!-- 批量操作工具栏 -->
        <div v-if="selectedCustomers.length > 0" class="batch-toolbar">
          <el-button type="danger" v-permission="'customer:delete'" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
          <el-tag type="info" style="margin-left: 10px">已选择 {{ selectedCustomers.length }} 项</el-tag>
        </div>
      </template>
      
      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="客户名称/拼音/电话" clearable @keyup.enter="handleSearch" />
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
        <el-table-column prop="customer_code" label="客户编码" width="120" />
        <el-table-column prop="customer_name" label="客户名称" min-width="150" />
        <el-table-column prop="customer_type" label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.customer_type === 1 ? 'info' : 'success'" size="small">
              {{ row.customer_type === 1 ? '个人' : '企业' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact_name" label="联系人" width="100" />
        <el-table-column prop="phone" label="联系电话" width="120" />
        <el-table-column prop="address" label="地址" min-width="150" show-overflow-tooltip />
        <el-table-column prop="discount_rate" label="折扣率" width="80" align="center">
          <template #default="{ row }">
            {{ row.discount_rate }}%
          </template>
        </el-table-column>
        <el-table-column prop="total_sales_amount" label="累计消费" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.total_sales_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link :icon="View" @click="handleView(row)">查看</el-button>
            <el-button type="primary" link :icon="Edit" v-permission="'customer:edit'" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link :icon="Delete" v-permission="'customer:delete'" @click="handleDelete(row)">删除</el-button>
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
    
    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="导入客户" width="500px">
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="客户名称" prop="customer_name">
          <el-input v-model="form.customer_name" :placeholder="form.customer_type === 1 ? '请输入姓名' : '请输入公司名称'" />
        </el-form-item>
        
        <el-form-item label="客户类型" prop="customer_type">
          <el-radio-group v-model="form.customer_type">
            <el-radio :label="1">个人</el-radio>
            <el-radio :label="2">企业</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 企业专属：联系人 -->
        <el-form-item v-if="form.customer_type === 2" label="联系人" prop="contact_name">
          <el-input v-model="form.contact_name" placeholder="请输入联系人" />
        </el-form-item>
        
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>
        
        <!-- 企业专属：备用电话 -->
        <el-form-item v-if="form.customer_type === 2" label="备用电话" prop="phone2">
          <el-input v-model="form.phone2" placeholder="请输入备用电话" />
        </el-form-item>
        
        <!-- 企业专属：邮箱 -->
        <el-form-item v-if="form.customer_type === 2" label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" placeholder="请输入地址" />
        </el-form-item>
        
        <el-form-item label="折扣率" prop="discount_rate">
          <el-input-number v-model="form.discount_rate" :min="0" :max="100" :precision="2" />
          <span class="ml-5">%</span>
        </el-form-item>
        
        <!-- 企业专属字段 -->
        <template v-if="form.customer_type === 2">
          <el-divider content-position="left">企业信息</el-divider>
          
          <el-form-item label="信用额度" prop="credit_limit">
            <el-input-number v-model="form.credit_limit" :min="0" :precision="2" />
          </el-form-item>
          
          <el-form-item label="税号" prop="tax_number">
            <el-input v-model="form.tax_number" placeholder="请输入税号" />
          </el-form-item>
          
          <el-form-item label="开户银行" prop="bank_name">
            <el-input v-model="form.bank_name" placeholder="请输入开户银行" />
          </el-form-item>
          
          <el-form-item label="银行账号" prop="bank_account">
            <el-input v-model="form.bank_account" placeholder="请输入银行账号" />
          </el-form-item>
        </template>
        
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, View, Edit, Delete, Download, Upload } from '@element-plus/icons-vue'
import { getCustomerList, createCustomer, updateCustomer, deleteCustomer, batchDeleteCustomers, importCustomers } from '@/api/customer'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const importLoading = ref(false)
const dialogTitle = ref('新增客户')
const formRef = ref()
const uploadRef = ref(null)
const importFile = ref(null)

const searchForm = reactive({
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  id: null,
  customer_name: '',
  customer_type: 1,
  contact_name: '',
  phone: '',
  phone2: '',
  email: '',
  address: '',
  discount_rate: 100,
  credit_limit: 0,
  tax_number: '',
  bank_name: '',
  bank_account: '',
  remark: ''
})

const formRules = {
  customer_name: [
    { required: true, message: '请输入客户名称', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getCustomerList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword
    })
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取客户列表失败:', error)
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
  handleSearch()
}

// 导出
const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  const token = localStorage.getItem('token') || ''
  window.open(`/api/customers/export?${params.toString()}&token=${token}`, '_blank')
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
    const res = await importCustomers(importFile.value)
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

const handleAdd = () => {
  dialogTitle.value = '新增客户'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑客户'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleView = (row) => {
  handleEdit(row)
}

const selectedCustomers = ref([])

const handleSelectionChange = (selection) => {
  selectedCustomers.value = selection
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该客户吗？', '提示', {
      type: 'warning'
    })
    const res = await deleteCustomer(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedCustomers.value.length === 0) {
    ElMessage.warning('请先选择要删除的客户')
    return
  }
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedCustomers.value.length} 个客户吗？`, '批量删除', {
      type: 'warning'
    })
    const ids = selectedCustomers.value.map(item => item.id)
    const res = await batchDeleteCustomers(ids)
    if (res.code === 200) {
      ElMessage.success('批量删除成功')
      selectedCustomers.value = []
      fetchData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      let res
      if (form.id) {
        res = await updateCustomer(form.id, form)
      } else {
        res = await createCustomer(form)
      }
      if (res.code === 200) {
        ElMessage.success(dialogTitle.value + '成功')
        dialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      console.error('操作失败:', error)
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    id: null,
    customer_name: '',
    customer_type: 1,
    contact_name: '',
    phone: '',
    address: '',
    discount_rate: 100,
    credit_limit: 0,
    tax_number: '',
    bank_name: '',
    bank_account: '',
    remark: ''
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

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.customer-page {
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
  
  .ml-5 {
    margin-left: 5px;
  }
}
</style>
