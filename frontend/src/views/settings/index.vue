<template>
  <div class="settings-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="基础设置" name="basic">
          <el-form :model="basicForm" label-width="120px">
            <el-form-item label="系统名称">
              <el-input v-model="basicForm.system_name" />
            </el-form-item>
            <el-form-item label="公司名称">
              <el-input v-model="basicForm.company_name" />
            </el-form-item>
            <el-form-item label="联系电话">
              <el-input v-model="basicForm.contact_phone" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveBasicSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 商品分类管理（树形） -->
        <el-tab-pane label="商品分类" name="category">
          <div class="tab-toolbar">
            <el-button type="primary" @click="handleAddCategory(null)">新增一级分类</el-button>
          </div>
          <el-table
            :data="categoryList"
            row-key="id"
            border
            v-loading="categoryLoading"
            :tree-props="{ children: 'children' }"
            default-expand-all
          >
            <el-table-column prop="category_name" label="分类名称" min-width="200" />
            <el-table-column prop="sort_order" label="排序" width="80" />
            <el-table-column label="操作" width="220" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleAddCategory(row)">添加子分类</el-button>
                <el-button type="primary" link @click="handleEditCategory(row)">编辑</el-button>
                <el-button type="danger" link @click="handleDeleteCategory(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 单位管理 -->
        <el-tab-pane label="单位管理" name="unit">
          <div class="tab-toolbar">
            <el-button type="primary" @click="handleAddUnit">新增单位</el-button>
          </div>
          <el-table :data="unitList" stripe border v-loading="unitLoading">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="unit_name" label="单位名称" />
            <el-table-column prop="unit_code" label="单位编码" width="120" />
            <el-table-column prop="is_base" label="基础单位" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_base ? 'success' : 'info'">{{ row.is_base ? '是' : '否' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="conversion_rate" label="换算率" width="100" />
            <el-table-column label="操作" width="150" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleEditUnit(row)">编辑</el-button>
                <el-button type="danger" link @click="handleDeleteUnit(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="打印模板" name="print">
          <el-alert title="打印模板设置" type="info" :closable="false" description="自定义销售单、采购单、工单、收据等打印模板" show-icon class="mb-20" />
        </el-tab-pane>
        
        <el-tab-pane label="用户管理" name="user">
          <el-alert title="用户管理" type="info" :closable="false" description="管理系统用户和权限" show-icon class="mb-20" />
        </el-tab-pane>
        
        <el-tab-pane label="操作日志" name="log">
          <el-alert title="操作日志" type="info" :closable="false" description="查看系统操作记录" show-icon class="mb-20" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 商品分类弹窗 -->
    <el-dialog v-model="categoryDialogVisible" :title="categoryDialogTitle" width="450px">
      <el-form :model="categoryForm" label-width="100px">
        <el-form-item label="上级分类">
          <el-input :model-value="categoryForm.parent_name || '无（一级分类）'" disabled />
        </el-form-item>
        <el-form-item label="分类名称" required>
          <el-input v-model="categoryForm.category_name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">确定</el-button>
      </template>
    </el-dialog>

    <!-- 单位弹窗 -->
    <el-dialog v-model="unitDialogVisible" :title="isEditUnit ? '编辑单位' : '新增单位'" width="450px">
      <el-form :model="unitForm" label-width="100px">
        <el-form-item label="单位名称" required>
          <el-input v-model="unitForm.unit_name" placeholder="请输入单位名称" />
        </el-form-item>
        <el-form-item label="单位编码">
          <el-input v-model="unitForm.unit_code" placeholder="请输入单位编码，如：个、箱、台" />
        </el-form-item>
        <el-form-item label="基础单位">
          <el-switch v-model="unitForm.is_base" />
          <span style="margin-left: 8px; color: #999; font-size: 12px;">基础单位是最小计量单位</span>
        </el-form-item>
        <el-form-item label="换算率">
          <el-input-number v-model="unitForm.conversion_rate" :min="0" :precision="2" :step="0.1" />
          <span style="margin-left: 8px; color: #999; font-size: 12px;">与基础单位的换算比例</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="unitDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUnit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const activeTab = ref('basic')

const basicForm = reactive({
  system_name: '维修商贸一体化管理系统',
  company_name: '',
  contact_phone: ''
})

// ========== 商品分类（树形） ==========
const categoryList = ref([])
const categoryLoading = ref(false)
const categoryDialogVisible = ref(false)
const isEditCategory = ref(false)
const categoryDialogTitle = ref('新增分类')
const categoryForm = reactive({ id: null, category_name: '', parent_id: 0, parent_name: '', sort_order: 0 })

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
  categoryLoading.value = true
  try {
    const res = await request.get('/product/categories')
    if (res.code === 200) {
      const flatList = res.data || []
      categoryList.value = buildTree(flatList)
    }
  } catch (e) {
    console.error('获取分类失败:', e)
  } finally {
    categoryLoading.value = false
  }
}

