<template>
  <div class="roles-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" v-permission="'settings-roles:add'" @click="handleAdd">新增角色</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="角色名称">
          <el-input v-model="searchForm.role_name" placeholder="请输入角色名称" clearable />
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

      <!-- 角色列表 -->
      <el-table :data="roleList" stripe border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="role_name" label="角色名称" min-width="120" />
        <el-table-column prop="role_code" label="角色编码" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
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
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link v-permission="'settings-roles:edit'" @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" link v-permission="'settings-roles:permission'" @click="handlePermission(row)">权限</el-button>
            <el-button type="danger" link v-permission="'settings-roles:delete'" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑角色对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑角色' : '新增角色'" width="500px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="form.role_name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色编码" prop="role_code">
          <el-input v-model="form.role_code" placeholder="请输入角色编码" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入角色描述" />
        </el-form-item>
        <el-form-item label="数据权限" prop="data_scope">
          <el-select v-model="form.data_scope" placeholder="请选择数据权限" style="width: 100%">
            <el-option label="全部数据" :value="1" />
            <el-option label="本部门数据" :value="2" />
            <el-option label="仅本人数据" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRole">确定</el-button>
      </template>
    </el-dialog>

    <!-- 权限配置对话框 -->
    <el-dialog v-model="permissionDialogVisible" title="权限配置" width="600px">
      <div class="permission-header">
        <span class="role-name">角色：{{ currentRole?.role_name }}</span>
        <el-button type="primary" link @click="handleExpandAll">
          {{ isAllExpanded ? '全部收起' : '全部展开' }}
        </el-button>
      </div>
      <el-tree
        ref="permissionTreeRef"
        :data="permissionTree"
        show-checkbox
        node-key="id"
        :default-checked-keys="checkedPermissionIds"
        :props="{ label: 'name', children: 'children' }"
        default-expand-all
        check-strictly
        @check="handlePermissionCheck"
        class="permission-tree"
      />
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="permissionSaving" @click="savePermissions">保存权限</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const loading = ref(false)
const roleList = ref([])
const dialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const permissionSaving = ref(false)
const isEdit = ref(false)
const currentRole = ref(null)
const formRef = ref(null)
const permissionTreeRef = ref(null)
const isAllExpanded = ref(true)

const searchForm = reactive({
  role_name: '',
  status: null
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const form = reactive({
  id: null,
  role_name: '',
  role_code: '',
  description: '',
  data_scope: 1,
  status: 1
})

const permissionTree = ref([])
const checkedPermissionIds = ref([])
const selectedPermissionIds = ref([])

const rules = {
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  role_code: [
    { required: true, message: '请输入角色编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '编码以字母开头，只允许字母、数字和下划线', trigger: 'blur' }
  ],
  data_scope: [{ required: true, message: '请选择数据权限', trigger: 'change' }]
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

// 获取角色列表
const fetchRoles = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const res = await request.get('/settings/roles', { params })
    if (res.code === 200) {
      roleList.value = res.data?.list || res.data || []
      pagination.total = res.data?.total || 0
    }
  } catch (e) {
    console.error('获取角色列表失败:', e)
    ElMessage.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

// 获取权限树
const fetchPermissionTree = async () => {
  try {
    const res = await request.get('/settings/permissions')
    if (res.code === 200) {
      permissionTree.value = res.data || []
    }
  } catch (e) {
    console.error('获取权限树失败:', e)
    ElMessage.error('获取权限树失败')
  }
}

// 获取角色已选权限
const fetchRolePermissions = async (roleId) => {
  try {
    const res = await request.get(`/settings/roles/${roleId}/permissions`)
    if (res.code === 200) {
      // 获取所有叶子节点id（el-tree check-strictly 模式下需要叶子节点id）
      const leafIds = getLeafIds(res.data || [])
      checkedPermissionIds.value = leafIds
      selectedPermissionIds.value = leafIds
    }
  } catch (e) {
    console.error('获取角色权限失败:', e)
    ElMessage.error('获取角色权限失败')
  }
}

// 递归获取叶子节点id
const getLeafIds = (nodes) => {
  const ids = []
  const traverse = (list) => {
    list.forEach(node => {
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      } else {
        ids.push(node.id)
      }
    })
  }
  traverse(nodes)
  return ids
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchRoles()
}

const handleReset = () => {
  searchForm.role_name = ''
  searchForm.status = null
  pagination.page = 1
  fetchRoles()
}

const handleSizeChange = (val) => {
  pagination.page_size = val
  fetchRoles()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  fetchRoles()
}

// 新增角色
const handleAdd = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    role_name: '',
    role_code: '',
    description: '',
    data_scope: 1,
    status: 1
  })
  dialogVisible.value = true
}

