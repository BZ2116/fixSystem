<template>
  <div class="asset-page">
    <!-- 1. 客户优先选择区 -->
    <div class="customer-select-area">
      <div class="title">
        <el-icon><User /></el-icon>
        请先选择客户
      </div>
      <el-row :gutter="20" align="middle">
        <el-col :span="8">
          <el-select
            v-model="selectedCustomerId"
            placeholder="请选择客户"
            filterable
            remote
            :remote-method="fetchCustomerList"
            :loading="customerLoading"
            clearable
            style="width: 100%"
            @change="handleCustomerChange"
          >
            <el-option
              v-for="item in customerList"
              :key="item.id"
              :label="item.customer_name"
              :value="item.id"
            />
          </el-select>
        </el-col>
        <el-col :span="16" v-if="selectedCustomer">
          <el-card shadow="hover" class="customer-info-card">
            <el-descriptions :column="3" size="small">
              <el-descriptions-item label="客户名称">{{ selectedCustomer.customer_name }}</el-descriptions-item>
              <el-descriptions-item label="联系人">{{ selectedCustomer.contact_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="联系电话">{{ selectedCustomer.phone || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 2. 筛选条件区 -->
    <div class="filter-area" v-if="selectedCustomerId">
      <el-row :gutter="15">
        <el-col :span="6">
          <el-form-item label="所属办公室">
            <div style="display: flex; gap: 5px; width: 100%;">
              <el-select v-model="queryParams.office_id" placeholder="请选择" clearable style="flex: 1">
                <el-option
                  v-for="item in officeList"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
              <el-button icon="Plus" size="small" @click="openOfficeDialog()" title="添加办公室" />
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="设备登记时间">
            <el-date-picker
              v-model="queryParams.date_range"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="保修状态">
            <el-select v-model="queryParams.warranty_status" placeholder="请选择" clearable style="width: 100%">
              <el-option label="在保" value="in_warranty" />
              <el-option label="过保" value="out_warranty" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="设备类型">
            <el-select v-model="queryParams.asset_type_id" placeholder="请选择" clearable style="width: 100%">
              <el-option
                v-for="item in assetTypeList"
                :key="item.id"
                :label="item.type_name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="15">
        <el-col :span="6">
          <el-form-item label="设备名称">
            <el-input v-model="queryParams.name" placeholder="请输入" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="设备编号">
            <el-input v-model="queryParams.asset_no" placeholder="请输入" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="SN码">
            <el-input v-model="queryParams.sn" placeholder="请输入" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="资产状态">
            <el-select v-model="queryParams.status" placeholder="请选择" clearable style="width: 100%">
              <el-option label="正常使用" value="normal" />
              <el-option label="维修中" value="repair" />
              <el-option label="闲置" value="idle" />
              <el-option label="报废" value="scrap" />
              <el-option label="停用" value="stop" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="24" style="text-align: right">
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 3. 操作按钮行 -->
    <div class="toolbar" v-if="selectedCustomerId">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>新增资产
      </el-button>
      <el-button @click="handleBatchImport">
        <el-icon><Upload /></el-icon>批量导入
      </el-button>
      <el-button @click="handleBatchExport">
        <el-icon><Download /></el-icon>批量导出
      </el-button>
      <el-button @click="handlePrint">
        <el-icon><Printer /></el-icon>台账打印
      </el-button>
    </div>

    <!-- 4. 数据表格 -->
    <el-table
      v-if="selectedCustomerId"
      v-loading="loading"
      :data="tableData"
      border
      stripe
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column label="资产编号" width="120" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="asset-no">{{ row.asset_no }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="asset_name" label="资产名称" min-width="120" show-overflow-tooltip />
      <el-table-column label="资产类型" width="120">
        <template #default="{ row }">
          <el-icon v-if="getAssetTypeIcon(row.asset_type_code)">
            <component :is="getAssetTypeIcon(row.asset_type_code)" />
          </el-icon>
          {{ row.asset_type_name }}
        </template>
      </el-table-column>
      <el-table-column prop="customer_name" label="归属客户" min-width="120" show-overflow-tooltip />
      <el-table-column prop="office_name" label="所属办公室" width="120" />
      <el-table-column prop="sn_code" label="SN序列号" width="150" show-overflow-tooltip />
      <el-table-column prop="warranty_expire_date" label="质保到期日" width="120" />
      <el-table-column label="保修状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.warranty_status === 'in_warranty' ? 'success' : 'danger'" size="small">
            {{ row.warranty_status === 'in_warranty' ? '在保' : '过保' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="资产状态" width="100" align="center">
        <template #default="{ row }">
          <span :class="getStatusClass(row.status)">
            {{ getStatusText(row.status) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="handleDetail(row)">详情</el-button>
          <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="warning" size="small" @click="handleScrap(row)" v-if="row.status !== 'scrap'">报废</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 5. 分页 -->
    <el-pagination
      v-if="selectedCustomerId && total > 0"
      v-model:current-page="queryParams.page"
      v-model:page-size="queryParams.page_size"
      :page-sizes="[10, 20, 50, 100]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      class="pagination"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <!-- 6. 新增/编辑资产对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="900px"
      destroy-on-close
    >
      <el-steps :active="activeStep" finish-status="success" simple style="margin-bottom: 20px">
        <el-step title="选择客户" />
        <el-step title="基础信息" />
        <el-step title="时间信息" />
        <el-step title="责任人" />
        <el-step title="技术信息" />
      </el-steps>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        class="asset-form"
      >
        <!-- 步骤1：选择客户 -->
        <div v-show="activeStep === 0">
          <el-form-item label="选择客户" prop="customer_id">
            <el-select
              v-model="formData.customer_id"
              placeholder="请选择客户"
              filterable
              remote
              :remote-method="fetchCustomerList"
              :loading="customerLoading"
              :disabled="isEdit"
              style="width: 100%"
              @change="(val) => {
                const customer = customerList.find(c => c.id === val)
                formData.customer_name = customer ? customer.customer_name : ''
              }"
            >
              <el-option
                v-for="item in customerList"
                :key="item.id"
                :label="item.customer_name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </div>

        <!-- 步骤2：基础信息 -->
        <div v-show="activeStep === 1">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="资产类型" prop="asset_type_id">
                <el-select
                  v-model="formData.asset_type_id"
                  placeholder="请选择资产类型"
                  style="width: 100%"
                  @change="handleAssetTypeChange"
                >
                  <el-option
                    v-for="item in assetTypeList"
                    :key="item.id"
                    :label="item.type_name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="资产名称" prop="asset_name">
                <el-input v-model="formData.asset_name" placeholder="请输入资产名称" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="设备编号" prop="asset_no">
                <el-input v-model="formData.asset_no" placeholder="请输入设备编号" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="SN序列号" prop="sn_code">
                <el-input v-model="formData.sn_code" placeholder="请输入SN序列号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="所属办公室" prop="office_id">
                <el-select v-model="formData.office_id" placeholder="请选择" style="width: 100%">
                  <el-option
                    v-for="item in officeList"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="存放位置" prop="location">
                <el-input v-model="formData.location" placeholder="请输入存放位置" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 专属字段（根据资产类型自动显示） -->
          <template v-if="currentTypeFields.length > 0">
            <el-divider content-position="left">{{ currentAssetTypeName }}专属字段</el-divider>
            <el-row :gutter="20">
              <el-col
                v-for="field in currentTypeFields"
                :key="field.key"
                :span="field.type === 'textarea' ? 24 : 12"
              >
                <el-form-item :label="field.label" :prop="`extra_fields.${field.key}`">
                  <el-input
                    v-if="field.type === 'input'"
                    v-model="formData.extra_fields[field.key]"
                    :placeholder="`请输入${field.label}`"
                  />
                  <el-input-number
                    v-else-if="field.type === 'number'"
                    v-model="formData.extra_fields[field.key]"
                    :placeholder="`请输入${field.label}`"
                    style="width: 100%"
                  />
                  <el-input
                    v-else-if="field.type === 'textarea'"
                    v-model="formData.extra_fields[field.key]"
                    type="textarea"
                    :rows="3"
                    :placeholder="`请输入${field.label}`"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </template>
        </div>

        <!-- 步骤3：时间信息 -->
        <div v-show="activeStep === 2">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="登记日期" prop="register_date">
                <el-date-picker
                  v-model="formData.register_date"
                  type="date"
                  placeholder="请选择登记日期"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="采购日期" prop="purchase_date">
                <el-date-picker
                  v-model="formData.purchase_date"
                  type="date"
                  placeholder="请选择采购日期"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="质保到期日" prop="warranty_expire_date">
                <el-date-picker
                  v-model="formData.warranty_expire_date"
                  type="date"
                  placeholder="请选择质保到期日"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 步骤4：责任人信息 -->
        <div v-show="activeStep === 3">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="使用责任人" prop="responsible_person">
                <el-input v-model="formData.responsible_person" placeholder="请输入使用责任人" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="联系电话" prop="contact_phone">
                <el-input v-model="formData.contact_phone" placeholder="请输入联系电话" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 步骤5：通用技术字段 -->
        <div v-show="activeStep === 4">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="IP地址" prop="ip_address">
                <el-input v-model="formData.ip_address" placeholder="请输入IP地址" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="设备登录密码" prop="login_password">
                <el-input
                  v-model="formData.login_password"
                  type="password"
                  placeholder="请输入设备登录密码"
                  show-password
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="备注信息" prop="remark">
                <el-input
                  v-model="formData.remark"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入备注信息"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

      </el-form>

      <template #footer>
        <el-button v-if="activeStep > 0" @click="activeStep--">上一步</el-button>
        <el-button v-if="activeStep < 4" type="primary" @click="handleNextStep">下一步</el-button>
        <el-button v-if="activeStep === 4" type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
        <el-button @click="dialogVisible = false">取消</el-button>
      </template>
    </el-dialog>

    <!-- 7. 详情对话框 -->
    <el-dialog v-model="detailVisible" title="资产详情" width="800px">
      <el-descriptions :column="2" border v-if="detailData">
        <el-descriptions-item label="资产编号" :span="2">
          <span class="asset-no">{{ detailData.asset_no }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="归属客户">{{ detailData.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="所属办公室">{{ detailData.office_name }}</el-descriptions-item>
        
        <el-descriptions-item label="资产名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="资产类型">{{ detailData.asset_type_name }}</el-descriptions-item>
        
        <el-descriptions-item label="SN序列号">{{ detailData.sn || '-' }}</el-descriptions-item>
        <el-descriptions-item label="存放位置">{{ detailData.location || '-' }}</el-descriptions-item>
        
        <el-descriptions-item label="登记日期">{{ detailData.register_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="采购日期">{{ detailData.purchase_date || '-' }}</el-descriptions-item>
        
        <el-descriptions-item label="质保到期日">{{ detailData.warranty_end_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="保修状态">
          <el-tag :type="detailData.warranty_status === 'in_warranty' ? 'success' : 'danger'">
            {{ detailData.warranty_status === 'in_warranty' ? '在保' : '过保' }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="使用责任人">{{ detailData.responsible_person || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ detailData.contact_phone || '-' }}</el-descriptions-item>
        
        <el-descriptions-item label="IP地址">{{ detailData.ip_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备登录密码">{{ detailData.login_password ? '******' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="质保到期日">{{ detailData.warranty_expire_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="资产状态" :span="2">
          <span :class="getStatusClass(detailData.status)">
            {{ getStatusText(detailData.status) }}
          </span>
        </el-descriptions-item>
        
        <el-descriptions-item label="备注信息" :span="2">{{ detailData.remark || '-' }}</el-descriptions-item>
        
        <!-- 专属字段 -->
        <template v-if="detailData.extra_fields && Object.keys(detailData.extra_fields).length > 0">
          <el-descriptions-item :span="2">
            <template #label>
              <strong>{{ detailData.asset_type_name }}专属信息</strong>
            </template>
          </el-descriptions-item>
          <el-descriptions-item
            v-for="(value, key) in detailData.extra_fields"
            :key="key"
            :label="getExtraFieldLabel(detailData.asset_type_code, key)"
          >
            {{ value || '-' }}
          </el-descriptions-item>
        </template>
      </el-descriptions>
    </el-dialog>

    <!-- 打印对话框 -->
    <PrintDialog v-model:visible="printDialogVisible" template-type="asset" :print-data="printData" />

    <!-- 办公室管理对话框 -->
    <el-dialog v-model="officeDialogVisible" title="办公室管理" width="600px">
      <div style="margin-bottom: 15px;">
        <el-button type="primary" @click="openOfficeForm()">新增办公室</el-button>
      </div>
      <el-table :data="officeList" stripe border size="small">
        <el-table-column prop="name" label="办公室名称" min-width="120" />
        <el-table-column prop="code" label="编码" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openOfficeForm(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDeleteOffice(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!officeList.length" description="暂无办公室，请点击" />

      <!-- 新增/编辑办公室表单 -->
      <el-divider v-if="officeFormVisible" content-position="left">{{ editingOfficeId ? '编辑' : '新增' }}办公室</el-divider>
      <el-form v-if="officeFormVisible" :model="officeForm" :inline="true" style="margin-top: 15px;">
        <el-form-item label="名称" required>
          <el-input v-model="officeForm.name" placeholder="办公室名称" style="width: 150px;" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="officeForm.code" placeholder="编码" style="width: 120px;" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="officeForm.sort_order" :min="0" style="width: 100px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSaveOffice" :loading="officeLoading">保存</el-button>
          <el-button @click="officeFormVisible = false">取消</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Search, Refresh, Plus, Upload, Download, Printer,
  Monitor, Printer as PrinterIcon, VideoCamera, OfficeBuilding, Lock, Bell, Microphone, Box
} from '@element-plus/icons-vue'
import PrintDialog from '@/components/PrintDialog.vue'
import {
  getAssetTypeList, getAssetList, getAssetDetail, createAsset,
  updateAsset, deleteAsset, scrapAsset, exportAssets, getAssetsByCustomer
} from '@/api/asset'
import { getCustomerList } from '@/api/customer'
import { getOffices, createOffice, updateOffice, deleteOffice } from '@/api/office'

// 专属字段配置
const typeFields = {
  network: [
    { key: 'brand', label: '品牌', type: 'input' },
    { key: 'model', label: '型号', type: 'input' },
    { key: 'subnet_mask', label: '子网掩码', type: 'input' },
    { key: 'gateway', label: '网关', type: 'input' },
    { key: 'port_count', label: '端口数量', type: 'number' },
    { key: 'install_location', label: '安装位置', type: 'input' },
    { key: 'firmware_version', label: '固件版本', type: 'input' }
  ],
  computer: [
    { key: 'cpu', label: '处理器', type: 'input' },
    { key: 'memory', label: '内存', type: 'input' },
    { key: 'disk', label: '硬盘', type: 'input' },
    { key: 'os_version', label: '系统版本', type: 'input' },
    { key: 'peripherals', label: '外设配件', type: 'input' }
  ],
  printer: [
    { key: 'consumable_model', label: '耗材型号', type: 'input' },
    { key: 'paper_spec', label: '纸张规格', type: 'input' },
    { key: 'total_prints', label: '累计打印页数', type: 'number' },
    { key: 'toner_level', label: '墨粉余量', type: 'input' },
    { key: 'maintenance_cycle', label: '维保周期', type: 'input' }
  ],
  security: [
    { key: 'channel_no', label: '通道编号', type: 'input' },
    { key: 'storage_disk', label: '存储硬盘', type: 'input' },
    { key: 'pixel_spec', label: '像素规格', type: 'input' },
    { key: 'power_supply', label: '供电方式', type: 'input' },
    { key: 'record_duration', label: '录像时长', type: 'input' }
  ],
  server: [
    { key: 'rack_position', label: '机架位置', type: 'input' },
    { key: 'hardware_config', label: '硬件配置', type: 'textarea' },
    { key: 'port_mapping', label: '端口映射', type: 'input' },
    { key: 'running_load', label: '运行负载', type: 'input' },
    { key: 'maintenance_provider', label: '维保服务商', type: 'input' }
  ],
  access: [
    { key: 'open_method', label: '开门方式', type: 'input' },
    { key: 'storage_capacity', label: '存储容量', type: 'input' },
    { key: 'bound_persons', label: '绑定人员', type: 'textarea' },
    { key: 'control_area', label: '管控区域', type: 'input' }
  ],
  audio: [
    { key: 'power_param', label: '功率参数', type: 'input' },
    { key: 'channel_spec', label: '声道规格', type: 'input' },
    { key: 'connection_line', label: '连接线路', type: 'input' },
    { key: 'speaker_points', label: '喇叭点位', type: 'input' },
    { key: 'volume_preset', label: '音量预设参数', type: 'input' }
  ],
  other: [
    { key: 'custom_spec', label: '自定义规格参数', type: 'textarea' },
    { key: 'accessory_list', label: '配件清单', type: 'textarea' },
    { key: 'usage_purpose', label: '使用用途', type: 'input' }
  ]
}

// 资产类型图标映射
const typeIconMap = {
  network: Monitor,
  computer: Monitor,
  printer: PrinterIcon,
  security: VideoCamera,
  server: OfficeBuilding,
  access: Lock,
  audio: Microphone,
  other: Box
}

// 状态映射
const statusMap = {
  normal: { text: '正常使用', class: 'status-normal' },
  repair: { text: '维修中', class: 'status-repair' },
  idle: { text: '闲置', class: 'status-idle' },
  scrap: { text: '报废', class: 'status-scrap' },
  stop: { text: '停用', class: 'status-stop' }
}

// 响应式数据
const loading = ref(false)
const submitLoading = ref(false)
const customerLoading = ref(false)
const selectedCustomerId = ref(null)
const selectedCustomer = ref(null)
const customerList = ref([])
const assetTypeList = ref([])
const officeList = ref([])
const officeDialogVisible = ref(false)
const officeFormVisible = ref(false)
const officeForm = ref({ name: '', code: '', sort_order: 0 })
const editingOfficeId = ref(null)
const officeLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedRows = ref([])

// 查询参数
const queryParams = reactive({
  page: 1,
  page_size: 10,
  customer_id: null,
  office_id: null,
  date_range: null,
  warranty_status: null,
  asset_type_id: null,
  name: '',
  asset_no: '',
  sn: '',
  status: null
})

// 对话框相关
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const activeStep = ref(0)
const formRef = ref(null)

// 表单数据
const formData = reactive({
  id: null,
  customer_id: null,
  customer_name: '',
  asset_type_id: null,
  asset_name: '',
  asset_no: '',
  sn_code: '',
  office_id: null,
  location: '',
  register_date: '',
  purchase_date: '',
  warranty_expire_date: '',
  responsible_person: '',
  contact_phone: '',
  ip_address: '',
  login_password: '',
  remark: '',
  extra_fields: {}
})

// 表单校验规则
const formRules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  asset_type_id: [{ required: true, message: '请选择资产类型', trigger: 'change' }],
  asset_name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  asset_no: [{ required: true, message: '请输入设备编号', trigger: 'blur' }]
}

// 详情对话框
const detailVisible = ref(false)
const detailData = ref(null)

// 打印相关
const printDialogVisible = ref(false)
const printData = ref({})

// 计算属性
const currentAssetTypeCode = computed(() => {
  const type = assetTypeList.value.find(t => t.id === formData.asset_type_id)
  return type ? type.type_code : null
})

const currentAssetTypeName = computed(() => {
  const type = assetTypeList.value.find(t => t.id === formData.asset_type_id)
  return type ? type.type_name : ''
})

const currentTypeFields = computed(() => {
  const code = currentAssetTypeCode.value
  return code && typeFields[code] ? typeFields[code] : []
})

// 方法
const fetchCustomerList = async (keyword = '') => {
  customerLoading.value = true
  try {
    const res = await getCustomerList({ keyword, page_size: 50 })
    customerList.value = res.data?.list || []
  } catch (error) {
    console.error('获取客户列表失败:', error)
  } finally {
    customerLoading.value = false
  }
}

const fetchAssetTypeList = async () => {
  try {
    const res = await getAssetTypeList()
    assetTypeList.value = res.data || []
  } catch (error) {
    console.error('获取资产类型列表失败:', error)
  }
}

// 加载办公室列表
const fetchOfficeList = async () => {
  try {
    const res = await getOffices()
    officeList.value = res.data || []
  } catch (error) {
    console.error('获取办公室列表失败:', error)
  }
}

// 打开办公室管理对话框
const openOfficeDialog = () => {
  officeDialogVisible.value = true
  officeFormVisible.value = false
  editingOfficeId.value = null
}

// 打开办公室编辑表单
const openOfficeForm = (row) => {
  if (row) {
    editingOfficeId.value = row.id
    officeForm.value = { name: row.name, code: row.code || '', sort_order: row.sort_order || 0 }
  } else {
    editingOfficeId.value = null
    officeForm.value = { name: '', code: '', sort_order: 0 }
  }
  officeFormVisible.value = true
}

// 保存办公室
const handleSaveOffice = async () => {
  if (!officeForm.value.name) {
    ElMessage.warning('请输入办公室名称')
    return
  }
  officeLoading.value = true
  try {
    if (editingOfficeId.value) {
      await updateOffice(editingOfficeId.value, officeForm.value)
      ElMessage.success('更新成功')
    } else {
      await createOffice(officeForm.value)
      ElMessage.success('创建成功')
    }
    officeFormVisible.value = false
    fetchOfficeList()
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    officeLoading.value = false
  }
}

// 删除办公室
const handleDeleteOffice = (row) => {
  ElMessageBox.confirm(`确定要删除办公室"${row.name}"吗？`, '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      await deleteOffice(row.id)
      ElMessage.success('删除成功')
      fetchOfficeList()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }).catch(() => {})
}

const fetchAssetList = async () => {
  if (!selectedCustomerId.value) return
  
  loading.value = true
  try {
    const params = {
      ...queryParams,
      customer_id: selectedCustomerId.value
    }
    const res = await getAssetList(params)
    tableData.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (error) {
    console.error('获取资产列表失败:', error)
    ElMessage.error('获取资产列表失败')
  } finally {
    loading.value = false
  }
}

const handleCustomerChange = (val) => {
  selectedCustomer.value = customerList.value.find(c => c.id === val)
  queryParams.customer_id = val
  queryParams.page = 1
  fetchAssetList()
}

const handleSearch = () => {
  queryParams.page = 1
  fetchAssetList()
}

const handleReset = () => {
  queryParams.office_id = null
  queryParams.date_range = null
  queryParams.warranty_status = null
  queryParams.asset_type_id = null
  queryParams.name = ''
  queryParams.asset_no = ''
  queryParams.sn = ''
  queryParams.status = null
  queryParams.page = 1
  fetchAssetList()
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const handleSizeChange = (val) => {
  queryParams.page_size = val
  fetchAssetList()
}

const handleCurrentChange = (val) => {
  queryParams.page = val
  fetchAssetList()
}

const resetForm = () => {
  formData.id = null
  formData.customer_id = selectedCustomerId.value
  // 根据 customer_id 设置 customer_name
  const customer = customerList.value.find(c => c.id === selectedCustomerId.value)
  formData.customer_name = customer ? customer.customer_name : ''
  formData.asset_type_id = null
  formData.asset_name = ''
  formData.asset_no = ''
  formData.sn_code = ''
  formData.office_id = null
  formData.location = ''
  formData.register_date = ''
  formData.purchase_date = ''
  formData.warranty_expire_date = ''
  formData.responsible_person = ''
  formData.contact_phone = ''
  formData.ip_address = ''
  formData.login_password = ''
  formData.remark = ''
  formData.extra_fields = {}
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增资产'
  resetForm()
  activeStep.value = selectedCustomerId.value ? 1 : 0
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑资产'
  resetForm()
  
  try {
    const res = await getAssetDetail(row.id)
    const data = res.data
    Object.assign(formData, {
      id: data.id,
      customer_id: data.customer_id,
      asset_type_id: data.asset_type_id,
      asset_name: data.asset_name,
      asset_no: data.device_no,
      sn_code: data.sn_code,
      office_id: data.office_id,
      location: data.location,
      register_date: data.register_date,
      purchase_date: data.purchase_date,
      warranty_expire_date: data.warranty_expire_date,
      responsible_person: data.responsible_person,
      contact_phone: data.contact_phone,
      ip_address: data.ip_address,
      login_password: data.login_password,
      remark: data.remark,
      extra_fields: data.asset_data || {}
    })
    activeStep.value = 1
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取资产详情失败')
  }
}

const handleDetail = async (row) => {
  try {
    const res = await getAssetDetail(row.id)
    const data = res.data
    data.asset_type_code = data.asset_type_id ? (assetTypeList.value.find(t => t.id === data.asset_type_id)?.type_code || '') : ''
    detailData.value = data
    detailVisible.value = true
  } catch (error) {
    ElMessage.error('获取资产详情失败')
  }
}

const handleNextStep = async () => {
  if (activeStep.value === 0) {
    // 验证客户选择
    if (!formData.customer_id) {
      ElMessage.warning('请选择客户')
      return
    }
  } else if (activeStep.value === 1) {
    // 验证基础信息
    const valid = await formRef.value.validateField(['asset_type_id', 'asset_name', 'asset_no']).catch(() => false)
    if (!valid) return
  }
  activeStep.value++
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  submitLoading.value = true
  try {
    const data = { ...formData }
    if (isEdit.value) {
      await updateAsset(data.id, data)
      ElMessage.success('更新成功')
    } else {
      await createAsset(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchAssetList()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该资产吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteAsset(row.id)
      ElMessage.success('删除成功')
      fetchAssetList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const handleScrap = (row) => {
  ElMessageBox.confirm('确定要将该资产报废吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await scrapAsset(row.id)
      ElMessage.success('报废成功')
      fetchAssetList()
    } catch (error) {
      ElMessage.error('报废失败')
    }
  })
}

const handleBatchImport = () => {
  ElMessage.info('批量导入功能开发中')
}

const handleBatchExport = async () => {
  try {
    await exportAssets({ customer_id: selectedCustomerId.value })
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const handlePrint = () => {
  const customer = selectedCustomer.value || {}
  const assets = tableData.value || []

  // 构建资产列表HTML表格
  const assetListHtml = assets.length > 0
    ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead style="background:#f5f5f5;">
          <tr>
            <th style="border:1px solid #ddd;padding:8px;">序号</th>
            <th style="border:1px solid #ddd;padding:8px;">资产编号</th>
            <th style="border:1px solid #ddd;padding:8px;">资产名称</th>
            <th style="border:1px solid #ddd;padding:8px;">资产类型</th>
            <th style="border:1px solid #ddd;padding:8px;">所属办公室</th>
            <th style="border:1px solid #ddd;padding:8px;">SN序列号</th>
            <th style="border:1px solid #ddd;padding:8px;">质保到期日</th>
            <th style="border:1px solid #ddd;padding:8px;">保修状态</th>
            <th style="border:1px solid #ddd;padding:8px;">资产状态</th>
          </tr>
        </thead>
        <tbody>
          ${assets.map((item, index) => `
            <tr>
              <td style="border:1px solid #ddd;padding:8px;text-align:center;">${index + 1}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.asset_no || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.asset_name || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.asset_type_name || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.office_name || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.sn_code || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.warranty_expire_date || '-'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${item.warranty_status === 'in_warranty' ? '在保' : '过保'}</td>
              <td style="border:1px solid #ddd;padding:8px;">${getStatusText(item.status)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>`
    : '<p style="color:#999;">暂无资产数据</p>'

  printData.value = {
    customer_name: customer.customer_name || '-',
    contact_name: customer.contact_name || '-',
    phone: customer.phone || '-',
    asset_count: assets.length,
    asset_list_html: assetListHtml
  }
  printDialogVisible.value = true
}

const handleAssetTypeChange = () => {
  // 切换资产类型时重置专属字段
  formData.extra_fields = {}
}

const getAssetTypeIcon = (code) => {
  return typeIconMap[code] || null
}

const getStatusText = (status) => {
  return statusMap[status]?.text || status
}

const getStatusClass = (status) => {
  return statusMap[status]?.class || ''
}

const getExtraFieldLabel = (typeCode, key) => {
  const fields = typeFields[typeCode] || []
  const field = fields.find(f => f.key === key)
  return field ? field.label : key
}

// 初始化
onMounted(() => {
  fetchCustomerList()
  fetchAssetTypeList()
  fetchOfficeList()
})
</script>

<style scoped lang="scss">
.asset-page {
  padding: 20px;

  .customer-select-area {
    background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;

    .title {
      color: #7b1fa2;
      font-size: 18px;
      font-weight: bold;
      margin-bottom: 15px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .customer-info-card {
      background: rgba(255, 255, 255, 0.9);
      border: none;
    }
  }

  .filter-area {
    background: #fafafa;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
  }

  .toolbar {
    margin-bottom: 15px;
  }

  .el-table {
    :deep(th) {
      background: #f3e5f5 !important;
      color: #4a148c;
      font-weight: 600;
    }

    .asset-no {
      color: #7b1fa2;
      font-weight: bold;
    }
  }

  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }

  .status-normal {
    color: #4caf50;
    font-weight: 500;
  }

  .status-repair {
    color: #ff9800;
    font-weight: 500;
  }

  .status-idle {
    color: #9e9e9e;
    font-weight: 500;
  }

  .status-scrap {
    color: #f44336;
    font-weight: 500;
  }

  .status-stop {
    color: #757575;
    font-weight: 500;
  }

  .asset-form {
    max-height: 500px;
    overflow-y: auto;
    padding-right: 10px;
  }
}


</style>
