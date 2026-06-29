<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="batch-dialog-content">
      <!-- 已选数据摘要 -->
      <el-alert
        :title="`已选择 ${selectedCount} 条数据`"
        type="info"
        :closable="false"
        style="margin-bottom: 16px"
      />
      
      <!-- 批量修改分类 -->
      <template v-if="operationType === 'category'">
        <el-form label-width="120px">
          <el-form-item label="新分类" required>
            <el-select v-model="batchForm.category_id" placeholder="选择新分类" style="width: 100%">
              <el-option
                v-for="item in categoryOptions"
                :key="item.id"
                :label="item.category_name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </template>
      
      <!-- 批量修改价格 -->
      <template v-if="operationType === 'price'">
        <el-form label-width="120px">
          <el-form-item label="采购价">
            <el-input-number v-model="batchForm.purchase_price" :min="0" :precision="4" style="width: 100%" placeholder="不修改则留空" />
          </el-form-item>
          <el-form-item label="销售价">
            <el-input-number v-model="batchForm.sale_price" :min="0" :precision="4" style="width: 100%" placeholder="不修改则留空" />
          </el-form-item>
          <el-form-item label="成本价">
            <el-input-number v-model="batchForm.cost_price" :min="0" :precision="4" style="width: 100%" placeholder="不修改则留空" />
          </el-form-item>
          <el-form-item label="会员价">
            <el-input-number v-model="batchForm.member_price" :min="0" :precision="4" style="width: 100%" placeholder="不修改则留空" />
          </el-form-item>
          <el-form-item label="批发价">
            <el-input-number v-model="batchForm.wholesale_price" :min="0" :precision="4" style="width: 100%" placeholder="不修改则留空" />
          </el-form-item>
        </el-form>
        <el-alert title="提示：留空的字段将保持原有数据不变" type="warning" :closable="false" />
      </template>
      
      <!-- 批量修改库存预警 -->
      <template v-if="operationType === 'stock_warning'">
        <el-form label-width="120px">
          <el-form-item label="最低库存" required>
            <el-input-number v-model="batchForm.min_stock" :min="0" style="width: 100%" />
          </el-form-item>
          <el-form-item label="最高库存">
            <el-input-number v-model="batchForm.max_stock" :min="0" style="width: 100%" placeholder="不修改则留空" />
          </el-form-item>
        </el-form>
      </template>
      
      <!-- 批量修改排序 -->
      <template v-if="operationType === 'sort'">
        <el-form label-width="120px">
          <el-form-item label="排序值" required>
            <el-input-number v-model="batchForm.sort_order" :min="0" style="width: 100%" />
          </el-form-item>
        </el-form>
      </template>
      
      <!-- 批量禁用/启用确认 -->
      <template v-if="operationType === 'disable' || operationType === 'enable'">
        <el-alert
          :title="operationType === 'disable' ? '确定要批量禁用选中的商品吗？禁用后商品将不可使用' : '确定要批量启用选中的商品吗？'"
          :type="operationType === 'disable' ? 'warning' : 'success'"
          :closable="false"
          show-icon
        />
      </template>
      
      <!-- 批量删除确认 -->
      <template v-if="operationType === 'delete'">
        <el-alert
          title="确定要批量删除选中的商品吗？此操作不可恢复！"
          type="error"
          :closable="false"
          show-icon
        />
        <div style="margin-top: 16px; color: #f56c6c; font-size: 14px">
          <p>注意：已产生业务记录的商品将无法删除</p>
        </div>
      </template>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleConfirm" :loading="loading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  operationType: {
    type: String,
    required: true
  },
  selectedCount: {
    type: Number,
    default: 0
  },
  categoryOptions: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const title = computed(() => {
  const titles = {
    category: '批量修改分类',
    price: '批量修改价格',
    stock_warning: '批量设置库存预警',
    sort: '批量修改排序',
    disable: '批量禁用',
    enable: '批量启用',
    delete: '批量删除'
  }
  return titles[props.operationType] || '批量操作'
})

const batchForm = ref({
  category_id: null,
  purchase_price: undefined,
  sale_price: undefined,
  cost_price: undefined,
  member_price: undefined,
  wholesale_price: undefined,
  min_stock: undefined,
  max_stock: undefined,
  sort_order: undefined
})

// 监听弹窗打开，重置表单
watch(() => props.modelValue, (val) => {
  if (val) {
    resetForm()
  }
})

const resetForm = () => {
  batchForm.value = {
    category_id: null,
    purchase_price: undefined,
    sale_price: undefined,
    cost_price: undefined,
    member_price: undefined,
    wholesale_price: undefined,
    min_stock: undefined,
    max_stock: undefined,
    sort_order: undefined
  }
}

const handleClose = () => {
  visible.value = false
  resetForm()
}

const handleConfirm = () => {
  // 校验
  if (props.operationType === 'category' && !batchForm.value.category_id) {
    ElMessage.warning('请选择新分类')
    return
  }
  if (props.operationType === 'stock_warning' && batchForm.value.min_stock === undefined) {
    ElMessage.warning('请设置最低库存')
    return
  }
  if (props.operationType === 'sort' && batchForm.value.sort_order === undefined) {
    ElMessage.warning('请设置排序值')
    return
  }
  
  // 过滤掉undefined的字段，只提交有值的字段
  const submitData = {}
  for (const [key, value] of Object.entries(batchForm.value)) {
    if (value !== undefined && value !== null) {
      submitData[key] = value
    }
  }
  
  emit('confirm', props.operationType, submitData)
}
</script>

<style scoped>
.batch-dialog-content {
  padding: 10px 0;
}
</style>