// 编辑角色
const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    role_name: row.role_name,
    role_code: row.role_code,
    description: row.description,
    data_scope: row.data_scope,
    status: row.status
  })
  dialogVisible.value = true
}

// 保存角色
const saveRole = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const payload = { ...form }
    if (isEdit.value) {
      const res = await request.put(`/settings/roles/${form.id}`, payload)
      if (res.code === 200) {
        ElMessage.success('修改成功')
        dialogVisible.value = false
        fetchRoles()
      }
    } else {
      const res = await request.post('/settings/roles', payload)
      if (res.code === 200) {
        ElMessage.success('添加成功')
        dialogVisible.value = false
        fetchRoles()
      }
    }
  } catch (e) {
    console.error('保存角色失败:', e)
    ElMessage.error('保存失败')
  }
}

// 状态切换
const handleStatusChange = async (row, val) => {
  try {
    const res = await request.put(`/settings/roles/${row.id}`, { status: val })
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

// 删除角色
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除角色"${row.role_name}"？删除后无法恢复。`,
      '提示',
      { type: 'warning' }
    )
    const res = await request.delete(`/settings/roles/${row.id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchRoles()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除角色失败:', e)
    }
  }
}

// 配置权限
const handlePermission = async (row) => {
  currentRole.value = row
  checkedPermissionIds.value = []
  selectedPermissionIds.value = []
  permissionDialogVisible.value = true

  await fetchPermissionTree()
  await fetchRolePermissions(row.id)

  // 等待DOM更新后设置选中
  await nextTick()
  if (permissionTreeRef.value) {
    permissionTreeRef.value.setCheckedKeys(checkedPermissionIds.value)
  }
}

// 权限树勾选变化
const handlePermissionCheck = () => {
  if (permissionTreeRef.value) {
    selectedPermissionIds.value = permissionTreeRef.value.getCheckedKeys()
  }
}

// 全部展开/收起
const handleExpandAll = () => {
  if (!permissionTreeRef.value) return
  const tree = permissionTreeRef.value
  const nodes = tree.store._getAllNodes()
  isAllExpanded.value = !isAllExpanded.value
  nodes.forEach(node => {
    node.expanded = isAllExpanded.value
  })
}

// 保存权限
const savePermissions = async () => {
  if (!currentRole.value) return
  permissionSaving.value = true
  try {
    const res = await request.post(`/settings/roles/${currentRole.value.id}/permissions`, {
      permission_ids: selectedPermissionIds.value
    })
    if (res.code === 200) {
      ElMessage.success('权限配置成功')
      permissionDialogVisible.value = false
    }
  } catch (e) {
    console.error('保存权限失败:', e)
    ElMessage.error('保存权限失败')
  } finally {
    permissionSaving.value = false
  }
}

onMounted(() => {
  fetchRoles()
})
</script>

<style lang="scss" scoped>
.roles-page {
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

  .permission-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .role-name {
      font-weight: bold;
      font-size: 14px;
    }
  }

  .permission-tree {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    padding: 8px;
  }
}
</style>
