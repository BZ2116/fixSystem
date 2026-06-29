<template>
  <div class="users-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" v-permission="'settings-users:add'" @click="handleAdd">新增用户</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="searchForm.phone" placeholder="请输入手机号" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable style="width: 120px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="userList" stripe border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="real_name" label="真实姓名" min-width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="role_name" label="角色" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.role_name" size="small">{{ row.role_name }}</el-tag>
            <span v-else style="color:#999">未分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="data_scope" label="数据权限" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="dataScopeTagType(row.data_scope)" size="small">
              {{ dataScopeLabel(row.data_scope) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              @change="(val) => handleStatusChange(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="last_login_time" label="最后登录" width="180" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link v-permission="'settings-users:edit'" @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" link v-permission="'settings-users:role'" @click="handleAssignRole(row)">分配角色</el-button>
            <el-button type="primary" link v-permission="'settings-users:password'" @click="handleResetPassword(row)">重置密码</el-button>
            <el-button type="danger" link v-permission="'settings-users:delete'" @click="handleDelete(row)">删除</el-button>
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

    <!-- 用户弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="500px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="form.role_id" placeholder="请选择角色" style="width: 100%" filterable>
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.role_name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="基本工资">
          <el-input-number v-model="form.base_salary" :min="0" :precision="2" :step="100" placeholder="请输入基本工资" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUser">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配角色弹窗 -->
    <el-dialog v-model="roleDialogVisible" title="分配角色" width="400px">
      <el-form label-width="100px">
        <el-form-item label="用户">
          <span>{{ currentUser?.real_name || currentUser?.username }}</span>
        </el-form-item>
        <el-form-item label="当前角色">
          <el-tag v-if="currentUser?.role_name" size="small">{{ currentUser.role_name }}</el-tag>
          <span v-else style="color:#999">未分配</span>
        </el-form-item>
        <el-form-item label="选择角色">
          <el-select v-model="assignRoleId" placeholder="请选择角色" style="width: 100%" filterable>
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.role_name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAssignRole">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="resetPwdVisible" title="重置密码" width="400px">
      <el-form :model="resetPwdForm" label-width="100px" :rules="resetPwdRules" ref="resetPwdRef">
        <el-form-item label="新密码" prop="password">
          <el-input v-model="resetPwdForm.password" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="resetPwdForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmResetPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const loading = ref(false)
const userList = ref([])
const roleList = ref([])
const dialogVisible = ref(false)
const roleDialogVisible = ref(false)
const resetPwdVisible = ref(false)
const isEdit = ref(false)
const currentUser = ref(null)
const assignRoleId = ref(null)
const formRef = ref(null)
const resetPwdRef = ref(null)

const searchForm = reactive({
  username: '',
  phone: '',
  status: null
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const form = reactive({
  id: null,
  username: '',
  real_name: '',
  phone: '',
  email: '',
  password: '',
  role_id: null,
  base_salary: 0,
  status: 1,
  remark: ''
})

const resetPwdForm = reactive({
  password: '',
  confirmPassword: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur', min: 6 }],
  role_id: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const resetPwdRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetPwdForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 数据权限标签
const dataScopeLabel = (scope) => {
  const map = { 1: '全部数据', 2: '本部门', 3: '仅本人' }
  return map[scope] || '未知'
}

const dataScopeTagType = (scope) => {
  const map = { 1: 'danger', 2: 'warning', 3: 'info' }
  return map[scope] || 'info'
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const res = await request.get('/settings/users', { params })
    if (res.code === 200) {
      userList.value = res.data?.list || []
      pagination.total = res.data?.total || 0
    }
  } catch (e) {
    console.error('获取用户列表失败:', e)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const fetchRoles = async () => {
  try {
    const res = await request.get('/settings/roles/all')
    if (res.code === 200) {
      roleList.value = res.data || []
    }
  } catch (e) {
    // 如果 all 接口不可用，回退到分页接口
    try {
      const res = await request.get('/settings/roles')
      if (res.code === 200) {
        roleList.value = res.data?.list || res.data || []
      }
    } catch (e2) {
      console.error('获取角色列表失败:', e2)
    }
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchUsers()
}

const handleReset = () => {
  searchForm.username = ''
  searchForm.phone = ''
  searchForm.status = null
  pagination.page = 1
  fetchUsers()
}

const handleSizeChange = (val) => {
  pagination.page_size = val
  fetchUsers()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  fetchUsers()
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    username: '',
    real_name: '',
    phone: '',
    email: '',
    password: '',
    role_id: null,
    base_salary: 0,
    status: 1,
    remark: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(form, row)
  form.password = ''
  dialogVisible.value = true
}

const saveUser = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const payload = { ...form }
    if (isEdit.value) {
      delete payload.password
      const res = await request.put(`/settings/users/${form.id}`, payload)
      if (res.code === 200) {
        ElMessage.success('修改成功')
        dialogVisible.value = false
        fetchUsers()
      }
    } else {
      const res = await request.post('/settings/users', payload)
      if (res.code === 200) {
        ElMessage.success('添加成功')
        dialogVisible.value = false
        fetchUsers()
      }
    }
  } catch (e) {
    console.error('保存用户失败:', e)
    ElMessage.error('保存失败')
  }
}

const handleStatusChange = async (row, val) => {
  try {
    const res = await request.put(`/settings/users/${row.id}/status`, { status: val })
    if (res.code === 200) {
      ElMessage.success(val === 1 ? '已启用' : '已禁用')
    } else {
      row.status = val === 1 ? 0 : 1
    }
  } catch (e) {
    row.status = val === 1 ? 0 : 1
    ElMessage.error('操作失败')
  }
}

// 分配角色
const handleAssignRole = (row) => {
  currentUser.value = row
  assignRoleId.value = row.role_id || null
  roleDialogVisible.value = true
}

const confirmAssignRole = async () => {
  if (!assignRoleId.value) {
    ElMessage.warning('请选择角色')
    return
  }
  try {
    const res = await request.put(`/settings/users/${currentUser.value.id}/roles`, {
      role_id: assignRoleId.value
    })
    if (res.code === 200) {
      ElMessage.success('角色分配成功')
      roleDialogVisible.value = false
      fetchUsers()
    }
  } catch (e) {
    console.error('分配角色失败:', e)
    ElMessage.error('分配角色失败')
  }
}

const handleResetPassword = (row) => {
  currentUser.value = row
  resetPwdForm.password = ''
  resetPwdForm.confirmPassword = ''
  resetPwdVisible.value = true
}

const confirmResetPassword = async () => {
  const valid = await resetPwdRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const res = await request.put(`/settings/users/${currentUser.value.id}/password`, {
      password: resetPwdForm.password
    })
    if (res.code === 200) {
      ElMessage.success('密码重置成功')
      resetPwdVisible.value = false
    }
  } catch (e) {
    console.error('重置密码失败:', e)
    ElMessage.error('重置密码失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除用户"${row.username}"？删除后无法恢复。`,
      '提示',
      { type: 'warning' }
    )
    const res = await request.delete(`/settings/users/${row.id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchUsers()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除用户失败:', e)
    }
  }
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
})
</script>

<style lang="scss" scoped>
.users-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
