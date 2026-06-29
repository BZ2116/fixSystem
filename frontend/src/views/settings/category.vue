<template>
  <div class="category-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>商品分类管理</span>
          <el-button type="primary" @click="handleAddCategory(null)">新增一级分类</el-button>
        </div>
      </template>

      <el-table
        :data="categoryList"
        row-key="id"
        border
        v-loading="loading"
        :tree-props="{ children: 'children' }"
        default-expand-all
      >
        <el-table-column prop="category_name" label="分类名称" min-width="200" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleAddCategory(row)">添加子分类</el-button>
            <el-button type="primary" link @click="handleEditCategory(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDeleteCategory(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 分类弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="450px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="上级分类">
          <el-input :model-value="form.parent_name || '无（一级分类）'" disabled />
        </el-form-item>
        <el-form-item label="分类名称" prop="category_name">
          <el-input v-model="form.category_name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const loading = ref(false)
const categoryList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const dialogTitle = ref('新增分类')
const formRef = ref(null)

const form = reactive({
  id: null,
  category_name: '',
  parent_id: 0,
  parent_name: '',
  sort_order: 0
})

const rules = {
  category_name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }]
}

// 将扁平列表转为树形结构
const buildTree = (list, parentId = 0) => {
  return list
    .filter(item => item.parent_id === parentId)
    .map(item => {
      const children = buildTree(list, item.id)
      return children.length > 0 ? { ...item, children } : { ...item }
    })
    .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
}

const fetchCategories = async () => {
  loading.value = true
  try {
    const res = await request.get('/product/categories')
    if (res.code === 200) {
      const flatList = res.data || []
      categoryList.value = buildTree(flatList)
    }
  } catch (e) {
    console.error('获取分类失败:', e)
    ElMessage.error('获取分类失败')
  } finally {
    loading.value = false
  }
}

const handleAddCategory = (parentRow) => {
  isEdit.value = false
  dialogTitle.value = parentRow ? `在"${parentRow.category_name}"下添加子分类` : '新增一级分类'
  form.id = null
  form.category_name = ''
  form.parent_id = parentRow ? parentRow.id : 0
  form.parent_name = parentRow ? parentRow.category_name : ''
  form.sort_order = 0
  dialogVisible.value = true
}

const handleEditCategory = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑分类'
  form.id = row.id
  form.category_name = row.category_name
  form.parent_id = row.parent_id || 0
  form.parent_name = ''
  form.sort_order = row.sort_order || 0
  dialogVisible.value = true
}

const saveCategory = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const payload = {
      category_name: form.category_name,
      parent_id: form.parent_id,
      sort_order: form.sort_order
    }
    if (isEdit.value) {
      const res = await request.put(`/product/categories/${form.id}`, payload)
      if (res.code === 200) {
        ElMessage.success('修改成功')
        dialogVisible.value = false
        fetchCategories()
      }
    } else {
      const res = await request.post('/product/categories', payload)
      if (res.code === 200) {
        ElMessage.success('添加成功')
        dialogVisible.value = false
        fetchCategories()
      }
    }
  } catch (e) {
    console.error('保存分类失败:', e)
    ElMessage.error('保存失败')
  }
}

const handleDeleteCategory = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除分类"${row.category_name}"？删除后子分类也会被删除。`,
      '提示',
      { type: 'warning' }
    )
    const res = await request.delete(`/product/categories/${row.id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchCategories()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除分类失败:', e)
    }
  }
}

onMounted(() => {
  fetchCategories()
})
</script>

<style lang="scss" scoped>
.category-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
