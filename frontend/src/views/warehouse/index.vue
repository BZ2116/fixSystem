<template>
  <div class="app-container">
    <!-- 搜索区域 -->
    <el-card shadow="never" class="mb-4">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input v-model="searchForm.keyword" placeholder="仓库名称/编码" clearable @clear="fetchData" @keyup.enter="fetchData">
            <template #append><el-button :icon="Search" @click="fetchData" /></template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="searchForm.status" placeholder="状态" clearable @change="fetchData" style="width: 100%">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-col>
        <el-col :span="14" style="text-align: right;">
          <el-button type="primary" @click="handleAdd">新增仓库</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="never">
      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="warehouse_code" label="仓库编码" width="120" />
        <el-table-column prop="warehouse_name" label="仓库名称" width="150" />
        <el-table-column prop="address" label="仓库地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="contact_person" label="联系人" width="100" />
        <el-table-column prop="contact_phone" label="联系电话" width="130" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.status" :active-value="1" :inactive-value="0" @change="handleStatusChange(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该仓库？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @size-change="fetchData" @current-change="fetchData" class="pagination" />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑仓库' : '新增仓库'" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="仓库名称" prop="warehouse_name">
          <el-input v-model="formData.warehouse_name" placeholder="请输入仓库名称" />
        </el-form-item>
        <el-form-item label="仓库编码" prop="warehouse_code">
          <el-input v-model="formData.warehouse_code" placeholder="请输入仓库编码" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="仓库地址" prop="address">
          <el-input v-model="formData.address" placeholder="请输入仓库地址" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact_person">
          <el-input v-model="formData.contact_person" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="formData.contact_phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getWarehouseList, createWarehouse, updateWarehouse, deleteWarehouse, updateWarehouseStatus } from '@/api/inventory'

// 搜索表单
const searchForm = reactive({
  keyword: '',
  status: undefined
})

// 表格数据
const loading = ref(false)
const tableData = ref([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const editId = ref(null)

const formData = reactive({
  warehouse_name: '',
  warehouse_code: '',
  address: '',
  contact_person: '',
  contact_phone: '',
  remark: ''
})

// 表单验证规则
const rules = {
  warehouse_name: [{ required: true, message: '请输入仓库名称', trigger: 'blur' }],
  warehouse_code: [{ required: true, message: '请输入仓库编码', trigger: 'blur' }]
}

// 获取仓库列表
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword || undefined,
      status: searchForm.status !== undefined && searchForm.status !== '' ? searchForm.status : undefined
    }
    const res = await getWarehouseList(params)
    if (res.code === 200) {
      tableData.value = res.data.list || res.data.data || []
      pagination.total = res.data.total || 0
    }
  } catch (e) {
    console.error('获取仓库列表失败', e)
  } finally {
    loading.value = false
  }
}

// 重置表单数据
const resetForm = () => {
  formData.warehouse_name = ''
  formData.warehouse_code = ''
  formData.address = ''
  formData.contact_person = ''
  formData.contact_phone = ''
  formData.remark = ''
  editId.value = null
  isEdit.value = false
}

// 新增仓库
const handleAdd = () => {
  resetForm()
  dialogVisible.value = true
}

// 编辑仓库
const handleEdit = (row) => {
  resetForm()
  isEdit.value = true
  editId.value = row.id
  formData.warehouse_name = row.warehouse_name
  formData.warehouse_code = row.warehouse_code
  formData.address = row.address || ''
  formData.contact_person = row.contact_person || ''
  formData.contact_phone = row.contact_phone || ''
  formData.remark = row.remark || ''
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      let res
      if (isEdit.value) {
        res = await updateWarehouse(editId.value, { ...formData })
      } else {
        res = await createWarehouse({ ...formData })
      }
      if (res.code === 200) {
        ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
        dialogVisible.value = false
        fetchData()
      } else {
        ElMessage.error(res.message || '操作失败')
      }
    } catch (e) {
      console.error('提交失败', e)
      ElMessage.error('操作失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 删除仓库
const handleDelete = async (id) => {
  try {
    const res = await deleteWarehouse(id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (e) {
    console.error('删除失败', e)
    ElMessage.error('删除失败')
  }
}

// 切换仓库状态
const handleStatusChange = async (row) => {
  try {
    const res = await updateWarehouseStatus(row.id, { status: row.status })
    if (res.code === 200) {
      ElMessage.success(row.status === 1 ? '已启用' : '已禁用')
    } else {
      ElMessage.error(res.message || '状态切换失败')
      row.status = row.status === 1 ? 0 : 1
    }
  } catch (e) {
    console.error('状态切换失败', e)
    ElMessage.error('状态切换失败')
    row.status = row.status === 1 ? 0 : 1
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.mb-4 {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>