const handleAddCategory = (parentRow) => {
  isEditCategory.value = false
  categoryDialogTitle.value = parentRow ? `在"${parentRow.category_name}"下添加子分类` : '新增一级分类'
  categoryForm.id = null
  categoryForm.category_name = ''
  categoryForm.parent_id = parentRow ? parentRow.id : 0
  categoryForm.parent_name = parentRow ? parentRow.category_name : ''
  categoryForm.sort_order = 0
  categoryDialogVisible.value = true
}

const handleEditCategory = (row) => {
  isEditCategory.value = true
  categoryDialogTitle.value = '编辑分类'
  categoryForm.id = row.id
  categoryForm.category_name = row.category_name
  categoryForm.parent_id = row.parent_id || 0
  categoryForm.parent_name = ''
  categoryForm.sort_order = row.sort_order || 0
  categoryDialogVisible.value = true
}

const saveCategory = async () => {
  if (!categoryForm.category_name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  try {
    const payload = {
      category_name: categoryForm.category_name,
      parent_id: categoryForm.parent_id,
      sort_order: categoryForm.sort_order
    }
    if (isEditCategory.value) {
      const res = await request.put(`/product/categories/${categoryForm.id}`, payload)
      if (res.code === 200) {
        ElMessage.success('修改成功')
        categoryDialogVisible.value = false
        fetchCategories()
      }
    } else {
      const res = await request.post('/product/categories', payload)
      if (res.code === 200) {
        ElMessage.success('添加成功')
        categoryDialogVisible.value = false
        fetchCategories()
      }
    }
  } catch (e) {
    console.error('保存分类失败:', e)
  }
}

const handleDeleteCategory = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除分类"${row.category_name}"？删除后子分类也会被删除。`, '提示', { type: 'warning' })
    const res = await request.delete(`/product/categories/${row.id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchCategories()
    }
  } catch (e) {}
}

// ========== 单位管理 ==========
const unitList = ref([])
const unitLoading = ref(false)
const unitDialogVisible = ref(false)
const isEditUnit = ref(false)
const unitForm = reactive({ id: null, unit_name: '', unit_code: '', is_base: false, conversion_rate: 1, sort_order: 0 })

const fetchUnits = async () => {
  unitLoading.value = true
  try {
    const res = await request.get('/product/units')
    if (res.code === 200) {
      unitList.value = res.data || []
    }
  } catch (e) {
    console.error('获取单位失败:', e)
  } finally {
    unitLoading.value = false
  }
}

const handleAddUnit = () => {
  isEditUnit.value = false
  unitForm.id = null
  unitForm.unit_name = ''
  unitForm.unit_code = ''
  unitForm.is_base = false
  unitForm.conversion_rate = 1
  unitForm.sort_order = 0
  unitDialogVisible.value = true
}

const handleEditUnit = (row) => {
  isEditUnit.value = true
  unitForm.id = row.id
  unitForm.unit_name = row.unit_name
  unitForm.unit_code = row.unit_code || ''
  unitForm.is_base = !!row.is_base
  unitForm.conversion_rate = row.conversion_rate || 1
  unitForm.sort_order = row.sort_order || 0
  unitDialogVisible.value = true
}

const saveUnit = async () => {
  if (!unitForm.unit_name.trim()) {
    ElMessage.warning('请输入单位名称')
    return
  }
  try {
    const payload = {
      unit_name: unitForm.unit_name,
      unit_code: unitForm.unit_code,
      is_base: unitForm.is_base ? 1 : 0,
      conversion_rate: unitForm.conversion_rate,
      sort_order: unitForm.sort_order
    }
    if (isEditUnit.value) {
      const res = await request.put(`/product/units/${unitForm.id}`, payload)
      if (res.code === 200) {
        ElMessage.success('修改成功')
        unitDialogVisible.value = false
        fetchUnits()
      }
    } else {
      const res = await request.post('/product/units', payload)
      if (res.code === 200) {
        ElMessage.success('添加成功')
        unitDialogVisible.value = false
        fetchUnits()
      }
    }
  } catch (e) {
    console.error('保存单位失败:', e)
  }
}

const handleDeleteUnit = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除单位"${row.unit_name}"？`, '提示', { type: 'warning' })
    const res = await request.delete(`/product/units/${row.id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchUnits()
    }
  } catch (e) {}
}

// ========== Tab切换时加载数据 ==========
watch(activeTab, (val) => {
  if (val === 'category') fetchCategories()
  if (val === 'unit') fetchUnits()
})

// ========== 其他功能 ==========
const saveBasicSettings = () => {
  ElMessage.success('保存成功')
}
</script>

<style lang="scss" scoped>
.settings-page {
  .mb-20 {
    margin-bottom: 20px;
  }

  .tab-toolbar {
    margin-bottom: 16px;
  }
}
</style>
