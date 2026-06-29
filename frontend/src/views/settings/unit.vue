<template>
  <div class="unit-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>计量单位管理</span>
          <el-button type="primary" @click="handleAdd">新增单位</el-button>
        </div>
      </template>

      <el-table :data="unitList" stripe border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="unit_name" label="单位名称" min-width="150" />
        <el-table-column prop="unit_code" label="单位编码" width="120" />
        <el-table-column prop="is_base" label="基础单位" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_base ? 'success' : 'info'">
              {{ row.is_base ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="conversion_rate" label="换算率" width="100" align="center" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 单位弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑单位' : '新增单位'" width="450px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="单位名称" prop="unit_name">
          <el-input v-model="form.unit_name" placeholder="请输入单位名称" />
        </el-form-item>
        <el-form-item label="单位编码">
          <el-input v-model="form.unit_code" placeholder="请输入单位编码，如：个、箱、台" />
        </el-form-item>
        <el-form-item label="基础单位">
          <el-switch v-model="form.is_base" />
          <span class="form-tip">基础单位是最小计量单位</span>
        </el-form-item>
        <el-form-item label="换算率">
          <el-input-number v-model="form.conversion_rate" :min="0" :precision="2" :step="0.1" />
          <span class="form-tip">与基础单位的换算比例</span>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUnit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const loading = ref(false)
const unitList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = reactive({
  id: null,
  unit_name: '',
  unit_code: '',
  is_base: false,
  conversion_rate: 1,
  sort_order: 0
})

const rules = {
  unit_name: [{ required: true, message: '请输入单位名称', trigger: 'blur' }]
}

const fetchUnits = async () => {
  loading.value = true
  try {
    const res = await request.get('/product/units')
    if (res.code === 200) {
      unitList.value = res.data || []
    }
  } catch (e) {
    console.error('获取单位失败:', e)
    ElMessage.error('获取单位失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.id = null
  form.unit_name = ''
  form.unit_code = ''
  form.is_base = false
  form.conversion_rate = 1
  form.sort_order = 0
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  form.id = row.id
  form.unit_name = row.unit_name
  form.unit_code = row.unit_code || ''
  form.is_base = !!row.is_base
  form.conversion_rate = row.conversion_rate || 1
  form.sort_order = row.sort_order || 0
  dialogVisible.value = true
}

const saveUnit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const payload = {
      unit_name: form.unit_name,
      unit_code: form.unit_code,
      is_base: form.is_base ? 1 : 0,
      conversion_rate: form.conversion_rate,
      sort_order: form.sort_order
    }
    if (isEdit.value) {
      const res = await request.put(`/product/units/${form.id}`, payload)
      if (res.code === 200) {
        ElMessage.success('修改成功')
        dialogVisible.value = false
        fetchUnits()
      }
    } else {
      const res = await request.post('/product/units', payload)
      if (res.code === 200) {
        ElMessage.success('添加成功')
        dialogVisible.value = false
        fetchUnits()
      }
    }
  } catch (e) {
    console.error('保存单位失败:', e)
    ElMessage.error('保存失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除单位"${row.unit_name}"？`,
      '提示',
      { type: 'warning' }
    )
    const res = await request.delete(`/product/units/${row.id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchUnits()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除单位失败:', e)
    }
  }
}

onMounted(() => {
  fetchUnits()
})
</script>

<style lang="scss" scoped>
.unit-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .form-tip {
    margin-left: 8px;
    color: #999;
    font-size: 12px;
  }
}
</style>
