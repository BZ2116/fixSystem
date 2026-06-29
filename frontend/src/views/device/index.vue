<template>
  <div class="device-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>设备管理</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增设备</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- Tab1 - 客户设备 -->
        <el-tab-pane label="客户设备" name="customer">
          <el-form :inline="true" :model="customerSearch" class="search-form">
            <el-form-item label="关键词">
              <el-input v-model="customerSearch.keyword" placeholder="设备型号/序列号/客户名称" clearable @keyup.enter="handleCustomerSearch" />
            </el-form-item>
            <el-form-item label="设备类型">
              <el-select v-model="customerSearch.device_type" placeholder="全部" clearable>
                <el-option label="台式机" value="desktop" />
                <el-option label="笔记本" value="laptop" />
                <el-option label="服务器" value="server" />
                <el-option label="打印机" value="printer" />
                <el-option label="网络设备" value="network" />
                <el-option label="办公文具" value="office_supplies" />
                <el-option label="监控设备" value="monitor" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
            <el-form-item label="客户">
              <el-select v-model="customerSearch.customer_id" placeholder="全部" clearable filterable>
                <el-option v-for="item in customerOptions" :key="item.id" :label="item.customer_name" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="handleCustomerSearch">搜索</el-button>
              <el-button :icon="Refresh" @click="handleCustomerReset">重置</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="customerTableData" stripe border v-loading="customerLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column label="设备类型" width="100" align="center">
              <template #default="{ row }">
                {{ deviceTypeLabel(row.device_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="brand" label="品牌" width="100" />
            <el-table-column prop="model" label="型号" width="130" />
            <el-table-column prop="serial_number" label="序列号" width="150" />
            <el-table-column prop="customer_name" label="所属客户" min-width="120" />
            <el-table-column prop="contact_name" label="联系人" width="100" />
            <el-table-column prop="phone" label="电话" width="120" />
            <el-table-column prop="status" label="设备状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="purchase_date" label="购买日期" width="110" />
            <el-table-column label="操作" width="220" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" :icon="View" @click="handleView(row)">查看</el-button>
                <el-button type="primary" link size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
                <el-button type="warning" link size="small" :icon="Document" @click="handleRepairHistory(row)">维修历史</el-button>
                <el-button type="danger" link size="small" :icon="Delete" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="customerPagination.page"
            v-model:page-size="customerPagination.pageSize"
            :total="customerPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="handleCustomerSizeChange"
            @current-change="handleCustomerPageChange"
          />
        </el-tab-pane>

        <!-- Tab2 - 自有设备 -->
        <el-tab-pane label="自有设备" name="own">
          <el-form :inline="true" :model="ownSearch" class="search-form">
            <el-form-item label="关键词">
              <el-input v-model="ownSearch.keyword" placeholder="资产编号/型号/序列号" clearable @keyup.enter="handleOwnSearch" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="ownSearch.status" placeholder="全部" clearable>
                <el-option label="正常" value="normal" />
                <el-option label="维修中" value="repairing" />
                <el-option label="报废" value="scrapped" />
                <el-option label="外借" value="lent" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="handleOwnSearch">搜索</el-button>
              <el-button :icon="Refresh" @click="handleOwnReset">重置</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="ownTableData" stripe border v-loading="ownLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="asset_number" label="资产编号" width="130" />
            <el-table-column prop="device_type" label="设备类型" width="100" align="center" />
            <el-table-column prop="model" label="型号" width="130" />
            <el-table-column prop="serial_number" label="序列号" width="150" />
            <el-table-column prop="config_summary" label="配置摘要" min-width="180" show-overflow-tooltip />
            <el-table-column prop="location" label="存放位置" width="120" />
            <el-table-column prop="user_name" label="使用人" width="100" />
            <el-table-column prop="cost" label="成本" width="100" align="right">
              <template #default="{ row }">
                ¥{{ row.cost?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" :icon="View" @click="handleView(row)">查看</el-button>
                <el-button type="primary" link size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
                <el-button type="danger" link size="small" :icon="Delete" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="ownPagination.page"
            v-model:page-size="ownPagination.pageSize"
            :total="ownPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="handleOwnSizeChange"
            @current-change="handleOwnPageChange"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新增/编辑弹窗 - 客户设备 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="750px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所属客户" prop="customer_id">
              <el-select 
                v-model="form.customer_id" 
                placeholder="请选择客户" 
                filterable 
                style="width: 100%"
                :loading="customerLoading"
              >
                <el-option 
                  v-for="item in customerOptions" 
                  :key="item.id" 
                  :label="item.customer_name" 
                  :value="item.id" 
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备类型" prop="device_type">
              <el-select v-model="form.device_type" placeholder="请选择设备类型" style="width: 100%" @change="handleDeviceTypeChange">
                <el-option label="台式机" value="desktop" />
                <el-option label="笔记本" value="laptop" />
                <el-option label="服务器" value="server" />
                <el-option label="打印机" value="printer" />
                <el-option label="网络设备" value="network" />
                <el-option label="办公文具" value="office_supplies" />
                <el-option label="监控设备" value="monitor" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <!-- 通用字段：设备名称 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备名称" prop="device_name">
              <el-input v-model="form.device_name" placeholder="请输入设备名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备状态" prop="status">
              <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="正常" value="normal" />
                <el-option label="维修中" value="repairing" />
                <el-option label="报废" value="scrapped" />
                <el-option label="外借" value="lent" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 通用字段：设备密码 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备密码" prop="device_password">
              <el-input v-model="form.device_password" placeholder="请输入设备密码" type="password" show-password />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 办公文具特有字段 -->
        <template v-if="form.device_type === 'office_supplies'">
          <el-divider content-position="left">办公文具信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="品牌" prop="brand">
                <el-input v-model="form.brand" placeholder="请输入品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="型号" prop="model">
                <el-input v-model="form.model" placeholder="请输入型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="数量" prop="quantity">
                <el-input-number v-model="form.quantity" :min="1" :controls="false" placeholder="请输入数量" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- 监控设备特有字段 -->
        <template v-if="form.device_type === 'monitor'">
          <el-divider content-position="left">监控设备信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="IP地址" prop="ip_address">
                <el-input v-model="form.ip_address" placeholder="请输入IP地址" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="端口" prop="port">
                <el-input-number v-model="form.port" :min="1" :max="65535" :controls="false" placeholder="请输入端口" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- 打印机字段 -->
        <template v-if="form.device_type === 'printer'">
          <el-divider content-position="left">设备信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="品牌" prop="brand">
                <el-input v-model="form.brand" placeholder="请输入品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="型号" prop="model">
                <el-input v-model="form.model" placeholder="请输入型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="序列号" prop="serial_number">
                <el-input v-model="form.serial_number" placeholder="请输入序列号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-divider content-position="left">耗材信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="硒鼓型号">
                <el-input v-model="form.toner_model" placeholder="请输入硒鼓型号" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="粉盒型号">
                <el-input v-model="form.drum_model" placeholder="请输入粉盒型号" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- 网络设备字段 -->
        <template v-if="form.device_type === 'network'">
          <el-divider content-position="left">设备信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="品牌" prop="brand">
                <el-input v-model="form.brand" placeholder="请输入品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="型号" prop="model">
                <el-input v-model="form.model" placeholder="请输入型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="序列号" prop="serial_number">
                <el-input v-model="form.serial_number" placeholder="请输入序列号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-divider content-position="left">网络信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="IP地址">
                <el-input v-model="form.ip_address" placeholder="请输入IP地址" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="端口">
                <el-input-number v-model="form.port" :min="1" :max="65535" placeholder="端口" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- 其他设备字段 -->
        <template v-if="form.device_type === 'other'">
          <el-divider content-position="left">设备信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="品牌" prop="brand">
                <el-input v-model="form.brand" placeholder="请输入品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="型号" prop="model">
                <el-input v-model="form.model" placeholder="请输入型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="序列号" prop="serial_number">
                <el-input v-model="form.serial_number" placeholder="请输入序列号" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- IT设备字段（台式机、笔记本、服务器 - 完整配置信息） -->
        <template v-if="isITDevice(form.device_type)">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="品牌" prop="brand">
                <el-input v-model="form.brand" placeholder="请输入品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="型号" prop="model">
                <el-input v-model="form.model" placeholder="请输入型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="序列号" prop="serial_number">
                <el-input v-model="form.serial_number" placeholder="请输入序列号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-divider content-position="left">配置信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="CPU" prop="cpu">
                <el-input v-model="form.cpu" placeholder="请输入CPU" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="内存" prop="memory">
                <el-input v-model="form.memory" placeholder="请输入内存" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="硬盘" prop="disk">
                <el-input v-model="form.disk" placeholder="请输入硬盘" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="系统" prop="os">
                <el-input v-model="form.os" placeholder="请输入操作系统" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="系统版本" prop="os_version">
                <el-input v-model="form.os_version" placeholder="请输入系统版本" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="配件" prop="accessories">
                <el-input v-model="form.accessories" placeholder="请输入配件" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-divider content-position="left">账号信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="账号" prop="account">
                <el-input v-model="form.account" placeholder="请输入账号" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="密码" prop="password">
                <el-input v-model="form.password" placeholder="请输入密码" type="password" show-password />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="密码备注" prop="password_remark">
                <el-input v-model="form.password_remark" placeholder="请输入密码备注" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        <el-divider content-position="left">其他信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="购买日期" prop="purchase_date">
              <el-date-picker v-model="form.purchase_date" type="date" placeholder="请选择购买日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="维保到期" prop="warranty_expire">
              <el-date-picker v-model="form.warranty_expire" type="date" placeholder="请选择维保到期日" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑弹窗 - 自有设备 -->
    <el-dialog
      v-model="ownDialogVisible"
      :title="ownDialogTitle"
      width="750px"
      @close="handleOwnDialogClose"
    >
      <el-form ref="ownFormRef" :model="ownForm" :rules="ownFormRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="资产编号" prop="asset_number">
              <el-input v-model="ownForm.asset_number" placeholder="请输入资产编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备类型" prop="device_type">
              <el-select v-model="ownForm.device_type" placeholder="请选择设备类型" style="width: 100%">
                <el-option label="台式机" value="desktop" />
                <el-option label="笔记本" value="laptop" />
                <el-option label="服务器" value="server" />
                <el-option label="打印机" value="printer" />
                <el-option label="网络设备" value="network" />
                <el-option label="办公文具" value="office_supplies" />
                <el-option label="监控设备" value="monitor" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="型号" prop="model">
              <el-input v-model="ownForm.model" placeholder="请输入型号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="序列号" prop="serial_number">
              <el-input v-model="ownForm.serial_number" placeholder="请输入序列号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="ownForm.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="正常" value="normal" />
                <el-option label="维修中" value="repairing" />
                <el-option label="报废" value="scrapped" />
                <el-option label="外借" value="lent" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="成本" prop="cost">
              <el-input-number v-model="ownForm.cost" :min="0" :precision="2" :controls="false" placeholder="请输入成本" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">配置信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="CPU" prop="cpu">
              <el-input v-model="ownForm.cpu" placeholder="请输入CPU" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="内存" prop="memory">
              <el-input v-model="ownForm.memory" placeholder="请输入内存" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="硬盘" prop="disk">
              <el-input v-model="ownForm.disk" placeholder="请输入硬盘" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="系统" prop="os">
              <el-input v-model="ownForm.os" placeholder="请输入操作系统" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="配件" prop="accessories">
              <el-input v-model="ownForm.accessories" placeholder="请输入配件" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="账号" prop="account">
              <el-input v-model="ownForm.account" placeholder="请输入账号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="ownForm.password" placeholder="请输入密码" type="password" show-password />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="购买日期" prop="purchase_date">
              <el-date-picker v-model="ownForm.purchase_date" type="date" placeholder="请选择购买日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="维保到期" prop="warranty_expire">
              <el-date-picker v-model="ownForm.warranty_expire" type="date" placeholder="请选择维保到期日" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="存放位置" prop="location">
              <el-input v-model="ownForm.location" placeholder="请输入存放位置" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="使用人" prop="user_name">
              <el-input v-model="ownForm.user_name" placeholder="请输入使用人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="折旧" prop="depreciation">
              <el-input-number v-model="ownForm.depreciation" :min="0" :precision="2" :controls="false" placeholder="请输入折旧" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="ownForm.remark" type="textarea" :rows="3" placeholder="请输入备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="ownDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleOwnSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="设备详情"
      width="850px"
    >
      <el-descriptions :column="2" border>
        <!-- 通用字段 -->
        <el-descriptions-item label="所属客户">{{ detailData.customer_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ deviceTypeLabel(detailData.device_type) }}</el-descriptions-item>
        <el-descriptions-item label="品牌">{{ detailData.device_brand || detailData.brand || '-' }}</el-descriptions-item>
        <el-descriptions-item label="型号">{{ detailData.device_model || detailData.model || '-' }}</el-descriptions-item>
        <el-descriptions-item label="序列号">{{ detailData.device_sn || detailData.serial_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备状态">
          <el-tag :type="statusTagType(detailData.status)" size="small">{{ statusLabel(detailData.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="联系人">{{ detailData.contact_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ detailData.phone || '-' }}</el-descriptions-item>

        <!-- IT设备特有字段：台式机、笔记本、服务器 -->
        <template v-if="['desktop', 'laptop', 'server'].includes(detailData.device_type)">
          <el-descriptions-item label="CPU">{{ detailData.cpu || '-' }}</el-descriptions-item>
          <el-descriptions-item label="内存">{{ detailData.memory || '-' }}</el-descriptions-item>
          <el-descriptions-item label="硬盘">{{ detailData.disk || '-' }}</el-descriptions-item>
          <el-descriptions-item label="系统">{{ detailData.os || '-' }}</el-descriptions-item>
          <el-descriptions-item label="系统版本">{{ detailData.os_version || '-' }}</el-descriptions-item>
          <el-descriptions-item label="配件">{{ detailData.accessories || '-' }}</el-descriptions-item>
          <el-descriptions-item label="账号">{{ detailData.account || '-' }}</el-descriptions-item>
          <el-descriptions-item label="密码">{{ detailData.password || detailData.device_password || '-' }}</el-descriptions-item>
        </template>

        <!-- 打印机特有字段 -->
        <template v-if="detailData.device_type === 'printer'">
          <el-descriptions-item label="耗材型号">{{ detailData.consumable_model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="硒鼓型号">{{ detailData.toner_model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="粉盒型号">{{ detailData.drum_model || '-' }}</el-descriptions-item>
        </template>

        <!-- 网络设备：显示IP地址、端口、账号、密码 -->
        <template v-if="detailData.device_type === 'network'">
          <el-descriptions-item label="IP地址">{{ detailData.ip_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="端口">{{ detailData.port || '-' }}</el-descriptions-item>
          <el-descriptions-item label="账号">{{ detailData.account || '-' }}</el-descriptions-item>
          <el-descriptions-item label="密码">{{ detailData.password || detailData.device_password || '-' }}</el-descriptions-item>
        </template>

        <!-- 其他设备：显示账号密码 -->
        <template v-if="detailData.device_type === 'other'">
          <el-descriptions-item label="账号">{{ detailData.account || '-' }}</el-descriptions-item>
          <el-descriptions-item label="密码">{{ detailData.password || detailData.device_password || '-' }}</el-descriptions-item>
        </template>

        <!-- 办公文具特有字段 -->
        <template v-if="detailData.device_type === 'office_supplies'">
          <el-descriptions-item label="数量">{{ detailData.quantity || '-' }}</el-descriptions-item>
        </template>

        <!-- 监控设备特有字段 -->
        <template v-if="detailData.device_type === 'monitor'">
          <el-descriptions-item label="IP地址">{{ detailData.ip_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="端口">{{ detailData.port || '-' }}</el-descriptions-item>
          <el-descriptions-item label="账号">{{ detailData.account || '-' }}</el-descriptions-item>
          <el-descriptions-item label="密码">{{ detailData.password || detailData.device_password || '-' }}</el-descriptions-item>
        </template>

        <el-descriptions-item label="购买日期">{{ formatDate(detailData.purchase_date) }}</el-descriptions-item>
        <el-descriptions-item label="维保到期">{{ formatDate(detailData.warranty_expire) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detailData.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 维修历史弹窗 -->
    <el-dialog
      v-model="repairHistoryVisible"
      title="维修历史"
      width="750px"
    >
      <el-table :data="repairHistoryData" stripe border v-loading="repairHistoryLoading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="repair_date" label="维修日期" width="120" />
        <el-table-column prop="repair_type" label="维修类型" width="120" />
        <el-table-column prop="description" label="故障描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="repair_content" label="维修内容" min-width="180" show-overflow-tooltip />
        <el-table-column prop="cost" label="维修费用" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.cost?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
              {{ row.status === 'completed' ? '已完成' : '进行中' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, View, Edit, Delete, Document } from '@element-plus/icons-vue'
import { getDeviceList, createDevice, updateDevice, deleteDevice, getDeviceRepairHistory, getOwnDeviceList, createOwnDevice, updateOwnDevice, deleteOwnDevice } from '@/api/device'
import { getCustomerList } from '@/api/customer'

// ==================== 公共 ====================
const activeTab = ref('customer')
const customerOptions = ref([])

const statusTagType = (status) => {
  const map = { normal: 'success', repairing: 'warning', scrapped: 'danger', lent: 'info' }
  return map[status] || 'info'
}

const statusLabel = (status) => {
  const map = { normal: '正常', repairing: '维修中', scrapped: '报废', lent: '外借' }
  return map[status] || '未知'
}

// 设备类型转换
const deviceTypeLabel = (type) => {
  const map = {
    desktop: '台式机',
    laptop: '笔记本',
    server: '服务器',
    printer: '打印机',
    network: '网络设备',
    office_supplies: '办公文具',
    monitor: '监控设备',
    other: '其他'
  }
  return map[type] || type || '未知'
}

// 日期格式化
const formatDate = (date) => {
  if (!date) return '-'
  if (typeof date === 'string' && date.includes('GMT')) {
    const d = new Date(date)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }
  return date
}

// 判断是否为IT设备（显示完整配置信息：CPU、内存、硬盘等）
const isITDevice = (deviceType) => {
  return ['desktop', 'laptop', 'server'].includes(deviceType)
}

// 判断是否为外设/网络设备（显示品牌、型号、序列号，但不显示配置信息）
const isPeripheralDevice = (deviceType) => {
  return ['printer', 'network', 'other'].includes(deviceType)
}

// 设备类型改变时处理
const handleDeviceTypeChange = (val) => {
  // 根据设备类型重置相关字段
  if (val === 'office_supplies') {
    // 办公文具：重置IT设备字段
    form.cpu = ''
    form.memory = ''
    form.disk = ''
    form.os = ''
    form.os_version = ''
    form.serial_number = ''
    form.account = ''
    form.password = ''
    form.password_remark = ''
    form.ip_address = ''
    form.port = null
  } else if (val === 'monitor') {
    // 监控设备：重置IT设备和办公文具字段
    form.cpu = ''
    form.memory = ''
    form.disk = ''
    form.os = ''
    form.os_version = ''
    form.serial_number = ''
    form.account = ''
    form.password = ''
    form.password_remark = ''
    form.quantity = null
  } else {
    // IT设备：重置办公文具和监控设备字段
    form.quantity = null
    form.ip_address = ''
    form.port = null
  }
}

// ==================== 客户设备 ====================
const customerLoading = ref(false)
const customerTableData = ref([])
const customerSearch = reactive({
  keyword: '',
  device_type: '',
  customer_id: ''
})
const customerPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const fetchCustomerDevices = async () => {
  customerLoading.value = true
  try {
    const res = await getDeviceList({
      page: customerPagination.page,
      page_size: customerPagination.pageSize,
      keyword: customerSearch.keyword,
      device_type: customerSearch.device_type,
      customer_id: customerSearch.customer_id
    })
    if (res.code === 200) {
      customerTableData.value = res.data.list
      customerPagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取客户设备列表失败:', error)
  } finally {
    customerLoading.value = false
  }
}

const handleCustomerSearch = () => {
  customerPagination.page = 1
  fetchCustomerDevices()
}

const handleCustomerReset = () => {
  customerSearch.keyword = ''
  customerSearch.device_type = ''
  customerSearch.customer_id = ''
  handleCustomerSearch()
}

const handleCustomerSizeChange = (val) => {
  customerPagination.pageSize = val
  fetchCustomerDevices()
}

const handleCustomerPageChange = (val) => {
  customerPagination.page = val
  fetchCustomerDevices()
}

// ==================== 自有设备 ====================
const ownLoading = ref(false)
const ownTableData = ref([])
const ownSearch = reactive({
  keyword: '',
  status: ''
})
const ownPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const fetchOwnDevices = async () => {
  ownLoading.value = true
  try {
    const res = await getOwnDeviceList({
      page: ownPagination.page,
      page_size: ownPagination.pageSize,
      keyword: ownSearch.keyword,
      status: ownSearch.status
    })
    if (res.code === 200) {
      ownTableData.value = res.data.list
      ownPagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取自有设备列表失败:', error)
  } finally {
    ownLoading.value = false
  }
}

const handleOwnSearch = () => {
  ownPagination.page = 1
  fetchOwnDevices()
}

const handleOwnReset = () => {
  ownSearch.keyword = ''
  ownSearch.status = ''
  handleOwnSearch()
}

const handleOwnSizeChange = (val) => {
  ownPagination.pageSize = val
  fetchOwnDevices()
}

const handleOwnPageChange = (val) => {
  ownPagination.page = val
  fetchOwnDevices()
}

// ==================== Tab切换 ====================
const handleTabChange = (tab) => {
  if (tab === 'customer') {
    fetchCustomerDevices()
  } else {
    fetchOwnDevices()
  }
}

// ==================== 客户设备 - 新增/编辑 ====================
const dialogVisible = ref(false)
const dialogTitle = ref('新增客户设备')
const formRef = ref()
const isCustomerEdit = ref(false)

const getDefaultForm = () => ({
  id: null,
  customer_id: '',
  device_type: '',
  device_name: '',
  device_password: '',
  brand: '',
  model: '',
  serial_number: '',
  status: 'normal',
  cpu: '',
  memory: '',
  disk: '',
  os: '',
  os_version: '',
  accessories: '',
  account: '',
  password: '',
  password_remark: '',
  purchase_date: '',
  warranty_expire: '',
  remark: '',
  // 办公文具特有字段
  quantity: null,
  // 监控设备特有字段
  ip_address: '',
  port: null
})

const form = reactive(getDefaultForm())

const formRules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  device_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }]
}

const handleAdd = () => {
  if (activeTab.value === 'customer') {
    dialogTitle.value = '新增客户设备'
    isCustomerEdit.value = false
    dialogVisible.value = true
  } else {
    ownDialogTitle.value = '新增自有设备'
    isOwnEdit.value = false
    ownDialogVisible.value = true
  }
}

const handleEdit = (row) => {
  if (activeTab.value === 'customer') {
    dialogTitle.value = '编辑客户设备'
    isCustomerEdit.value = true
    Object.assign(form, row)
    dialogVisible.value = true
  } else {
    ownDialogTitle.value = '编辑自有设备'
    isOwnEdit.value = true
    Object.assign(ownForm, row)
    ownDialogVisible.value = true
  }
}

const handleView = (row) => {
  if (activeTab.value === 'customer') {
    Object.assign(detailData, row)
    detailVisible.value = true
  } else {
    ownDialogTitle.value = '查看自有设备'
    isOwnEdit.value = true
    Object.assign(ownForm, row)
    ownDialogVisible.value = true
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      let res
      if (form.id) {
        res = await updateDevice(form.id, form)
      } else {
        res = await createDevice(form)
      }
      if (res.code === 200) {
        ElMessage.success(dialogTitle.value + '成功')
        dialogVisible.value = false
        fetchCustomerDevices()
      }
    } catch (error) {
      console.error('操作失败:', error)
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(form, getDefaultForm())
}

// ==================== 自有设备 - 新增/编辑 ====================
const ownDialogVisible = ref(false)
const ownDialogTitle = ref('新增自有设备')
const ownFormRef = ref()
const isOwnEdit = ref(false)

const getDefaultOwnForm = () => ({
  id: null,
  asset_number: '',
  device_type: '',
  model: '',
  serial_number: '',
  status: 'normal',
  cpu: '',
  memory: '',
  disk: '',
  os: '',
  accessories: '',
  account: '',
  password: '',
  purchase_date: '',
  warranty_expire: '',
  location: '',
  user_name: '',
  cost: 0,
  depreciation: 0,
  remark: ''
})

const ownForm = reactive(getDefaultOwnForm())

const ownFormRules = {
  asset_number: [{ required: true, message: '请输入资产编号', trigger: 'blur' }],
  device_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  model: [{ required: true, message: '请输入型号', trigger: 'blur' }],
  serial_number: [{ required: true, message: '请输入序列号', trigger: 'blur' }]
}

const handleOwnSubmit = async () => {
  if (!ownFormRef.value) return
  await ownFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      let res
      if (ownForm.id) {
        res = await updateOwnDevice(ownForm.id, ownForm)
      } else {
        res = await createOwnDevice(ownForm)
      }
      if (res.code === 200) {
        ElMessage.success(ownDialogTitle.value + '成功')
        ownDialogVisible.value = false
        fetchOwnDevices()
      }
    } catch (error) {
      console.error('操作失败:', error)
    }
  })
}

const handleOwnDialogClose = () => {
  ownFormRef.value?.resetFields()
  Object.assign(ownForm, getDefaultOwnForm())
}

// ==================== 详情弹窗 ====================
const detailVisible = ref(false)
const detailData = reactive({})

// ==================== 维修历史 ====================
const repairHistoryVisible = ref(false)
const repairHistoryData = ref([])
const repairHistoryLoading = ref(false)

const handleRepairHistory = async (row) => {
  repairHistoryVisible.value = true
  repairHistoryLoading.value = true
  try {
    const res = await getDeviceRepairHistory(row.id)
    if (res.code === 200) {
      repairHistoryData.value = res.data
    }
  } catch (error) {
    console.error('获取维修历史失败:', error)
  } finally {
    repairHistoryLoading.value = false
  }
}

// ==================== 删除 ====================
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该设备吗？', '提示', { type: 'warning' })
    const api = activeTab.value === 'customer' ? deleteDevice : deleteOwnDevice
    const res = await api(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      if (activeTab.value === 'customer') {
        fetchCustomerDevices()
      } else {
        fetchOwnDevices()
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// ==================== 加载客户列表 ====================
const fetchCustomerOptions = async () => {
  try {
    const res = await getCustomerList({ page: 1, page_size: 9999 })
    if (res.code === 200) {
      customerOptions.value = res.data.list || []
    }
  } catch (error) {
    console.error('获取客户列表失败:', error)
  }
}

// ==================== 初始化 ====================
onMounted(() => {
  fetchCustomerDevices()
  fetchCustomerOptions()
})
</script>

<style lang="scss" scoped>
.device-page {
  .card-header {
    display: flex;
    justify-content: space-between;
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
}
</style>
