<template>
  <div class="log-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>操作日志</span>
          <el-button type="danger" @click="handleClear">清空日志</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="操作用户">
          <el-select v-model="searchForm.user_id" placeholder="请选择用户" clearable style="width: 150px">
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="操作模块">
          <el-select v-model="searchForm.module" placeholder="请选择模块" clearable style="width: 150px">
            <el-option label="登录" value="login" />
            <el-option label="用户管理" value="user" />
            <el-option label="商品管理" value="product" />
            <el-option label="客户管理" value="customer" />
            <el-option label="供应商管理" value="supplier" />
            <el-option label="销售管理" value="sales" />
            <el-option label="采购管理" value="purchase" />
            <el-option label="工单管理" value="work_order" />
            <el-option label="库存管理" value="inventory" />
            <el-option label="财务管理" value="finance" />
            <el-option label="系统设置" value="settings" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="searchForm.action" placeholder="请选择类型" clearable style="width: 150px">
            <el-option label="新增" value="create" />
            <el-option label="修改" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="查询" value="query" />
            <el-option label="导出" value="export" />
            <el-option label="登录" value="login" />
            <el-option label="登出" value="logout" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="请输入关键词" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="logList" stripe border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="created_at" label="操作时间" width="180" />
        <el-table-column prop="username" label="操作用户" width="120" />
        <el-table-column prop="module" label="操作模块" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getModuleText(row.module) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getActionType(row.action)">
              {{ getActionText(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="description" label="操作描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="600px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="日志ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="操作时间">{{ currentLog.created_at }}</el-descriptions-item>
        <el-descriptions-item label="操作用户">{{ currentLog.username }}</el-descriptions-item>
        <el-descriptions-item label="操作模块">{{ getModuleText(currentLog.module) }}</el-descriptions-item>
        <el-descriptions-item label="操作类型">{{ getActionText(currentLog.action) }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip_address }}</el-descriptions-item>
        <el-descriptions-item label="操作描述">{{ currentLog.description }}</el-descriptions-item>
        <el-descriptions-item label="请求参数">
          <pre class="json-content">{{ formatJson(currentLog.request_params) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="响应结果">
          <pre class="json-content">{{ formatJson(currentLog.response_result) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const loading = ref(false)
const logList = ref([])
const userList = ref([])
const detailVisible = ref(false)
const currentLog = ref({})

const searchForm = reactive({
  dateRange: [],
  user_id: null,
  module: '',
  action: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const moduleMap = {
  login: '登录',
  user: '用户管理',
  product: '商品管理',
  customer: '客户管理',
  supplier: '供应商管理',
  sales: '销售管理',
  purchase: '采购管理',
  work_order: '工单管理',
  inventory: '库存管理',
  finance: '财务管理',
  settings: '系统设置'
}

const actionMap = {
  create: '新增',
  update: '修改',
  delete: '删除',
  query: '查询',
  export: '导出',
  login: '登录',
  logout: '登出'
}

const actionTypeMap = {
  create: 'success',
  update: 'warning',
  delete: 'danger',
  query: 'info',
  export: 'primary',
  login: 'success',
  logout: 'info'
}

const getModuleText = (module) => {
  return moduleMap[module] || module
}

const getActionText = (action) => {
  return actionMap[action] || action
}

const getActionType = (action) => {
  return actionTypeMap[action] || 'info'
}

const formatJson = (json) => {
  if (!json) return ''
  try {
    const obj = typeof json === 'string' ? JSON.parse(json) : json
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return json
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      user_id: searchForm.user_id,
      module: searchForm.module,
      action: searchForm.action,
      keyword: searchForm.keyword
    }
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_time = searchForm.dateRange[0]
      params.end_time = searchForm.dateRange[1]
    }
    const res = await request.get('/settings/logs', { params })
    if (res.code === 200) {
      logList.value = res.data?.list || []
      pagination.total = res.data?.total || 0
    }
  } catch (e) {
    console.error('获取日志失败:', e)
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

const fetchUsers = async () => {
  try {
    const res = await request.get('/settings/users', { params: { page_size: 999 } })
    if (res.code === 200) {
      userList.value = res.data?.list || []
    }
  } catch (e) {
    console.error('获取用户列表失败:', e)
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchLogs()
}

const handleReset = () => {
  searchForm.dateRange = []
  searchForm.user_id = null
  searchForm.module = ''
  searchForm.action = ''
  searchForm.keyword = ''
  pagination.page = 1
  fetchLogs()
}

const handleSizeChange = (val) => {
  pagination.page_size = val
  fetchLogs()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  fetchLogs()
}

const handleViewDetail = (row) => {
  currentLog.value = row
  detailVisible.value = true
}

const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.user_id) params.append('user_id', searchForm.user_id)
  if (searchForm.module) params.append('module', searchForm.module)
  if (searchForm.action) params.append('action', searchForm.action)
  if (searchForm.dateRange && searchForm.dateRange.length === 2) {
    params.append('start_time', searchForm.dateRange[0])
    params.append('end_time', searchForm.dateRange[1])
  }
  const token = localStorage.getItem('token') || ''
  window.open(`/api/operation-logs/export?${params.toString()}&token=${token}`, '_blank')
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm(
      '确认清空所有操作日志？此操作不可恢复。',
      '警告',
      { type: 'warning' }
    )
    const res = await request.delete('/settings/logs')
    if (res.code === 200) {
      ElMessage.success('清空成功')
      fetchLogs()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('清空日志失败:', e)
    }
  }
}

onMounted(() => {
  fetchLogs()
  fetchUsers()
})
</script>

<style lang="scss" scoped>
.log-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-form {
    margin-bottom: 20px;

    :deep(.el-form-item) {
      margin-bottom: 10px;
    }
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .json-content {
    margin: 0;
    padding: 10px;
    background: #f5f7fa;
    border-radius: 4px;
    font-size: 12px;
    line-height: 1.5;
    max-height: 200px;
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }
}
</style>
