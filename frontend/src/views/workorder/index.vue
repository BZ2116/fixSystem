<template>
  <div class="workorder-page">
    <!-- ==================== 1. 统计卡片（顶部8个） ==================== -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="3" v-for="item in statCards" :key="item.key">
        <el-card shadow="hover" class="stat-card" :body-style="{ padding: '16px' }">
          <div class="stat-content">
            <p class="stat-label">{{ item.label }}</p>
            <p class="stat-value" :class="item.colorClass">{{ item.value }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ==================== 2. 主内容区 ==================== -->
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">工单管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
            <el-button type="primary" :icon="Plus" v-permission="'workorder:add'" @click="handleAdd">新建工单</el-button>
          </div>
        </div>
        <!-- 批量操作工具栏 -->
        <div v-if="selectedWorkorders.length > 0" class="batch-toolbar">
          <el-button type="danger" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
          <el-tag type="info" style="margin-left: 10px">已选择 {{ selectedWorkorders.length }} 项</el-tag>
        </div>
      </template>

      <!-- ==================== 3. 搜索栏 ==================== -->
      <el-form :inline="true" :model="searchForm" class="search-form" @submit.prevent="fetchData">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="工单号/客户/电话" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="工单类型">
          <el-select v-model="searchForm.wo_type" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="(label, key) in woTypeMap" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="(label, key) in statusMap" :key="key" :label="label" :value="parseInt(key)" />
          </el-select>
        </el-form-item>
        <el-form-item label="工程师">
          <el-select v-model="searchForm.assigned_user_id" placeholder="全部" clearable filterable style="width: 120px">
            <el-option v-for="u in userList" :key="u.id" :label="u.real_name || u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="金额范围">
          <el-input-number v-model="searchForm.min_amount" :min="0" :precision="2" placeholder="最低" controls-position="right" style="width: 110px" />
          <span style="margin: 0 4px; color: #999;">-</span>
          <el-input-number v-model="searchForm.max_amount" :min="0" :precision="2" placeholder="最高" controls-position="right" style="width: 110px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- ==================== 4. 列表表格 ==================== -->
      <el-table :data="tableData" stripe border v-loading="loading" @row-click="handleView" @selection-change="handleSelectionChange" style="width: 100%">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="wo_no" label="工单号" width="160">
          <template #default="{ row }">
            <el-link type="primary" @click.stop="handleView(row)">{{ row.wo_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="wo_type" label="类型" width="160">
          <template #default="{ row }">
            {{ woTypeMap[row.wo_type] || row.wo_type }}
            <span v-if="row.sub_type_name" style="color:#999;font-size:12px"> / {{ row.sub_type_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户名称" min-width="100" show-overflow-tooltip />
        <el-table-column prop="customer_phone" label="电话" width="120" />
        <el-table-column prop="assigned_user_name" label="工程师" width="90" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ statusMap[row.status] || '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_cost" label="费用" width="100" align="right">
          <template #default="{ row }">
            <span v-if="row.total_cost != null">¥{{ Number(row.total_cost).toFixed(2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="info" link size="small" @click.stop="handleView(row)">详情</el-button>
            <template v-for="(btn, idx) in primaryActions[row.status] || []" :key="idx">
              <el-button :type="btn.type" link size="small" @click.stop="handlePrimaryAction(btn.action, row)">{{ btn.label }}</el-button>
            </template>
            <el-dropdown trigger="click" v-if="(moreActions[row.status] || []).length > 0 || (row.status !== 9 && row.status !== 10)">
              <el-button type="info" link size="small">
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click.stop="handlePrint(row)">打印</el-dropdown-item>
                  <el-dropdown-item @click.stop="handleEdit(row)">编辑</el-dropdown-item>
                  <el-dropdown-item v-for="(item, idx) in moreActions[row.status] || []" :key="idx" @click.stop="handleMoreAction(item.action, row)">
                    {{ item.label }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </el-card>

    <!-- ==================== 5. 新建/编辑对话框（950px） ==================== -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑工单' : '新建工单'"
      width="950px"
      destroy-on-close
      :close-on-click-modal="false"
      top="3vh"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px" size="default">
        <!-- 客户信息区 -->
        <el-divider content-position="left">客户信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户名称" prop="customer_name">
              <el-autocomplete
                v-model="formData.customer_name"
                :fetch-suggestions="queryCustomerSuggestions"
                placeholder="输入客户名称搜索（可手动输入）"
                clearable
                style="width: 100%"
                @select="onCustomerSelect"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="formData.customer_phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户单位">
              <el-input v-model="formData.customer_company" placeholder="客户单位" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="办公室">
              <el-input v-model="formData.customer_office" placeholder="办公室/部门" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="详细地址">
              <el-input v-model="formData.customer_address" placeholder="详细地址" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 员工信息区 -->
        <el-divider content-position="left">员工信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="接待员工">
              <el-select v-model="formData.reception_user_id" placeholder="选择接待员工" filterable style="width: 100%">
                <el-option v-for="u in userList" :key="u.id" :label="u.real_name || u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="接单方式" required>
              <el-select v-model="formData.order_source" placeholder="选择接单方式" style="width: 100%">
                <el-option label="微信" value="wechat" />
                <el-option label="电话" value="phone" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="处理方式" required>
              <el-select v-model="formData.service_type" placeholder="选择处理方式" style="width: 100%">
                <el-option label="上门" value="onsite" />
                <el-option label="远程" value="remote" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 工单类型选择 -->
        <el-divider content-position="left">工单类型</el-divider>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="工单类型" prop="wo_type">
              <el-radio-group v-model="formData.wo_type" @change="onWoTypeChange">
                <el-radio-button v-for="(label, key) in woTypeMap" :key="key" :label="key">
                  {{ label }}
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 二级分类选择（维护/检测/安装/维修四类显示） -->
        <template v-if="['repair', 'maintenance', 'inspection', 'installation'].includes(formData.wo_type)">
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="二级分类">
                <el-select v-model="formData.wo_sub_type" placeholder="选择二级分类" @change="onSubTypeChange" style="width: 100%">
                  <el-option v-for="s in subTypeList" :key="s.sub_type_code" :label="s.sub_type_name" :value="s.sub_type_code" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- ==================== 网络类字段（网络维修/维护/检测/安装通用） ==================== -->
        <template v-if="deviceCategory === 'network'">
          <el-divider content-position="left">网络信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="IP地址">
                <el-input :model-value="getDynamicField('ip_address')" @update:model-value="val => setDynamicField('ip_address', val)" placeholder="IP地址" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="管理账号">
                <el-input :model-value="getDynamicField('manage_account')" @update:model-value="val => setDynamicField('manage_account', val)" placeholder="管理账号" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="管理密码">
                <el-input :model-value="getDynamicField('manage_password')" @update:model-value="val => setDynamicField('manage_password', val)" placeholder="管理密码" show-password />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="设备品牌">
                <el-input v-model="formData.device_brand" placeholder="品牌（选填）" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="设备型号">
                <el-input v-model="formData.device_model" placeholder="型号（选填）" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- ==================== 电脑类字段（电脑维修/维护/检测/安装通用） ==================== -->
        <template v-if="deviceCategory === 'computer'">
          <el-divider content-position="left">电脑信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="设备类型">
                <el-select v-model="formData.device_type" placeholder="选择类型" style="width: 100%">
                  <el-option label="笔记本" value="笔记本" />
                  <el-option label="台式机" value="台式机" />
                  <el-option label="一体机" value="一体机" />
                  <el-option label="服务器" value="服务器" />
                  <el-option label="其他" value="其他" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="品牌">
                <el-input v-model="formData.device_brand" placeholder="品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="型号">
                <el-input v-model="formData.device_model" placeholder="型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="登录账号">
                <el-input :model-value="getDynamicField('login_account')" @update:model-value="val => setDynamicField('login_account', val)" placeholder="设备登录账号" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="登录密码">
                <el-input :model-value="getDynamicField('login_password')" @update:model-value="val => setDynamicField('login_password', val)" placeholder="登录密码" show-password />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- ==================== 监控类字段（监控维修/维护/检测/安装通用） ==================== -->
        <template v-if="deviceCategory === 'monitor'">
          <el-divider content-position="left">监控信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="监控品牌">
                <el-select v-model="formData.monitor_brand" placeholder="选择品牌" style="width: 100%">
                  <el-option label="海康威视" value="海康威视" />
                  <el-option label="大华" value="大华" />
                  <el-option label="宇视" value="宇视" />
                  <el-option label="其他" value="其他" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="摄像头数量">
                <el-input-number v-model="formData.camera_count" :min="0" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8" v-if="formData.wo_sub_type && formData.wo_sub_type.startsWith('repair')">
              <el-form-item label="维修数量">
                <el-input-number v-model="formData.repair_camera_count" :min="0" style="width: 100%" placeholder="需维修的监控数量" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="NVR型号">
                <el-input v-model="formData.nvr_model" placeholder="NVR型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="通道号">
                <el-input v-model="formData.channel_no" placeholder="通道号" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="硬盘容量">
                <el-input v-model="formData.disk_capacity" placeholder="硬盘容量" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="录像状态">
                <el-input v-model="formData.recording_status" placeholder="录像状态" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="安装位置">
                <el-input v-model="formData.camera_location" placeholder="安装位置" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="管理账号">
                <el-input :model-value="getDynamicField('manage_account')" @update:model-value="val => setDynamicField('manage_account', val)" placeholder="管理账号" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="管理密码">
                <el-input :model-value="getDynamicField('manage_password')" @update:model-value="val => setDynamicField('manage_password', val)" placeholder="管理密码" show-password />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- ==================== 打印类字段（打印维修/维护/检测/安装通用） ==================== -->
        <template v-if="deviceCategory === 'printer'">
          <el-divider content-position="left">打印设备信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="设备品牌">
                <el-input v-model="formData.device_brand" placeholder="品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="设备型号">
                <el-input v-model="formData.device_model" placeholder="型号" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="序列号">
                <el-input v-model="formData.device_sn" placeholder="序列号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="硒鼓型号">
                <el-input v-model="formData.toner_model" placeholder="硒鼓型号" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="感光鼓型号">
                <el-input v-model="formData.drum_model" placeholder="感光鼓型号" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- ==================== 其他办公设备字段 ==================== -->
        <template v-if="deviceCategory === 'other'">
          <el-divider content-position="left">设备信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="设备类型">
                <el-input v-model="formData.device_type" placeholder="设备类型" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="品牌">
                <el-input v-model="formData.device_brand" placeholder="品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="型号">
                <el-input v-model="formData.device_model" placeholder="型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="序列号">
                <el-input v-model="formData.device_sn" placeholder="序列号" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- ==================== 送货服务专属字段 ==================== -->
        <template v-if="formData.wo_type === 'delivery'">
          <el-divider content-position="left">配送信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="配送地址">
                <el-input v-model="formData.delivery_address" placeholder="配送地址" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="安装位置">
                <el-input v-model="formData.install_position" placeholder="安装位置" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="到货时间">
                <el-date-picker v-model="formData.arrival_time" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="货物数量">
                <el-input-number v-model="formData.goods_quantity" :min="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="楼层类型">
                <el-select v-model="formData.goods_floor_type" style="width: 100%">
                  <el-option label="有电梯" value="有电梯" />
                  <el-option label="无电梯" value="无电梯" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="安装材料">
                <el-input v-model="formData.install_material" type="textarea" :rows="2" placeholder="安装材料" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-divider content-position="left">配送产品清单</el-divider>
          <el-button type="primary" size="small" :icon="Plus" @click="addDeliveryProduct" style="margin-bottom: 10px;">添加配送产品</el-button>
          <el-table :data="formData.delivery_products || []" border size="small" v-if="formData.delivery_products && formData.delivery_products.length > 0">
            <el-table-column label="产品名称" min-width="150">
              <template #default="{ row }">
                <el-input v-model="row.product_name" placeholder="产品名称" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="规格" width="120">
              <template #default="{ row }">
                <el-input v-model="row.specification" placeholder="规格" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="数量" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="单价" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" controls-position="right" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="小计" width="100" align="right">
              <template #default="{ row }">
                <span>¥{{ ((row.quantity || 0) * (row.unit_price || 0)).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" align="center">
              <template #default="{ row, $index }">
                <el-button type="primary" link size="small" @click="openDeliveryProductSelector($index)">从商品库选择</el-button>
                <el-button type="danger" link size="small" @click="formData.delivery_products.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无配送产品" :image-size="40" />
        </template>

        <!-- ==================== 产品代购专属字段 ==================== -->
        <template v-if="formData.wo_type === 'purchase'">
          <el-divider content-position="left">代购信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="代购产品">
                <el-input v-model="formData.purchase_product" placeholder="产品名称" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="品牌">
                <el-input v-model="formData.purchase_brand" placeholder="品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="规格">
                <el-input v-model="formData.purchase_spec" placeholder="规格" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="数量">
                <el-input-number v-model="formData.purchase_qty" :min="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="预期到货">
                <el-date-picker v-model="formData.expected_arrival_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="采购价">
                <el-input-number v-model="formData.purchase_price" :min="0" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="代购服务费">
                <el-input-number v-model="formData.service_fee" :min="0" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="客户需求">
                <el-input v-model="formData.customer_demand" type="textarea" :rows="3" placeholder="客户需求描述" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- ==================== 现场勘察专属字段 ==================== -->
        <template v-if="formData.wo_type === 'survey'">
          <el-divider content-position="left">勘察信息</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="勘察地址">
                <el-input v-model="formData.survey_address" placeholder="勘察地址" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="预估工期">
                <el-input v-model="formData.estimated_duration" placeholder="预估工期" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="预估费用">
                <el-input-number v-model="formData.estimated_cost" :min="0" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="现场环境">
                <el-input v-model="formData.site_environment" type="textarea" :rows="2" placeholder="现场环境描述" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="设备现状">
                <el-input v-model="formData.device_status_desc" type="textarea" :rows="2" placeholder="设备现状描述" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="问题汇总">
                <el-input v-model="formData.problem_summary" type="textarea" :rows="2" placeholder="问题汇总" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="施工方案">
                <el-input v-model="formData.construction_plan" type="textarea" :rows="2" placeholder="施工方案" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- ==================== 通用区域（所有类型） ==================== -->
        <el-divider content-position="left">其他信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="优先级">
              <el-select v-model="formData.priority" placeholder="选择优先级" style="width: 100%">
                <el-option label="普通" :value="0" />
                <el-option label="紧急" :value="1" />
                <el-option label="特急" :value="2" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="预计完成时间">
              <el-date-picker v-model="formData.expected_finish_time" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="故障描述/需求描述">
              <el-input v-model="formData.fault_desc" type="textarea" :rows="3" placeholder="详细描述故障现象或需求" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="备注信息" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- ==================== 配件/材料区域（非配送服务类型显示） ==================== -->
        <template v-if="formData.wo_type !== 'delivery'">
          <el-divider content-position="left">配件/材料</el-divider>
          <el-button type="primary" size="small" :icon="Plus" @click="addFormPart" style="margin-bottom: 10px;">添加配件</el-button>
          <el-table :data="formData.parts" border size="small" v-if="formData.parts && formData.parts.length > 0">
            <el-table-column label="商品名称" min-width="150">
              <template #default="{ row }">
                <el-input v-model="row.part_name" placeholder="配件名称" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="规格" width="120">
              <template #default="{ row }">
                <el-input v-model="row.specification" placeholder="规格" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="数量" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="单价" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" controls-position="right" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="小计" width="100" align="right">
              <template #default="{ row }">
                <span>¥{{ ((row.quantity || 0) * (row.unit_price || 0)).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" align="center">
              <template #default="{ row, $index }">
                <el-button type="primary" link size="small" @click="openProductSelector($index)">从商品库选择</el-button>
                <el-button type="danger" link size="small" @click="formData.parts.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无配件" :image-size="40" />
        </template>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 6. 详情对话框（1050px） ==================== -->
    <el-dialog v-model="detailDialogVisible" title="工单详情" width="1200px" destroy-on-close top="2vh">
      <div v-loading="detailLoading" class="detail-layout">
        <!-- 左侧主内容区 -->
        <div class="detail-main" style="flex: 1; max-height: 65vh; overflow-y: auto; padding-right: 15px;">
          <!-- ==================== 流程引导卡片 ==================== -->
          <div class="workflow-guide-card">
            <div class="guide-header">
              <div class="stage-indicator">
                <el-tag :type="getStatusTagType(detailData.status)" size="large" effect="dark">
                  {{ statusMap[detailData.status] || '未知状态' }}
                </el-tag>
                <span class="stage-name">{{ stageGuide[detailData.status]?.title || '' }}</span>
              </div>
              <div class="guide-desc">{{ stageGuide[detailData.status]?.desc || '' }}</div>
            </div>
            
            <!-- 核心阶段进度条 -->
            <div class="stage-progress">
              <div v-for="(name, idx) in stageNames" :key="idx" 
                   class="stage-item" 
                   :class="{ active: stageMap[detailData.status] === idx, done: stageMap[detailData.status] > idx }">
                <div class="stage-dot">{{ idx + 1 }}</div>
                <div class="stage-label">{{ name }}</div>
              </div>
            </div>
            
            <!-- 下一步操作提示 -->
            <div class="next-action-hint" v-if="stageGuide[detailData.status]?.nextAction">
              <el-icon><InfoFilled /></el-icon>
              <span>下一步：{{ stageGuide[detailData.status]?.nextAction }} - {{ stageGuide[detailData.status]?.nextDesc }}</span>
            </div>
          </div>

          <!-- 基本信息 -->
        <el-divider content-position="left">基本信息</el-divider>
        <el-descriptions :column="2" border size="default">
          <el-descriptions-item label="工单编号">{{ detailData.wo_no }}</el-descriptions-item>
          <el-descriptions-item label="工单类型">{{ woTypeMap[detailData.wo_type] || detailData.wo_type }}</el-descriptions-item>
          <el-descriptions-item label="二级分类" v-if="detailData.sub_type_name">{{ detailData.sub_type_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(detailData.status)">{{ statusMap[detailData.status] || '未知' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级">{{ priorityMap[detailData.priority] || detailData.priority || '-' }}</el-descriptions-item>
          <el-descriptions-item label="客户名称">{{ detailData.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detailData.customer_phone }}</el-descriptions-item>
          <el-descriptions-item label="客户单位">{{ detailData.customer_company || '-' }}</el-descriptions-item>
          <el-descriptions-item label="办公室">{{ detailData.customer_office || '-' }}</el-descriptions-item>
          <el-descriptions-item label="详细地址" :span="2">{{ detailData.customer_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="接待员工">{{ detailData.reception_user_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="接单方式">{{ orderSourceMap[detailData.order_source] || '-' }}</el-descriptions-item>
          <el-descriptions-item label="处理方式">{{ serviceTypeMap[detailData.service_type] || '-' }}</el-descriptions-item>
          <el-descriptions-item label="工程师">{{ detailData.assigned_user_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detailData.created_at }}</el-descriptions-item>
          <el-descriptions-item label="预计完成时间">{{ detailData.expected_finish_time || '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 专属字段信息（根据类型显示） -->
        <!-- 网络类详情 -->
        <template v-if="detailData.device_category === 'network'">
          <el-divider content-position="left">网络信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="IP地址">{{ getDetailDynamicField('ip_address') }}</el-descriptions-item>
            <el-descriptions-item label="管理账号">{{ getDetailDynamicField('manage_account') }}</el-descriptions-item>
            <el-descriptions-item label="管理密码">{{ getDetailDynamicField('manage_password') }}</el-descriptions-item>
            <el-descriptions-item label="设备品牌">{{ detailData.device_brand || '-' }}</el-descriptions-item>
            <el-descriptions-item label="设备型号">{{ detailData.device_model || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- 电脑类详情 -->
        <template v-if="detailData.device_category === 'computer'">
          <el-divider content-position="left">电脑信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="设备类型">{{ detailData.device_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="品牌">{{ detailData.device_brand || '-' }}</el-descriptions-item>
            <el-descriptions-item label="型号">{{ detailData.device_model || '-' }}</el-descriptions-item>
            <el-descriptions-item label="序列号">{{ detailData.device_sn || '-' }}</el-descriptions-item>
            <el-descriptions-item label="登录账号">{{ getDetailDynamicField('login_account') }}</el-descriptions-item>
            <el-descriptions-item label="登录密码">{{ getDetailDynamicField('login_password') }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- 监控类详情 -->
        <template v-if="detailData.device_category === 'monitor'">
          <el-divider content-position="left">监控信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="监控品牌">{{ detailData.monitor_brand || '-' }}</el-descriptions-item>
            <el-descriptions-item label="摄像头数量">{{ detailData.camera_count || '-' }}</el-descriptions-item>
            <el-descriptions-item label="维修数量" v-if="detailData.wo_sub_type && detailData.wo_sub_type.startsWith('repair')">{{ detailData.repair_camera_count || '-' }}</el-descriptions-item>
            <el-descriptions-item label="NVR型号">{{ detailData.nvr_model || '-' }}</el-descriptions-item>
            <el-descriptions-item label="通道号">{{ detailData.channel_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="硬盘容量">{{ detailData.disk_capacity || '-' }}</el-descriptions-item>
            <el-descriptions-item label="录像状态">{{ detailData.recording_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="安装位置">{{ detailData.camera_location || '-' }}</el-descriptions-item>
            <el-descriptions-item label="管理账号">{{ getDetailDynamicField('manage_account') }}</el-descriptions-item>
            <el-descriptions-item label="管理密码">{{ getDetailDynamicField('manage_password') }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- 打印类详情 -->
        <template v-if="detailData.device_category === 'printer'">
          <el-divider content-position="left">打印设备信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="品牌">{{ detailData.device_brand || '-' }}</el-descriptions-item>
            <el-descriptions-item label="型号">{{ detailData.device_model || '-' }}</el-descriptions-item>
            <el-descriptions-item label="序列号">{{ detailData.device_sn || '-' }}</el-descriptions-item>
            <el-descriptions-item label="硒鼓型号">{{ detailData.toner_model || '-' }}</el-descriptions-item>
            <el-descriptions-item label="感光鼓型号">{{ detailData.drum_model || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- 其他办公设备详情 -->
        <template v-if="detailData.device_category === 'other'">
          <el-divider content-position="left">设备信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="设备类型">{{ detailData.device_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="品牌">{{ detailData.device_brand || '-' }}</el-descriptions-item>
            <el-descriptions-item label="型号">{{ detailData.device_model || '-' }}</el-descriptions-item>
            <el-descriptions-item label="序列号">{{ detailData.device_sn || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- 送货服务详情 -->
        <template v-if="detailData.wo_type === 'delivery'">
          <el-divider content-position="left">配送信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="配送地址">{{ detailData.delivery_address || '-' }}</el-descriptions-item>
            <el-descriptions-item label="安装位置">{{ detailData.install_position || '-' }}</el-descriptions-item>
            <el-descriptions-item label="到货时间">{{ detailData.arrival_time || '-' }}</el-descriptions-item>
            <el-descriptions-item label="货物数量">{{ detailData.goods_quantity || '-' }}</el-descriptions-item>
            <el-descriptions-item label="楼层类型">{{ detailData.goods_floor_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="安装材料" :span="2">{{ detailData.install_material || '-' }}</el-descriptions-item>
          </el-descriptions>
          <!-- 配送产品清单 -->
          <template v-if="detailData.delivery_products && detailData.delivery_products.length > 0">
            <el-divider content-position="left">配送产品清单</el-divider>
            <el-table :data="detailData.delivery_products" size="small" border>
              <el-table-column type="index" label="序号" width="60" align="center" />
              <el-table-column prop="product_name" label="产品名称" min-width="150" />
              <el-table-column prop="specification" label="规格" width="120" />
              <el-table-column prop="quantity" label="数量" width="80" align="center" />
            </el-table>
          </template>
        </template>

        <!-- 代购详情 -->
        <template v-if="detailData.wo_type === 'purchase'">
          <el-divider content-position="left">代购信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="代购产品名称">{{ detailData.purchase_product_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="品牌">{{ detailData.purchase_brand || '-' }}</el-descriptions-item>
            <el-descriptions-item label="规格">{{ detailData.purchase_spec || '-' }}</el-descriptions-item>
            <el-descriptions-item label="数量">{{ detailData.purchase_quantity || '-' }}</el-descriptions-item>
            <el-descriptions-item label="预期到货时间">{{ detailData.expected_arrival || '-' }}</el-descriptions-item>
            <el-descriptions-item label="采购价">{{ detailData.purchase_price != null ? '¥' + Number(detailData.purchase_price).toFixed(2) : '-' }}</el-descriptions-item>
            <el-descriptions-item label="代购服务费">{{ detailData.service_fee != null ? '¥' + Number(detailData.service_fee).toFixed(2) : '-' }}</el-descriptions-item>
            <el-descriptions-item label="客户需求" :span="2">{{ detailData.customer_requirement || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- 勘察详情 -->
        <template v-if="detailData.wo_type === 'survey'">
          <el-divider content-position="left">勘察信息</el-divider>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="勘察地址">{{ detailData.survey_address || '-' }}</el-descriptions-item>
            <el-descriptions-item label="预估工期">{{ detailData.estimated_duration || '-' }}</el-descriptions-item>
            <el-descriptions-item label="预估费用">{{ detailData.estimated_cost != null ? '¥' + Number(detailData.estimated_cost).toFixed(2) : '-' }}</el-descriptions-item>
            <el-descriptions-item label="现场环境" :span="2">{{ detailData.site_environment || '-' }}</el-descriptions-item>
            <el-descriptions-item label="设备现状" :span="2">{{ detailData.device_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="问题汇总" :span="2">{{ detailData.problem_summary || '-' }}</el-descriptions-item>
            <el-descriptions-item label="施工方案" :span="2">{{ detailData.construction_plan || '-' }}</el-descriptions-item>
            <el-descriptions-item label="所需设备配件" :span="2">{{ detailData.required_parts || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- 配件明细 -->
        <el-divider content-position="left">配件明细</el-divider>
        <el-table :data="detailData.parts || []" size="small" border v-if="detailData.parts && detailData.parts.length > 0">
          <el-table-column type="index" label="#" width="50" align="center" />
          <el-table-column prop="product_name" label="商品名称" min-width="120" />
          <el-table-column prop="specification" label="规格" width="100" />
          <el-table-column prop="quantity" label="数量" width="80" align="center" />
          <el-table-column prop="unit_price" label="单价" width="100" align="right">
            <template #default="{ row }">¥{{ Number(row.unit_price || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="小计" width="100" align="right">
            <template #default="{ row }">¥{{ (Number(row.quantity || 0) * Number(row.unit_price || 0)).toFixed(2) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无配件" :image-size="40" />

        <!-- 费用信息 -->
        <el-divider content-position="left">费用信息</el-divider>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="人工费">{{ detailData.labor_cost != null ? '¥' + Number(detailData.labor_cost).toFixed(2) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="配件材料费">{{ detailData.parts_cost != null ? '¥' + Number(detailData.parts_cost).toFixed(2) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="其他费用">{{ detailData.other_cost != null ? '¥' + Number(detailData.other_cost).toFixed(2) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="总费用">
            <span style="color: #f56c6c; font-weight: bold;">
              {{ detailData.total_cost != null ? '¥' + Number(detailData.total_cost).toFixed(2) : '-' }}
            </span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 报价明细 -->
        <el-divider content-position="left">报价明细</el-divider>
        <el-table :data="detailData.quote_items || []" size="small" border v-if="detailData.quote_items && detailData.quote_items.length > 0">
          <el-table-column type="index" label="序号" width="60" align="center" />
          <el-table-column prop="product_name" label="配件名称" min-width="150" />
          <el-table-column prop="spec" label="规格" width="120" />
          <el-table-column prop="unit" label="单位" width="80" />
          <el-table-column prop="quantity" label="数量" width="80" align="center" />
          <el-table-column prop="unit_price" label="单价" width="100" align="right">
            <template #default="{ row }">¥{{ Number(row.unit_price || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="subtotal" label="小计" width="100" align="right">
            <template #default="{ row }">¥{{ Number(row.subtotal || 0).toFixed(2) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无报价明细" :image-size="40" />

        <!-- 关联单据 -->
        <el-divider content-position="left">关联单据</el-divider>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="接件单号">
            <el-link v-if="detailData.receive_order_no" type="primary">{{ detailData.receive_order_no }}</el-link>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="报价单号">
            <el-link v-if="detailData.quote_no" type="primary">{{ detailData.quote_no }}</el-link>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="采购单号">
            <el-link v-if="detailData.purchase_no" type="primary">{{ detailData.purchase_no }}</el-link>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="销售单号">
            <el-link v-if="detailData.sales_no" type="primary">{{ detailData.sales_no }}</el-link>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="财务记录ID">
            <el-link v-if="detailData.finance_record_id" type="primary">{{ detailData.finance_record_id }}</el-link>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>

        </div>

        <!-- 右侧操作日志区 -->
        <div v-if="detailData.logs && detailData.logs.length > 0" class="detail-sidebar" style="width: 280px; max-height: 65vh; overflow-y: auto; padding-left: 15px; border-left: 1px solid #e4e7ed;">
          <div style="font-weight: bold; font-size: 14px; margin-bottom: 15px; color: #303133;">操作日志</div>
          <el-timeline>
            <el-timeline-item
              v-for="log in detailData.logs"
              :key="log.id"
              :timestamp="log.created_at"
              placement="top"
            >
              <el-card shadow="never" :body-style="{ padding: '10px' }">
                <p style="margin: 0; font-weight: bold;">{{ log.action }}</p>
                <p style="margin: 4px 0 0; color: #606266;">{{ log.content }}</p>
                <p style="margin: 4px 0 0; font-size: 12px; color: #909399;">操作人：{{ log.operator_name || '-' }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>

      <!-- 详情底部操作按钮区 -->
      <template #footer>
        <div class="detail-footer">
          <!-- 左侧：核心操作按钮 -->
          <div class="primary-actions">
            <template v-for="(btn, idx) in primaryActions[detailData.status] || []" :key="idx">
              <el-button :type="btn.type" @click="handlePrimaryAction(btn.action, detailData)">
                {{ btn.label }}
              </el-button>
            </template>
          </div>
          
          <!-- 中间：更多操作下拉 -->
          <div class="more-actions" v-if="(moreActions[detailData.status] || []).length > 0">
            <el-dropdown trigger="click">
              <el-button type="info" link>
                更多操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-for="(item, idx) in moreActions[detailData.status] || []" :key="idx" @click="handleMoreAction(item.action, detailData)">
                    {{ item.label }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          
          <!-- 右侧：通用操作 -->
          <div class="common-actions">
            <el-button type="primary" link @click="handlePrint(detailData)">
              <el-icon><Printer /></el-icon> 打印
            </el-button>
            <el-button @click="detailDialogVisible = false">关闭</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- ==================== 7. 派单对话框 ==================== -->
    <el-dialog v-model="dispatchDialogVisible" title="派单" width="550px" destroy-on-close>
      <el-form :model="dispatchForm" label-width="100px">
        <el-form-item label="派单方式">
          <el-radio-group v-model="dispatchForm.dispatch_type" @change="onDispatchTypeChange">
            <el-radio :label="'manual'">手动派单</el-radio>
            <el-radio :label="'auto'">自动派单</el-radio>
          </el-radio-group>
        </el-form-item>
        <!-- 手动派单 -->
        <template v-if="dispatchForm.dispatch_type === 'manual'">
          <el-form-item label="选择工程师" required>
            <el-select v-model="dispatchForm.assigned_user_id" placeholder="选择工程师" filterable style="width: 100%">
              <el-option v-for="u in userList" :key="u.id" :label="u.real_name || u.username" :value="u.id" />
            </el-select>
          </el-form-item>
        </template>
        <!-- 自动派单推荐 -->
        <template v-if="dispatchForm.dispatch_type === 'auto'">
          <el-form-item label="推荐工程师">
            <div v-loading="autoDispatchLoading">
              <el-table :data="autoDispatchList" size="small" border v-if="autoDispatchList.length > 0">
                <el-table-column prop="staff_name" label="工程师" width="100" />
                <el-table-column prop="today_count" label="当前工单数" width="100" align="center" />
                <el-table-column prop="score" label="推荐分数" width="100" align="center" />
                <el-table-column label="操作" width="80" align="center">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="dispatchForm.assigned_user_id = row.user_id">选择</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-else description="暂无推荐" :image-size="40" />
            </div>
          </el-form-item>
        </template>
        <el-form-item label="备注">
          <el-input v-model="dispatchForm.remark" type="textarea" :rows="2" placeholder="派单备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dispatchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDispatch" :loading="submitLoading">确认派单</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 8. 领用配件对话框 ==================== -->
    <el-dialog v-model="allocatePartsDialogVisible" title="领用配件" width="750px" destroy-on-close>
      <div style="margin-bottom: 10px; display: flex; gap: 10px;">
        <el-button type="primary" size="small" :icon="Plus" @click="addAllocatePart">添加配件</el-button>
        <el-button type="success" size="small" :icon="Refresh" @click="syncCustomerParts" :loading="syncPartsLoading">同步客户需求配件</el-button>
      </div>
      <el-table :data="allocatePartsList" border size="small">
        <el-table-column label="选择商品" width="90" align="center">
          <template #default="{ row, $index }">
            <el-button type="primary" link size="small" @click="openAllocateProductSelector($index)">选择</el-button>
          </template>
        </el-table-column>
        <el-table-column label="商品名称" min-width="120">
          <template #default="{ row }">
            <span>{{ row.product_name || row.part_name || '请选择商品' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="规格" width="100">
          <template #default="{ row }">
            <span>{{ row.specification || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="{ row }">
            <el-input-number v-model="row.quantity" :min="1" :max="row.stock || 9999" size="small" controls-position="right" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="库存" width="80" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.stock > 0 ? '#67c23a' : '#f56c6c' }">{{ row.stock ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.from_customer" type="warning" size="small">需求</el-tag>
            <el-tag v-else type="info" size="small">手动</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="60" align="center">
          <template #default="{ $index }">
            <el-button type="danger" link size="small" @click="allocatePartsList.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="allocatePartsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAllocateParts" :loading="submitLoading">确认领用</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 9. 完工对话框 ==================== -->
    <el-dialog v-model="finishDialogVisible" title="完工提交" width="550px" destroy-on-close>
      <el-form :model="finishForm" label-width="100px">
        <el-form-item label="完工报告">
          <el-input v-model="finishForm.report" type="textarea" :rows="4" placeholder="完工报告" />
        </el-form-item>
        <el-form-item label="测试结果">
          <el-radio-group v-model="finishForm.test_result">
            <el-radio :label="'pass'">通过</el-radio>
            <el-radio :label="'fail'">未通过</el-radio>
            <el-radio :label="'partial'">部分通过</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="测试备注">
          <el-input v-model="finishForm.test_remark" type="textarea" :rows="2" placeholder="测试备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="finishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFinish" :loading="submitLoading">确认完工</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 10. 结算对话框 ==================== -->
    <el-dialog v-model="settleDialogVisible" title="工单结算" width="750px" destroy-on-close>
      <el-form :model="settleForm" label-width="110px">
        <el-form-item label="工时（小时）">
          <el-input-number v-model="settleForm.labor_hours" :min="0" :precision="1" controls-position="right" style="width: 200px" @change="onLaborCalcChange" />
        </el-form-item>
        <el-form-item label="人工费单价">
          <el-input-number v-model="settleForm.labor_unit_price" :min="0" :precision="2" controls-position="right" style="width: 200px" @change="onLaborCalcChange" />
        </el-form-item>
        <el-form-item label="人工费">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-weight: bold; color: #409eff;">¥{{ calcLaborCost }}</span>
            <span style="color: #909399; font-size: 12px;">（工时×单价自动计算）</span>
          </div>
        </el-form-item>
        <el-form-item label="或直接输入人工费">
          <el-input-number v-model="settleForm.labor_cost_direct" :min="0" :precision="2" controls-position="right" style="width: 200px" placeholder="直接输入则覆盖上方计算" @change="onLaborDirectChange" />
        </el-form-item>

        <el-divider content-position="left">配件材料费（关联领用记录）</el-divider>
        <el-table :data="settlePartsList" border size="small" style="margin-bottom: 10px;" v-if="settlePartsList.length > 0">
          <el-table-column label="商品名称" min-width="120">
            <template #default="{ row }">
              <span>{{ row.product_name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="规格" width="100">
            <template #default="{ row }">
              <span>{{ row.specification || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="领用数量" width="80" align="center">
            <template #default="{ row }">
              <span>{{ row.quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column label="实际使用数量" width="120" align="center">
            <template #default="{ row }">
              <el-input-number v-model="row.used_quantity" :min="0" :max="row.quantity" size="small" controls-position="right" style="width: 100%" @change="calcSettlePartsCost" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="80" align="right">
            <template #default="{ row }">
              <span>{{ row.unit_price }}</span>
            </template>
          </el-table-column>
          <el-table-column label="小计" width="80" align="right">
            <template #default="{ row }">
              <span>{{ (row.used_quantity * row.unit_price).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="退回未使用" width="100" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.return_unused" @change="onReturnChange(row)" />
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无领用配件记录" :image-size="40" />

        <el-form-item label="配件材料费" style="margin-top: 10px;">
          <span style="font-weight: bold; color: #409eff;">¥{{ settleForm.parts_cost.toFixed(2) }}</span>
          <span style="color: #909399; font-size: 12px; margin-left: 5px;">（根据上方配件清单自动计算）</span>
        </el-form-item>
        <el-form-item label="其他费用">
          <el-input-number v-model="settleForm.other_cost" :min="0" :precision="2" controls-position="right" style="width: 200px" />
        </el-form-item>
        <el-form-item label="总费用">
          <span style="font-weight: bold; font-size: 18px; color: #f56c6c;">¥{{ calcTotalCost }}</span>
        </el-form-item>
        <el-form-item label="结算方式">
          <el-radio-group v-model="settleForm.settle_type" @change="onSettleTypeChange">
            <el-radio-button label="cash">现金结算</el-radio-button>
            <el-radio-button label="credit">签单挂账</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="结算账户" v-if="settleForm.settle_type === 'cash'">
          <el-select v-model="settleForm.account_id" placeholder="选择结算账户" style="width: 100%">
            <el-option v-for="a in accountList" :key="a.id" :label="a.account_name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="签单说明" v-if="settleForm.settle_type === 'credit'">
          <el-input v-model="settleForm.credit_remark" type="textarea" :rows="2" placeholder="签单挂账说明（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="settleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitSettle" :loading="submitLoading">确认结算</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 11. 客户验收对话框 ==================== -->
    <el-dialog v-model="acceptanceDialogVisible" title="客户验收" width="550px" destroy-on-close>
      <el-form :model="acceptanceForm" label-width="100px">
        <el-form-item label="验收结果">
          <el-radio-group v-model="acceptanceForm.result">
            <el-radio-button label="1">验收通过</el-radio-button>
            <el-radio-button label="2">验收不通过</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="验收备注">
          <el-input v-model="acceptanceForm.remark" type="textarea" :rows="3" placeholder="验收备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="acceptanceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAcceptance" :loading="submitLoading">确认验收</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 12. 上门送回对话框 ==================== -->
    <el-dialog v-model="returnVisitDialogVisible" title="上门送回" width="550px" destroy-on-close>
      <el-form :model="returnVisitForm" label-width="100px">
        <el-form-item label="上门时间">
          <el-date-picker v-model="returnVisitForm.visit_time" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="送回结果">
          <el-input v-model="returnVisitForm.result" type="textarea" :rows="3" placeholder="送回结果描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnVisitDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReturnVisit" :loading="submitLoading">确认送回</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 13. 转报价/转采购/转销售 确认对话框 ==================== -->
    <el-dialog v-model="convertDialogVisible" :title="convertDialogTitle" width="450px" destroy-on-close>
      <el-alert :title="convertDialogMsg" type="warning" :closable="false" show-icon style="margin-bottom: 16px;" />
      <template #footer>
        <el-button @click="convertDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitConvert" :loading="submitLoading">确认转换</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 14. 商品选择对话框（配件） ==================== -->
    <el-dialog v-model="productSelectorVisible" title="选择商品" width="750px" append-to-body destroy-on-close>
      <el-input v-model="productKeyword" placeholder="搜索商品名称" clearable style="margin-bottom: 10px" @input="fetchProducts" />
      <el-table :data="productList" stripe border v-loading="productLoading" max-height="400">
        <el-table-column prop="product_code" label="编码" width="120" />
        <el-table-column prop="product_name" label="名称" min-width="150" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="unit_name" label="单位" width="70" />
        <el-table-column prop="sale_price" label="售价" width="100" align="right">
          <template #default="{ row }">¥{{ Number(row.sale_price || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="current_stock" label="库存" width="80" align="center" />
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="selectProduct(row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- ==================== 15. 工单报价对话框 ==================== -->
    <el-dialog v-model="quoteDialogVisible" title="工单报价" width="800px" destroy-on-close>
      <el-form :model="quoteForm" label-width="100px">
        <el-divider content-position="left">费用明细</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="人工费">
              <el-input-number v-model="quoteForm.labor_cost" :min="0" :precision="2" style="width: 100%" @change="calcQuoteTotal" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="配件材料费">
              <el-input-number v-model="quoteForm.parts_cost" :min="0" :precision="2" style="width: 100%" @change="calcQuoteTotal" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="其他费用">
              <el-input-number v-model="quoteForm.other_cost" :min="0" :precision="2" style="width: 100%" @change="calcQuoteTotal" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24" style="text-align: right; padding-right: 20px;">
            <span style="font-size: 16px; font-weight: bold;">报价总计：¥{{ quoteForm.total_cost.toFixed(2) }}</span>
          </el-col>
        </el-row>

        <el-divider content-position="left">配件清单</el-divider>
        <el-table :data="quoteForm.items" border size="small" style="width: 100%">
          <el-table-column label="配件选择" width="100" align="center">
            <template #default="{ $index }">
              <el-button type="primary" link size="small" @click="openQuoteProductSelector($index)">选择</el-button>
            </template>
          </el-table-column>
          <el-table-column label="配件名称" min-width="150">
            <template #default="{ row }">
              <el-input v-model="row.product_name" placeholder="配件名称" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="规格" width="120">
            <template #default="{ row }">
              <el-input v-model="row.spec" placeholder="规格" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="80">
            <template #default="{ row }">
              <el-input v-model="row.unit" placeholder="单位" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" @change="calcQuoteItemSubtotal(row)" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" controls-position="right" @change="calcQuoteItemSubtotal(row)" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="100" align="right">
            <template #default="{ row }">
              <span>¥{{ (row.subtotal || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="quoteForm.items.splice($index, 1)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button type="primary" link @click="addQuoteItem" style="margin-top: 10px;">
          <el-icon><Plus /></el-icon> 添加配件
        </el-button>

        <el-divider content-position="left">客户确认</el-divider>
        <el-form-item label="客户确认">
          <el-radio-group v-model="quoteForm.customer_confirm">
            <el-radio label="1">客户确认</el-radio>
            <el-radio label="2">客户拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="拒绝原因" v-if="quoteForm.customer_confirm === '2'">
          <el-input v-model="quoteForm.reject_reason" type="textarea" :rows="2" placeholder="请输入拒绝原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quoteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitQuote" :loading="submitLoading">提交报价</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 16. 报价配件选择对话框 ==================== -->
    <el-dialog v-model="quoteProductSelectorVisible" title="选择配件" width="750px" append-to-body destroy-on-close>
      <el-input v-model="quoteProductKeyword" placeholder="搜索配件名称" clearable style="margin-bottom: 10px" @input="fetchQuoteProducts" />
      <el-table :data="quoteProductList" stripe border v-loading="quoteProductLoading" max-height="400">
        <el-table-column prop="product_code" label="编码" width="120" />
        <el-table-column prop="product_name" label="名称" min-width="150" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="unit_name" label="单位" width="70" />
        <el-table-column prop="sale_price" label="售价" width="100" align="right">
          <template #default="{ row }">¥{{ Number(row.sale_price || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="current_stock" label="库存" width="80" align="center" />
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="selectQuoteProduct(row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- ==================== 打印对话框（通用组件） ==================== -->
    <PrintDialog
      v-model:visible="printDialogVisible"
      template-type="work_order"
      :print-data="printData"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download, Printer, InfoFilled, ArrowDown, Delete } from '@element-plus/icons-vue'
import request from '@/api/request'
import { useBatchOperations } from '@/composables/useBatchOperations'

// ==================== 常量定义 ====================

// 工单类型映射
const woTypeMap = {
  repair: '维修服务',
  maintenance: '维护服务',
  delivery: '送货服务',
  installation: '安装服务',
  inspection: '检测服务',
  purchase: '产品代购',
  survey: '现场勘察'
}

// 状态映射（8个核心状态）
const statusMap = {
  0: '待派单',
  1: '待接单',
  2: '待备件',
  3: '待上门',
  4: '处理中',
  5: '待结算',
  6: '已完成',
  7: '已取消'
}

// 优先级映射
const priorityMap = {
  normal: '普通',
  urgent: '紧急',
  critical: '特急'
}

// 状态tag颜色映射（8个核心状态）
const statusTagTypeMap = {
  0: 'info',       // 待派单 - 灰色
  1: 'warning',    // 待接单 - 黄色
  2: 'danger',     // 待备件 - 红色
  3: 'warning',    // 待上门 - 黄色
  4: 'primary',    // 处理中 - 蓝色
  5: 'danger',     // 待结算 - 红色
  6: 'success',    // 已完成 - 绿色
  7: 'info'        // 已取消 - 灰色
}

// 接单方式映射
const orderSourceMap = {
  'wechat': '微信',
  'phone': '电话',
  'other': '其他'
}

// 处理方式映射
const serviceTypeMap = {
  'onsite': '上门',
  'remote': '远程'
}

// 需要显示配件区域的工单类型
const partsEnabledTypes = ['repair', 'maintenance', 'delivery', 'installation', 'inspection', 'purchase', 'survey']

// ==================== 流程引导配置 ====================

// 核心阶段映射（8个状态对应5个阶段）
const stageMap = {
  0: 0,  // 待派单
  1: 0,  // 待接单
  2: 1,  // 待备件
  3: 1,  // 待上门
  4: 2,  // 处理中
  5: 3,  // 待结算
  6: 4,  // 已完成
  7: 4   // 已取消
}

// 阶段名称
const stageNames = ['待派单/接单', '待备件', '上门处理', '待结算', '已完成']

// 阶段引导文案（每个状态对应的引导信息）
const stageGuide = {
  0: { title: '待派单', desc: '工单已创建，等待派单', nextAction: '派单', nextDesc: '指派工程师处理此工单' },
  1: { title: '待接单', desc: '已指派工程师，等待接单', nextAction: '接单', nextDesc: '工程师确认接单' },
  2: { title: '待备件', desc: '备件未就绪，需采购或补领', nextAction: '领取备件', nextDesc: '领取所需备件' },
  3: { title: '待上门', desc: '备件已就绪，等待上门', nextAction: '上门处理', nextDesc: '携带备件上门服务' },
  4: { title: '处理中', desc: '正在维修处理', nextAction: '完工结算', nextDesc: '完成维修后提交结算' },
  5: { title: '待结算', desc: '维修完成，等待结算', nextAction: '结算', nextDesc: '完成费用结算' },
  6: { title: '已完成', desc: '工单已完成', nextAction: '', nextDesc: '' },
  7: { title: '已取消', desc: '工单已取消', nextAction: '', nextDesc: '' }
}

// 核心操作按钮（每个状态显示核心操作）
const primaryActions = {
  0: [{ label: '派单', type: 'warning', action: 'dispatch' }],
  1: [{ label: '接单', type: 'success', action: 'accept' }],
  2: [{ label: '领取备件', type: 'warning', action: 'allocateParts' }, { label: '跳过领料', type: 'info', action: 'skipAllocate' }],
  3: [{ label: '上门处理', type: 'primary', action: 'startProcess' }],
  4: [{ label: '完工结算', type: 'success', action: 'settle' }],
  5: [{ label: '结算', type: 'warning', action: 'settle' }],
  6: [],
  7: []
}

// 更多操作（低频操作）
const moreActions = {
  0: [{ label: '取消', action: 'cancel' }],
  1: [{ label: '取消', action: 'cancel' }],
  2: [{ label: '报价', action: 'quote' }, { label: '转采购', action: 'toPurchase' }, { label: '取消', action: 'cancel' }],
  3: [{ label: '带回维修', action: 'bringBack' }, { label: '取消', action: 'cancel' }],
  4: [{ label: '报价', action: 'quote' }, { label: '转采购', action: 'toPurchase' }, { label: '取消', action: 'cancel' }],
  5: [{ label: '取消', action: 'cancel' }],
  6: [],
  7: []
}

// ==================== 状态变量 ====================

const loading = ref(false)
const submitLoading = ref(false)
const detailLoading = ref(false)
const tableData = ref([])

// 员工列表、账户列表
const userList = ref([])
const accountList = ref([])

// 统计数据
const statusStats = ref({
  pending: 0, dispatched: 0, processing: 0,
  waiting_settle: 0, completed: 0, cancelled: 0, today: 0
})

// 搜索表单
const searchForm = reactive({
  keyword: '',
  wo_type: '',
  status: null,
  assigned_user_id: null,
  dateRange: null,
  min_amount: null,
  max_amount: null
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// ==================== 统计卡片 ====================

const statCards = computed(() => [
  { key: 'pending', label: '待派单', value: statusStats.value.pending || 0, colorClass: 'color-warning' },
  { key: 'dispatched', label: '已派单', value: statusStats.value.dispatched || 0, colorClass: 'color-warning' },
  { key: 'processing', label: '处理中', value: statusStats.value.processing || 0, colorClass: 'color-primary' },
  { key: 'waiting_settle', label: '待结算', value: statusStats.value.waiting_settle || 0, colorClass: 'color-danger' },
  { key: 'completed', label: '已完成', value: statusStats.value.completed || 0, colorClass: 'color-success' },
  { key: 'cancelled', label: '已取消', value: statusStats.value.cancelled || 0, colorClass: 'color-info' },
  { key: 'today', label: '今日新增', value: statusStats.value.today || 0, colorClass: 'color-default' }
])

// ==================== 工具函数 ====================

/** 获取状态tag类型 */
const getStatusTagType = (status) => statusTagTypeMap[status] || 'info'

/** 处理核心操作 */
const handlePrimaryAction = (action, row) => {
  switch (action) {
    case 'dispatch': openDispatchDialog(row); break
    case 'accept': handleAccept(row); break
    case 'allocateParts': openAllocatePartsDialog(row); break
    case 'skipAllocate': handleSkipAllocate(row); break
    case 'startProcess': handleStartProcess(row); break
    case 'quote': openQuoteDialog(row); break
    case 'finish': openFinishDialog(row); break
    case 'partsReady': handlePartsReady(row); break
    case 'approve': handleApprove(row); break
    case 'confirmStockIn': handleConfirmStockIn(row); break
    case 'settle': openSettleDialog(row); break
  }
}

/** 工程师接单 */
const handleAccept = async (row) => {
  try {
    await request.post(`/workorders/${row.id}/status`, {
      status: 2,
      content: '工程师确认接单'
    })
    ElMessage.success('接单成功')
    fetchData()
    detailDialogVisible.value = false
  } catch (error) {
    ElMessage.error('接单失败: ' + (error.message || error))
  }
}

/** 跳过领料（不需要配件时使用） */
const handleSkipAllocate = async (row) => {
  try {
    await ElMessageBox.confirm('确认不需要领取配件，直接进入下一步？', '跳过领料', {
      confirmButtonText: '确认跳过',
      cancelButtonText: '取消',
      type: 'info'
    })
    await request.post(`/workorders/${row.id}/status`, {
      status: 3,
      content: '无需领料，直接进入待上门状态'
    })
    ElMessage.success('已跳过领料')
    fetchData()
    if (detailDialogVisible.value) {
      await handleView({ id: row.id })
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败: ' + (error.message || error))
    }
  }
}

/** 处理更多操作 */
const handleMoreAction = (action, row) => {
  switch (action) {
    case 'cancel': handleCancel(row); break
    case 'allocateParts': openAllocatePartsDialog(row); break
    case 'quote': openQuoteDialog(row); break
    case 'bringBack': handleBringBack(row); break
    case 'toPurchase': handleToPurchase(row); break
  }
}

/** 获取步骤条当前激活步骤 */
const getStepActive = (status) => {
  // 已取消(10)特殊处理
  if (status === 10) return -1
  // 已完成(9)表示全部完成
  if (status === 9) return 10
  return status
}

// ==================== 数据获取 ====================

/** 获取工单列表 */
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword || undefined,
      wo_type: searchForm.wo_type || undefined,
      status: searchForm.status != null ? searchForm.status : undefined,
      assigned_user_id: searchForm.assigned_user_id || undefined,
      date_start: searchForm.dateRange?.[0] || undefined,
      date_end: searchForm.dateRange?.[1] || undefined,
      min_amount: searchForm.min_amount != null ? searchForm.min_amount : undefined,
      max_amount: searchForm.max_amount != null ? searchForm.max_amount : undefined
    }
    const res = await request.get('/workorders', { params })
    if (res.code === 200) {
      tableData.value = res.data.list || res.data.data || []
      pagination.total = res.data.total || 0
      // 从列表数据中统计各状态数量
      computeStatusStats()
    }
  } catch (error) {
    console.error('获取工单列表失败:', error)
  } finally {
    loading.value = false
  }
}

// ==================== 批量操作 ====================
const { selectedItems: selectedWorkorders, handleSelectionChange, handleBatchDelete } = useBatchOperations({
  deleteApi: async (ids) => {
    return request.post('/workorders/batch-delete', { ids })
  },
  refreshFn: fetchData,
  moduleName: '工单',
  beforeDelete: (items) => {
    // 检查是否有已完成的工单
    const completedItems = items.filter(item => item.status === 6)
    if (completedItems.length > 0) {
      return '选中的工单中包含已完成的工单，无法删除'
    }
    return true
  }
})

/** 从列表数据中计算各状态统计 */
const computeStatusStats = () => {
  const stats = { pending: 0, dispatched: 0, processing: 0, waiting_settle: 0, completed: 0, cancelled: 0, today: 0 }
  const today = new Date().toISOString().slice(0, 10)
  tableData.value.forEach(item => {
    switch (item.status) {
      case 0: stats.pending++; break      // 待派单
      case 1: stats.dispatched++; break   // 已派单
      case 2: stats.processing++; break   // 处理中
      case 3: stats.waiting_settle++; break  // 待结算
      case 4: stats.completed++; break    // 已完成
      case 5: stats.cancelled++; break    // 已取消
    }
    // 今日新增
    if (item.created_at && item.created_at.startsWith(today)) {
      stats.today++
    }
  })
  statusStats.value = stats
}

/** 获取员工列表 */
const fetchUsers = async () => {
  try {
    const res = await request.get('/users')
    if (res.code === 200) {
      userList.value = res.data.list || res.data || []
    }
  } catch (error) {
    console.error('获取员工列表失败:', error)
  }
}

/** 获取财务账户列表 */
const fetchAccounts = async () => {
  try {
    const res = await request.get('/finance/accounts')
    if (res.code === 200) {
      accountList.value = res.data.list || res.data || []
    }
  } catch (error) {
    console.error('获取账户列表失败:', error)
  }
}

/** 获取商品列表（配件选择用） */
const fetchProducts = async () => {
  productLoading.value = true
  try {
    const res = await request.get('/products', {
      params: { keyword: productKeyword.value, page: 1, page_size: 50 }
    })
    if (res.code === 200) {
      productList.value = res.data.list || res.data || []
    }
  } catch (error) {
    console.error('获取商品列表失败:', error)
  } finally {
    productLoading.value = false
  }
}

/** 搜索客户（autocomplete） */
const queryCustomerSuggestions = async (queryString, cb) => {
  if (!queryString || queryString.length < 1) {
    cb([])
    return
  }
  try {
    const res = await request.get('/customers', { params: { keyword: queryString, page_size: 10 } })
    if (res.code === 200) {
      const list = res.data.list || res.data || []
      cb(list.map(item => ({
        value: item.customer_name,
        id: item.id,
        customer_name: item.customer_name,
        phone: item.phone,
        company: item.company,
        address: item.address,
        office: item.office
      })))
    } else {
      cb([])
    }
  } catch (error) {
    cb([])
  }
}

// ==================== 搜索操作 ====================

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const resetSearch = () => {
  Object.assign(searchForm, {
    keyword: '',
    wo_type: '',
    status: null,
    assigned_user_id: null,
    dateRange: null,
    min_amount: null,
    max_amount: null
  })
  pagination.page = 1
  fetchData()
}

// ==================== 导出 ====================

const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.wo_type) params.append('wo_type', searchForm.wo_type)
  if (searchForm.status != null) params.append('status', searchForm.status)
  if (searchForm.assigned_user_id) params.append('assigned_user_id', searchForm.assigned_user_id)
  if (searchForm.dateRange?.[0]) params.append('date_start', searchForm.dateRange[0])
  if (searchForm.dateRange?.[1]) params.append('date_end', searchForm.dateRange[1])
  if (searchForm.min_amount != null) params.append('min_amount', searchForm.min_amount)
  if (searchForm.max_amount != null) params.append('max_amount', searchForm.max_amount)
  const token = localStorage.getItem('token') || ''
  window.open(`/api/workorders/export?${params.toString()}&token=${token}`, '_blank')
}

// ==================== 新建/编辑对话框 ====================

const formDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const currentOrderId = ref(null)

// 表单数据
const formData = reactive({
  // 客户信息
  customer_name: '',
  customer_phone: '',
  customer_company: '',
  customer_office: '',
  customer_address: '',
  // 员工信息
  reception_user_id: null,
  need_bring_back: 0,
  // 工单类型
  wo_type: '',
  wo_sub_type: '',
  // 通用字段
  priority: 0,
  expected_finish_time: '',
  fault_desc: '',
  remark: '',
  // network
  network_topology: '', fault_location: '', ip_address: '', device_port: '',
  line_type: '', check_items: '', speed_test_data: '', maintenance_cycle: '',
  restart_record: '', debug_content: '',
  // device
  device_type: '', device_brand: '', device_model: '', device_sn: '',
  device_password: '', device_config: '', system_version: '', error_code: '',
  repair_part: '', maintenance_items: '', replace_parts_list: '',
  retest_result: '', appearance_desc: '',
  // delivery
  delivery_address: '', install_position: '', arrival_time: '',
  device_quantity: 1, install_materials: '', product_spec: '',
  debug_items: '', acceptance_criteria: '', customer_confirm_items: '',
  // monitor_repair
  camera_count: 0, channel_no: '', nvr_model: '', disk_capacity: '',
  record_status: '', screen_fault: '', infrared_status: '',
  power_status: '', line_inspection: '', point_debug_record: '',
  // monitor_install
  install_points: '', camera_model: '', storage_config: '', cable_length: '',
  consumable_count: 0, clarity: '', debug_result: '', record_settings: '',
  // purchase
  purchase_product_name: '', purchase_brand: '', purchase_spec: '',
  purchase_quantity: 1, customer_requirement: '', expected_arrival: '',
  purchase_price: 0, service_fee: 0,
  // survey
  survey_address: '', site_environment: '', device_status: '',
  problem_summary: '', construction_plan: '', required_parts: '',
  estimated_duration: '', estimated_cost: 0,
  // own_install
  own_device_model: '', device_source: '', install_requirement: '',
  debug_items: '', consumable_usage: '', acceptance_criteria: '', customer_confirmation: '',
  // 配件
  parts: []
})

// 表单验证规则
const formRules = {
  wo_type: [{ required: true, message: '请选择工单类型', trigger: 'change' }],
  customer_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }]
}

/** 二级分类列表 */
const subTypeList = ref([])
/** 当前设备类别（根据二级分类自动判断） */
const deviceCategory = ref('')

/** 根据工单类型获取二级分类 */
const fetchSubTypes = async (parentType) => {
  if (!parentType || ['delivery', 'purchase', 'survey'].includes(parentType)) {
    subTypeList.value = []
    return
  }
  try {
    const res = await request.get('/workorders/subtypes', { params: { parent_type: parentType } })
    // res 已经是 response.data（即 {code:200, data:[...]}），不需要再取 res.data
    if (res && res.code === 200) {
      subTypeList.value = res.data || []
    }
  } catch (e) {
    subTypeList.value = []
  }
}

/** 工单类型变更 */
const onWoTypeChange = (val) => {
  formData.wo_sub_type = ''
  deviceCategory.value = ''
  dynamicFields.value = []
  formData.delivery_products = []
  formData.repair_camera_count = 0
  fetchSubTypes(val)
}

/** 二级分类变更 */
const onSubTypeChange = (val) => {
  const selected = subTypeList.value.find(s => s.sub_type_code === val)
  if (selected) {
    deviceCategory.value = selected.device_category || ''
  }
  // 切换二级分类时清空动态字段（不同类别有不同的动态字段）
  dynamicFields.value = []
}

/** 动态字段列表 */
const dynamicFields = ref([])

/** 获取动态字段值 */
const getDynamicField = (key) => {
  const field = dynamicFields.value.find(f => f.field_key === key)
  return field ? field.field_value : ''
}

/** 设置动态字段值 */
const setDynamicField = (key, value) => {
  const field = dynamicFields.value.find(f => f.field_key === key)
  if (field) {
    field.field_value = value
  } else {
    dynamicFields.value.push({ field_key: key, field_value: value, field_label: key })
  }
}

/** 获取详情动态字段值 */
const getDetailDynamicField = (key) => {
  if (!detailData.value || !detailData.value.dynamic_fields) return '-'
  const field = detailData.value.dynamic_fields.find(f => f.field_key === key)
  return field && field.field_value ? field.field_value : '-'
}

/** 客户选择回调 */
const onCustomerSelect = (item) => {
  formData.customer_name = item.customer_name
  formData.customer_phone = item.phone || ''
  formData.customer_company = item.company || ''
  formData.customer_office = item.office || ''
  formData.customer_address = item.address || ''
}

/** 打开新建对话框 */
const handleAdd = () => {
  isEdit.value = false
  currentOrderId.value = null
  // 重置表单
  Object.assign(formData, {
    customer_name: '', customer_phone: '', customer_company: '',
    customer_office: '', customer_address: '',
    reception_user_id: null, need_bring_back: 0,
    wo_type: '', wo_sub_type: '', priority: 'normal', expected_finish_time: '',
    fault_desc: '', remark: '',
    network_topology: '', fault_location: '', ip_address: '', device_port: '',
    line_type: '', check_items: '', speed_test_data: '', maintenance_cycle: '',
    restart_record: '', debug_content: '',
    device_type: '', device_brand: '', device_model: '', device_sn: '',
    device_password: '', device_config: '', system_version: '', error_code: '',
    repair_part: '', maintenance_items: '', replace_parts_list: '',
    retest_result: '', appearance_desc: '',
    delivery_address: '', install_position: '', arrival_time: '',
    device_quantity: 1, install_materials: '', product_spec: '',
    debug_items: '', acceptance_criteria: '', customer_confirm_items: '',
    camera_count: 0, channel_no: '', nvr_model: '', disk_capacity: '',
    record_status: '', screen_fault: '', infrared_status: '',
    power_status: '', line_inspection: '', point_debug_record: '',
    install_points: '', camera_model: '', storage_config: '', cable_length: '',
    consumable_count: 0, clarity: '', debug_result: '', record_settings: '',
    purchase_product_name: '', purchase_brand: '', purchase_spec: '',
    purchase_quantity: 1, customer_requirement: '', expected_arrival: '',
    purchase_price: 0, service_fee: 0,
    survey_address: '', site_environment: '', device_status: '',
    problem_summary: '', construction_plan: '', required_parts: '',
    estimated_duration: '', estimated_cost: 0,
    own_device_model: '', device_source: '', install_requirement: '',
    consumable_usage: '', customer_confirmation: '',
    parts: [],
    delivery_products: [],
    repair_camera_count: 0,
    // 新增字段
    receive_method: '',
    handle_method: '',
    // 新增字段（订单来源和处理方式）
    order_source: 'wechat',
    service_type: 'onsite',
  })
  // 重置二级分类和动态字段
  subTypeList.value = []
  deviceCategory.value = ''
  dynamicFields.value = []
  formDialogVisible.value = true
}

/** 编辑工单 */
const handleEdit = async (row) => {
  isEdit.value = true
  currentOrderId.value = row.id
  try {
    const res = await request.get(`/workorders/${row.id}`)
    if (res.code === 200) {
      const order = res.data
      // 映射字段名（后端 -> 前端）
      // 配送产品（可能是JSON字符串）
        let deliveryProducts = order.delivery_products
        if (typeof deliveryProducts === 'string' && deliveryProducts) {
          try {
            deliveryProducts = JSON.parse(deliveryProducts)
          } catch (e) {
            deliveryProducts = []
          }
        }
        deliveryProducts = deliveryProducts || []
        Object.assign(formData, {
          customer_name: order.customer_name || '',
          customer_phone: order.customer_phone || '',
          customer_company: order.customer_company || '',
          customer_office: order.customer_office || '',
          customer_address: order.customer_address || '',
          reception_user_id: order.reception_user_id ? Number(order.reception_user_id) : null,
          engineer_user_id: order.engineer_user_id ? Number(order.engineer_user_id) : null,
          // 新增字段（订单来源和处理方式）
          order_source: order.order_source || '',
          service_type: order.service_type || '',
          need_bring_back: order.need_bring_back || 0,
          wo_type: order.wo_type || '',
          wo_sub_type: order.wo_sub_type || '',
          priority: order.priority !== undefined && order.priority !== null ? Number(order.priority) : 0,
          expected_finish_time: order.expected_finish_time || '',
          fault_desc: order.fault_desc || '',
          remark: order.remark || '',
        // 设备信息
        device_type: order.device_type || '',
        device_brand: order.device_brand || '',
        device_model: order.device_model || '',
        device_sn: order.device_sn || '',
        device_password: order.device_password || '',
        device_config: order.device_config || '',
        system_version: order.system_version || '',
        error_code: order.error_code || '',
        // 网络相关
        network_topology: order.network_topology || '',
        fault_location: order.fault_location || '',
        ip_address: order.ip_address || '',
        device_port: order.device_port || '',
        line_type: order.line_type || '',
        check_items: order.check_items || '',
        speed_test_data: order.speed_test_data || '',
        maintenance_cycle: order.maintenance_cycle || '',
        restart_record: order.restart_record || '',
        debug_content: order.debug_content || '',
        // 维修相关
        repair_part: order.repair_part || '',
        maintenance_items: order.maintenance_items || '',
        replace_parts_list: order.replace_parts_list || '',
        retest_result: order.retest_result || '',
        appearance_desc: order.appearance_desc || '',
        // 送货安装
        delivery_address: order.delivery_address || '',
        install_position: order.install_position || '',
        arrival_time: order.arrival_time || '',
        device_quantity: order.device_quantity || 1,
        install_materials: order.install_materials || '',
        product_spec: order.product_spec || '',
        // 监控相关
        camera_count: order.camera_count || 0,
        channel_no: order.channel_no || '',
        nvr_model: order.nvr_model || '',
        disk_capacity: order.disk_capacity || '',
        record_status: order.record_status || '',
        screen_fault: order.screen_fault || '',
        infrared_status: order.infrared_status || '',
        power_status: order.power_status || '',
        line_inspection: order.line_inspection || '',
        point_debug_record: order.point_debug_record || '',
        install_points: order.install_points || '',
        camera_model: order.camera_model || '',
        storage_config: order.storage_config || '',
        cable_length: order.cable_length || '',
        consumable_count: order.consumable_count || 0,
        clarity: order.clarity || '',
        debug_result: order.debug_result || '',
        record_settings: order.record_settings || '',
        // 办公设备
        purchase_product_name: order.purchase_product_name || '',
        purchase_brand: order.purchase_brand || '',
        purchase_spec: order.purchase_spec || '',
        purchase_quantity: order.purchase_quantity || 1,
        customer_requirement: order.customer_requirement || '',
        expected_arrival: order.expected_arrival || '',
        purchase_price: order.purchase_price || 0,
        service_fee: order.service_fee || 0,
        // 勘察相关
        survey_address: order.survey_address || '',
        site_environment: order.site_environment || '',
        device_status: order.device_status || '',
        problem_summary: order.problem_summary || '',
        construction_plan: order.construction_plan || '',
        required_parts: order.required_parts || '',
        estimated_duration: order.estimated_duration || '',
        estimated_cost: order.estimated_cost || 0,
        // 安装调试
        own_device_model: order.own_device_model || '',
        device_source: order.device_source || '',
        install_requirement: order.install_requirement || '',
        debug_items: order.debug_items || '',
        acceptance_criteria: order.acceptance_criteria || '',
        customer_confirmation: order.customer_confirmation || '',
        // 配件
        parts: (order.parts || []).map(p => ({
          part_name: p.part_name || p.product_name || '',
          specification: p.specification || '',
          quantity: p.quantity || 1,
          unit_price: p.unit_price || 0,
          product_id: p.product_id || null
        })),
        // 配送产品
        delivery_products: deliveryProducts,
        repair_camera_count: order.repair_camera_count || 0,
      })
      // 回填二级分类和动态字段
      dynamicFields.value = order.dynamic_fields || []
      if (order.wo_type && order.wo_sub_type) {
        await fetchSubTypes(order.wo_type)
        formData.wo_sub_type = order.wo_sub_type
        const selected = subTypeList.value.find(s => s.sub_type_code === order.wo_sub_type)
        if (selected) {
          deviceCategory.value = selected.device_category || ''
        }
      } else if (order.wo_type) {
        fetchSubTypes(order.wo_type)
      }
      formDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取工单详情失败:', error)
    ElMessage.error('获取工单详情失败')
  }
}

/** 提交新建/编辑表单 */
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      // 使用 toRaw 获取原始对象，并处理日期字段
      const rawFormData = { ...formData }
      // 处理日期字段：空字符串转为 null
      const dateFields = ['arrival_time', 'expected_arrival', 'estimated_time', 'actual_time', 'return_visit_time', 'customer_acceptance_time']
      dateFields.forEach(field => {
        if (rawFormData[field] === '' || rawFormData[field] === undefined) {
          rawFormData[field] = null
        }
      })
      const payload = { ...rawFormData }
      payload.dynamic_fields = dynamicFields.value
      payload.wo_sub_type = formData.wo_sub_type
      let res
      if (isEdit.value && currentOrderId.value) {
        // 编辑
        res = await request.put(`/workorders/${currentOrderId.value}`, payload)
        if (res.code === 200) {
          ElMessage.success('工单更新成功')
        }
      } else {
        // 新建
        res = await request.post('/workorders', payload)
        if (res.code === 200) {
          ElMessage.success('工单创建成功')
        }
      }
      if (res && res.code === 200) {
        formDialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      ElMessage.error('操作失败: ' + (error.message || '未知错误'))
    } finally {
      submitLoading.value = false
    }
  })
}

// ==================== 配件相关（新建表单） ====================

/** 添加配件行 */
const addFormPart = () => {
  if (!formData.parts) formData.parts = []
  formData.parts.push({ part_name: '', specification: '', quantity: 1, unit_price: 0, product_id: null })
}

/** 添加配送产品 */
const addDeliveryProduct = () => {
  if (!formData.delivery_products) {
    formData.delivery_products = []
  }
  formData.delivery_products.push({ product_name: '', specification: '', quantity: 1, unit_price: 0 })
}

/** 打开配送产品选择器 */
const openDeliveryProductSelector = (index) => {
  currentProductSelectorIndex.value = index
  productSelectorMode.value = 'delivery'
  productKeyword.value = ''
  productSelectorVisible.value = true
  fetchProducts()
}

// 商品选择器（新建表单配件用）
const productSelectorVisible = ref(false)
const productList = ref([])
const productLoading = ref(false)
const productKeyword = ref('')
const currentProductSelectorIndex = ref(0)
const productSelectorMode = ref('form') // 'form' 或 'allocate' 或 'delivery'

/** 打开商品选择器 */
const openProductSelector = (index) => {
  currentProductSelectorIndex.value = index
  productSelectorMode.value = 'form'
  productKeyword.value = ''
  productSelectorVisible.value = true
  fetchProducts()
}

/** 选择商品 */
const selectProduct = (product) => {
  if (productSelectorMode.value === 'form') {
    const part = formData.parts[currentProductSelectorIndex.value]
    if (part) {
      part.part_name = product.product_name
      part.specification = product.specification || ''
      part.unit_price = product.sale_price || 0
      part.product_id = product.id
    }
  } else if (productSelectorMode.value === 'delivery') {
    // 配送产品选择模式
    const dp = formData.delivery_products[currentProductSelectorIndex.value]
    if (dp) {
      dp.product_name = product.product_name
      dp.specification = product.specification || ''
      dp.unit_price = product.sale_price || 0
    }
  } else {
    // 领用配件模式
    const part = allocatePartsList.value[currentProductSelectorIndex.value]
    if (part) {
      part.part_name = product.product_name
      part.specification = product.specification || ''
      part.product_id = product.id
      part.stock = product.current_stock || 0
    }
  }
  productSelectorVisible.value = false
}

// ==================== 详情对话框 ====================

const detailDialogVisible = ref(false)
const detailData = ref({})

/** 查看工单详情 */
const handleView = async (row) => {
  detailLoading.value = true
  detailDialogVisible.value = true
  try {
    const res = await request.get(`/workorders/${row.id}`)
    if (res.code === 200) {
      detailData.value = res.data || {}
      // 根据 wo_sub_type 推断 device_category
      if (detailData.value.wo_sub_type && !detailData.value.device_category) {
        const categoryMap = {
          'monitor': ['repair_monitor', 'maintenance_monitor', 'inspection_monitor', 'installation_monitor'],
          'network': ['repair_network', 'maintenance_network', 'inspection_network', 'installation_network'],
          'printer': ['repair_printer', 'maintenance_printer', 'inspection_printer', 'installation_printer'],
          'computer': ['repair_computer', 'maintenance_computer', 'inspection_computer', 'installation_computer'],
          'other': ['repair_other', 'maintenance_other', 'inspection_other', 'installation_other']
        }
        for (const [cat, codes] of Object.entries(categoryMap)) {
          if (codes.includes(detailData.value.wo_sub_type)) {
            detailData.value.device_category = cat
            break
          }
        }
      }
    }
  } catch (error) {
    ElMessage.error('获取工单详情失败')
  } finally {
    detailLoading.value = false
  }
}

// ==================== 派单对话框 ====================

const dispatchDialogVisible = ref(false)
const dispatchForm = reactive({
  dispatch_type: 'manual',
  assigned_user_id: null,
  remark: ''
})
const autoDispatchLoading = ref(false)
const autoDispatchList = ref([])
const dispatchTargetId = ref(null)

/** 打开派单对话框 */
const openDispatchDialog = (row) => {
  dispatchTargetId.value = row.id
  dispatchForm.dispatch_type = 'manual'
  dispatchForm.assigned_user_id = null
  dispatchForm.remark = ''
  autoDispatchList.value = []
  dispatchDialogVisible.value = true
}

/** 派单方式切换时自动获取推荐 */
const onDispatchTypeChange = async (val) => {
  if (val === 'auto') {
    autoDispatchLoading.value = true
    try {
      // 获取当前工单的类型
      const currentOrder = tableData.value.find(item => item.id === dispatchTargetId.value)
      const woType = currentOrder ? currentOrder.wo_type : ''
      const res = await request.get('/workorders/auto-dispatch', { params: { wo_type: woType } })
      if (res.code === 200) {
        autoDispatchList.value = res.data.recommendations || res.data || []
      }
    } catch (error) {
      console.error('获取自动派单推荐失败:', error)
    } finally {
      autoDispatchLoading.value = false
    }
  }
}

/** 提交派单 */
const submitDispatch = async () => {
  if (dispatchForm.dispatch_type === 'manual' && !dispatchForm.assigned_user_id) {
    ElMessage.warning('请选择工程师')
    return
  }
  submitLoading.value = true
  try {
    const res = await request.post(`/workorders/${dispatchTargetId.value}/dispatch`, {
      dispatch_type: dispatchForm.dispatch_type,
      assigned_user_id: dispatchForm.assigned_user_id,
      remark: dispatchForm.remark
    })
    if (res.code === 200) {
      ElMessage.success('派单成功')
      dispatchDialogVisible.value = false
      fetchData()
      // 如果详情页打开则刷新
      if (detailDialogVisible.value) {
        handleView({ id: dispatchTargetId.value })
      }
    }
  } catch (error) {
    ElMessage.error('派单失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 领用配件对话框 ====================

const allocatePartsDialogVisible = ref(false)
const allocatePartsList = ref([])
const allocateTargetId = ref(null)
const syncPartsLoading = ref(false)

/** 打开领用配件对话框 */
const openAllocatePartsDialog = async (row) => {
  allocateTargetId.value = row.id
  allocatePartsList.value = []
  allocatePartsDialogVisible.value = true
}

/** 同步客户需求配件 */
const syncCustomerParts = async () => {
  syncPartsLoading.value = true
  try {
    const res = await request.get(`/workorders/${allocateTargetId.value}`)
    if (res.code === 200 && res.data) {
      const customerParts = res.data.customer_parts || []
      if (customerParts.length === 0) {
        ElMessage.info('该工单没有客户需求配件')
        syncPartsLoading.value = false
        return
      }
      // 把客户需求配件添加到领用列表（避免重复）
      for (const cp of customerParts) {
        const exists = allocatePartsList.value.find(p => p.product_name === cp.product_name && p.specification === cp.specification)
        if (!exists) {
          allocatePartsList.value.push({
            product_id: cp.product_id || null,
            product_name: cp.product_name,
            specification: cp.specification || '',
            quantity: cp.quantity || 1,
            stock: null,
            from_customer: true
          })
        }
      }
      ElMessage.success(`已同步${customerParts.length}项客户需求配件`)
    }
  } catch (error) {
    ElMessage.error('同步失败')
  } finally {
    syncPartsLoading.value = false
  }
}

/** 添加领用配件行 */
const addAllocatePart = () => {
  allocatePartsList.value.push({ part_name: '', product_name: '', specification: '', quantity: 1, product_id: null, stock: null, from_customer: false })
}

/** 打开商品选择器（领用配件模式） */
const openAllocateProductSelector = (index) => {
  currentProductSelectorIndex.value = index
  productSelectorMode.value = 'allocate'
  productKeyword.value = ''
  productSelectorVisible.value = true
  fetchProducts()
}

/** 提交领用配件 */
const submitAllocateParts = async () => {
  if (allocatePartsList.value.length === 0) {
    ElMessage.warning('请添加配件')
    return
  }
  submitLoading.value = true
  try {
    const res = await request.post(`/workorders/${allocateTargetId.value}/allocate-parts`, {
      parts: allocatePartsList.value
    })
    if (res.code === 200) {
      ElMessage.success('配件领用成功')
      allocatePartsDialogVisible.value = false
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: allocateTargetId.value })
      }
    }
  } catch (error) {
    ElMessage.error('领用配件失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 完工对话框 ====================

const finishDialogVisible = ref(false)
const finishForm = reactive({ report: '', test_result: 'pass', test_remark: '' })
const finishTargetId = ref(null)

/** 打开完工对话框 */
const openFinishDialog = (row) => {
  finishTargetId.value = row.id
  finishForm.report = ''
  finishForm.test_result = 'pass'
  finishForm.test_remark = ''
  finishDialogVisible.value = true
}

/** 提交完工 */
const submitFinish = async () => {
  submitLoading.value = true
  try {
    const res = await request.post(`/workorders/${finishTargetId.value}/finish`, finishForm)
    if (res.code === 200) {
      ElMessage.success('完工提交成功')
      finishDialogVisible.value = false
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: finishTargetId.value })
      }
    }
  } catch (error) {
    ElMessage.error('完工提交失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 结算对话框 ====================

const settleDialogVisible = ref(false)
const settleForm = reactive({
  labor_hours: 0,
  labor_unit_price: 0,
  labor_cost_direct: 0,
  parts_cost: 0,
  other_cost: 0,
  account_id: null,
  settle_type: 'cash',
  credit_remark: ''
})
const settleTargetId = ref(null)
const settlePartsList = ref([])

/** 计算人工费（工时×单价） */
const calcLaborCost = computed(() => {
  if (settleForm.labor_cost_direct > 0) return settleForm.labor_cost_direct.toFixed(2)
  return ((settleForm.labor_hours || 0) * (settleForm.labor_unit_price || 0)).toFixed(2)
})

/** 计算总费用 */
const calcTotalCost = computed(() => {
  const labor = settleForm.labor_cost_direct > 0
    ? settleForm.labor_cost_direct
    : (settleForm.labor_hours || 0) * (settleForm.labor_unit_price || 0)
  return (labor + (settleForm.parts_cost || 0) + (settleForm.other_cost || 0)).toFixed(2)
})

/** 工时/单价变化时清空直接输入 */
const onLaborCalcChange = () => {
  if (settleForm.labor_hours > 0 || settleForm.labor_unit_price > 0) {
    settleForm.labor_cost_direct = 0
  }
}

/** 直接输入人工费时清空工时/单价 */
const onLaborDirectChange = (val) => {
  if (val > 0) {
    settleForm.labor_hours = 0
    settleForm.labor_unit_price = 0
  }
}

/** 计算配件材料费 */
const calcSettlePartsCost = () => {
  let total = 0
  for (const part of settlePartsList.value) {
    total += (part.used_quantity || 0) * (part.unit_price || 0)
  }
  settleForm.parts_cost = total
}

/** 退回开关变化 */
const onReturnChange = (row) => {
  if (row.return_unused) {
    // 退回未使用：实际使用数量设为0
    row.used_quantity = 0
  } else {
    // 取消退回：恢复为领用数量
    row.used_quantity = row.quantity
  }
  calcSettlePartsCost()
}

/** 结算方式变化 */
const onSettleTypeChange = (val) => {
  if (val === 'cash') {
    settleForm.credit_remark = ''
  } else {
    settleForm.account_id = null
  }
}

/** 打开结算对话框 */
const openSettleDialog = async (row) => {
  settleTargetId.value = row.id
  settleForm.labor_hours = 0
  settleForm.labor_unit_price = 0
  settleForm.labor_cost_direct = 0
  settleForm.parts_cost = 0
  settleForm.other_cost = 0
  settleForm.account_id = null
  settleForm.settle_type = 'cash'
  settleForm.credit_remark = ''
  settlePartsList.value = []

  // 获取工单详情（包含已领配件列表）
  try {
    const res = await request.get(`/workorders/${row.id}`)
    if (res.code === 200) {
      const data = res.data || {}
      settleForm.labor_hours = data.labor_hours || 0
      settleForm.labor_unit_price = data.labor_unit_price || 0
      settleForm.other_cost = data.other_cost || 0

      // 填充已领配件清单
      const parts = data.parts || []
      settlePartsList.value = parts.map(p => ({
        id: p.id,
        product_id: p.product_id,
        product_name: p.product_name || '',
        specification: p.specification || '',
        quantity: p.quantity || 0,
        used_quantity: p.used_quantity || p.quantity || 0,
        unit_price: parseFloat(p.unit_price) || 0,
        is_own: p.is_own,
        return_unused: false
      }))
      calcSettlePartsCost()
    }
  } catch (error) {
    console.error('获取工单详情失败', error)
  }
  settleDialogVisible.value = true
}

/** 提交结算 */
const submitSettle = async () => {
  // 根据结算方式校验
  if (settleForm.settle_type === 'cash' && !settleForm.account_id) {
    ElMessage.warning('请选择结算账户')
    return
  }
  submitLoading.value = true
  try {
    // 构建配件使用数据
    const partsData = {}
    for (const part of settlePartsList.value) {
      partsData[`used_qty_${part.id}`] = part.used_quantity
    }
    const res = await request.post(`/workorders/${settleTargetId.value}/settle`, {
      labor_hours: settleForm.labor_hours,
      labor_unit_price: settleForm.labor_unit_price,
      labor_cost: calcLaborCost.value,
      parts_cost: settleForm.parts_cost,
      other_cost: settleForm.other_cost,
      total_cost: calcTotalCost.value,
      account_id: settleForm.settle_type === 'cash' ? settleForm.account_id : null,
      settle_type: settleForm.settle_type,
      credit_remark: settleForm.credit_remark,
      ...partsData
    })
    if (res.code === 200) {
      ElMessage.success('结算成功')
      settleDialogVisible.value = false
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: settleTargetId.value })
      }
    }
  } catch (error) {
    ElMessage.error('结算失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 客户验收对话框 ====================

const acceptanceDialogVisible = ref(false)
const acceptanceForm = reactive({ result: 1, remark: '' })
const acceptanceTargetId = ref(null)

/** 打开客户验收对话框 */
const openAcceptanceDialog = (row) => {
  acceptanceTargetId.value = row.id
  acceptanceForm.result = 1
  acceptanceForm.remark = ''
  acceptanceDialogVisible.value = true
}

/** 提交客户验收 */
const submitAcceptance = async () => {
  submitLoading.value = true
  try {
    // 后端期望的字段名是 customer_acceptance，不是 result
    const payload = {
      customer_acceptance: parseInt(acceptanceForm.result),
      customer_acceptance_sign: acceptanceForm.sign || ''
    }
    const res = await request.post(`/workorders/${acceptanceTargetId.value}/acceptance`, payload)
    if (res.code === 200) {
      ElMessage.success('验收提交成功')
      acceptanceDialogVisible.value = false
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: acceptanceTargetId.value })
      }
    }
  } catch (error) {
    ElMessage.error('验收提交失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 上门送回对话框 ====================

const returnVisitDialogVisible = ref(false)
const returnVisitForm = reactive({ visit_time: '', result: '' })
const returnVisitTargetId = ref(null)

/** 打开上门送回对话框 */
const openReturnVisitDialog = (row) => {
  returnVisitTargetId.value = row.id
  returnVisitForm.visit_time = ''
  returnVisitForm.result = ''
  returnVisitDialogVisible.value = true
}

/** 提交上门送回 */
const submitReturnVisit = async () => {
  submitLoading.value = true
  try {
    const res = await request.post(`/workorders/${returnVisitTargetId.value}/return-visit`, returnVisitForm)
    if (res.code === 200) {
      ElMessage.success('送回记录提交成功')
      returnVisitDialogVisible.value = false
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: returnVisitTargetId.value })
      }
    }
  } catch (error) {
    ElMessage.error('送回记录提交失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 转换对话框（转报价/转采购/转销售） ====================

const convertDialogVisible = ref(false)
const convertDialogTitle = ref('')
const convertDialogMsg = ref('')
const convertType = ref('')
const convertTargetId = ref(null)

/** 转报价 */
const handleToQuote = (row) => {
  convertTargetId.value = row.id
  convertType.value = 'to-quote'
  convertDialogTitle.value = '转报价单'
  convertDialogMsg.value = `确定将工单 ${row.wo_no} 转为报价单？`
  convertDialogVisible.value = true
}

/** 转采购 */
const handleToPurchase = (row) => {
  convertTargetId.value = row.id
  convertType.value = 'to-purchase'
  convertDialogTitle.value = '转采购预订单'
  convertDialogMsg.value = `确定将工单 ${row.wo_no} 转为采购预订单？`
  convertDialogVisible.value = true
}

/** 转销售 */
const handleToSales = (row) => {
  convertTargetId.value = row.id
  convertType.value = 'to-sales'
  convertDialogTitle.value = '转销售单'
  convertDialogMsg.value = `确定将工单 ${row.wo_no} 转为销售单？`
  convertDialogVisible.value = true
}

/** 提交转换 */
const submitConvert = async () => {
  submitLoading.value = true
  try {
    const res = await request.post(`/workorders/${convertTargetId.value}/${convertType.value}`)
    if (res.code === 200) {
      ElMessage.success('转换成功')
      convertDialogVisible.value = false
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: convertTargetId.value })
      }
    }
  } catch (error) {
    ElMessage.error('转换失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 工单报价功能 ====================

const quoteDialogVisible = ref(false)
const currentQuoteWoId = ref(null)
const quoteForm = reactive({
  labor_cost: 0,
  parts_cost: 0,
  other_cost: 0,
  total_cost: 0,
  items: [],
  customer_confirm: '1',
  reject_reason: ''
})

// 报价配件选择对话框
const quoteProductSelectorVisible = ref(false)
const quoteProductKeyword = ref('')
const quoteProductList = ref([])
const quoteProductLoading = ref(false)
const currentQuoteItemIndex = ref(null)

/** 打开报价对话框 */
const openQuoteDialog = (row) => {
  currentQuoteWoId.value = row.id
  quoteForm.labor_cost = row.labor_cost || 0
  quoteForm.parts_cost = row.parts_cost || 0
  quoteForm.other_cost = row.other_cost || 0
  quoteForm.total_cost = row.total_cost || 0
  quoteForm.items = []
  quoteForm.customer_confirm = '1'
  quoteForm.reject_reason = ''
  quoteDialogVisible.value = true
}

/** 计算报价总计 */
const calcQuoteTotal = () => {
  quoteForm.total_cost = (quoteForm.labor_cost || 0) + (quoteForm.parts_cost || 0) + (quoteForm.other_cost || 0)
}

/** 添加报价配件项 */
const addQuoteItem = () => {
  quoteForm.items.push({
    product_name: '',
    spec: '',
    unit: '',
    quantity: 1,
    unit_price: 0,
    subtotal: 0
  })
}

/** 计算配件小计 */
const calcQuoteItemSubtotal = (row) => {
  row.subtotal = (row.quantity || 0) * (row.unit_price || 0)
}

/** 打开报价配件选择对话框 */
const openQuoteProductSelector = (index) => {
  currentQuoteItemIndex.value = index
  quoteProductKeyword.value = ''
  quoteProductList.value = []
  quoteProductSelectorVisible.value = true
  fetchQuoteProducts()
}

/** 获取配件列表（关联库存） */
const fetchQuoteProducts = async () => {
  quoteProductLoading.value = true
  try {
    const res = await request.get('/products', {
      params: {
        keyword: quoteProductKeyword.value,
        page: 1,
        page_size: 50
      }
    })
    if (res.code === 200) {
      quoteProductList.value = res.data.list || []
    }
  } catch (error) {
    console.error('获取配件列表失败:', error)
  } finally {
    quoteProductLoading.value = false
  }
}

/** 选择配件 */
const selectQuoteProduct = (product) => {
  if (currentQuoteItemIndex.value !== null) {
    const item = quoteForm.items[currentQuoteItemIndex.value]
    item.product_name = product.product_name
    item.spec = product.specification
    item.unit = product.unit_name
    item.unit_price = product.sale_price || 0
    item.quantity = 1
    calcQuoteItemSubtotal(item)
  }
  quoteProductSelectorVisible.value = false
}

/** 提交报价 */
const submitQuote = async () => {
  submitLoading.value = true
  try {
    const res = await request.post(`/workorders/${currentQuoteWoId.value}/quote`, {
      labor_cost: quoteForm.labor_cost,
      parts_cost: quoteForm.parts_cost,
      other_cost: quoteForm.other_cost,
      total_cost: quoteForm.total_cost,
      items: quoteForm.items,
      customer_confirm: parseInt(quoteForm.customer_confirm),
      reject_reason: quoteForm.reject_reason
    })
    if (res.code === 200) {
      ElMessage.success('报价提交成功')
      quoteDialogVisible.value = false
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: currentQuoteWoId.value })
      }
    }
  } catch (error) {
    ElMessage.error('报价提交失败')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 状态操作 ====================

/** 开始处理（1→3） */
const handleStartProcess = async (row) => {
  try {
    await ElMessageBox.confirm('确定开始处理此工单？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    const res = await request.post(`/workorders/${row.id}/status`, { status: 4, content: '开始上门处理' })
    if (res.code === 200) {
      ElMessage.success('操作成功')
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: row.id })
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

/** 配件到齐（4→3） */
const handlePartsReady = async (row) => {
  try {
    await ElMessageBox.confirm('确认配件已到齐？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    const res = await request.post(`/workorders/${row.id}/status`, { status: 3, content: '配件到齐，继续处理' })
    if (res.code === 200) {
      ElMessage.success('操作成功')
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: row.id })
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

/** 审核通过（5→6） */
const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm('确认审核通过？', '审核确认', {
      confirmButtonText: '通过',
      cancelButtonText: '取消',
      type: 'info'
    })
    const res = await request.post(`/workorders/${row.id}/status`, { status: 6, content: '审核通过' })
    if (res.code === 200) {
      ElMessage.success('审核通过')
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: row.id })
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

/** 确认入库（6→7） */
const handleConfirmStockIn = async (row) => {
  try {
    await ElMessageBox.confirm('确认配件已入库？', '入库确认', {
      confirmButtonText: '确认入库',
      cancelButtonText: '取消',
      type: 'info'
    })
    const res = await request.post(`/workorders/${row.id}/status`, { status: 7, content: '配件已入库' })
    if (res.code === 200) {
      ElMessage.success('入库确认成功')
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: row.id })
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

/** 取消工单 */
const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm('确定要取消此工单吗？此操作不可撤销。', '取消确认', {
      confirmButtonText: '确定取消',
      cancelButtonText: '返回',
      type: 'warning'
    })
    const res = await request.post(`/workorders/${row.id}/cancel`)
    if (res.code === 200) {
      ElMessage.success('工单已取消')
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: row.id })
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败')
    }
  }
}

// 带回维修 - 工程师上门后发现需要带设备回店维修
const handleBringBack = async (row) => {
  try {
    await ElMessageBox.confirm(
      '确定要将设备带回本店维修吗？系统将自动创建接件单并关联此工单。',
      '带回维修确认',
      { confirmButtonText: '确定带回', cancelButtonText: '取消', type: 'warning' }
    )
    const res = await request.put(`/workorders/${row.id}`, { need_bring_back: 1 })
    if (res.code === 200) {
      ElMessage.success('已标记带回维修，接件单已自动创建')
      fetchData()
      if (detailDialogVisible.value) {
        handleView({ id: row.id })
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// ==================== 打印功能（使用通用打印组件） ====================
import PrintDialog from '@/components/PrintDialog.vue'

const printDialogVisible = ref(false)
const printData = ref({})

/** 打开打印对话框 */
const handlePrint = async (row) => {
  // 先获取完整数据（列表数据可能不完整）
  let fullData = row
  try {
    const res = await request.get(`/workorders/${row.id}`)
    if (res.code === 200) {
      fullData = res.data || row
    }
  } catch (e) {
    // 使用原始行数据
  }

  // 根据 wo_sub_type 推断 device_category
  let deviceCategory = ''
  if (fullData.wo_sub_type) {
    const categoryMap = {
      'monitor': ['repair_monitor', 'maintenance_monitor', 'inspection_monitor', 'installation_monitor'],
      'network': ['repair_network', 'maintenance_network', 'inspection_network', 'installation_network'],
      'printer': ['repair_printer', 'maintenance_printer', 'inspection_printer', 'installation_printer'],
      'computer': ['repair_computer', 'maintenance_computer', 'inspection_computer', 'installation_computer'],
      'other': ['repair_other', 'maintenance_other', 'inspection_other', 'installation_other']
    }
    for (const [cat, codes] of Object.entries(categoryMap)) {
      if (codes.includes(fullData.wo_sub_type)) {
        deviceCategory = cat
        break
      }
    }
  }

  // 格式化费用明细表格
  let feeDetail = ''
  if (fullData.parts && fullData.parts.length > 0) {
    feeDetail = '<table width="100%" border="1" cellspacing="0" cellpadding="5">' +
      '<tr><th>项目</th><th>数量</th><th>单价</th><th>金额</th></tr>' +
      fullData.parts.map(p => `<tr><td>${p.name || ''}</td><td>${p.quantity || 1}</td><td>¥${p.price || 0}</td><td>¥${(p.quantity || 1) * (p.price || 0)}</td></tr>`).join('') +
      '</table>'
  }

  // 格式化维修项目
  let repairItems = ''
  if (fullData.dynamic_fields && fullData.dynamic_fields.length > 0) {
    repairItems = fullData.dynamic_fields.map(f => `${f.label || ''}: ${f.value || ''}`).join('<br>')
  }

  printData.value = {
    wo_no: fullData.wo_no || '',
    wo_type: woTypeMap[fullData.wo_type] || fullData.wo_type || '',
    wo_type_name: woTypeMap[fullData.wo_type] || fullData.wo_type || '',
    sub_type_name: fullData.sub_type_name || '',
    device_category: deviceCategory,
    customer_name: fullData.customer_name || '',
    customer_phone: fullData.customer_phone || '',
    customer_address: fullData.customer_address || '',
    customer_company: fullData.customer_company || '',
    device_type: fullData.device_type || '',
    device_brand: fullData.device_brand || '',
    device_model: fullData.device_model || '',
    device_sn: fullData.device_sn || '',
    monitor_brand: fullData.monitor_brand || '',
    camera_count: fullData.camera_count || '',
    repair_camera_count: fullData.repair_camera_count || '',
    nvr_model: fullData.nvr_model || '',
    channel_no: fullData.channel_no || '',
    disk_capacity: fullData.disk_capacity || '',
    recording_status: fullData.recording_status || '',
    camera_location: fullData.camera_location || '',
    toner_model: fullData.toner_model || '',
    drum_model: fullData.drum_model || '',
    dynamic_fields: JSON.stringify(fullData.dynamic_fields || []),
    delivery_products: JSON.stringify(fullData.delivery_products || []),
    delivery_address: fullData.delivery_address || '',
    install_position: fullData.install_position || '',
    arrival_time: fullData.arrival_time || '',
    goods_quantity: fullData.goods_quantity || '',
    goods_floor_type: fullData.goods_floor_type || '',
    install_material: fullData.install_material || '',
    parts: JSON.stringify(fullData.parts || []),
    fault_desc: fullData.fault_desc || '',
    remark: fullData.remark || '',
    created_at: fullData.created_at || new Date().toLocaleString('zh-CN'),
    order_source: orderSourceMap[fullData.order_source] || fullData.order_source || '',
    service_type: serviceTypeMap[fullData.service_type] || fullData.service_type || '',
    status_name: statusMap[fullData.status] || '',
    priority_name: priorityMap[fullData.priority] || '',
    total_amount: fullData.total_amount || fullData.total_cost || '0.00',
    fee_detail: feeDetail,
    repair_items: repairItems,
    engineer_name: fullData.engineer_name || '',
    engineer_phone: fullData.engineer_phone || '',
    // 接件单相关字段（兼容用户在工单模板中添加的接件字段）
    receptionist: fullData.receptionist_name || fullData.receptionist || fullData.created_by_name || '',
    receptionist_name: fullData.receptionist_name || fullData.receptionist || fullData.created_by_name || '',
    receive_no: fullData.receive_no || fullData.wo_no || '',
    address: fullData.customer_address || fullData.address || '',
    appearance: fullData.appearance || '',
    accessories: fullData.accessories || '',
    estimate_amount: fullData.estimate_amount || fullData.total_amount || '0.00',
    // 设备信息兼容字段
    equipment_name: fullData.device_brand || '',
    equipment_model: fullData.device_model || '',
    // 时间字段
    receive_date: fullData.created_at || fullData.receive_date || ''
  }
  printDialogVisible.value = true
}

// ==================== 初始化 ====================

onMounted(() => {
  fetchData()
  fetchUsers()
  fetchAccounts()
  // 初始化二级分类数据（如果数据库中还没有数据，调用 init-subtypes 接口）
  initSubTypes()
})

/** 初始化二级分类数据 */
const initSubTypes = async () => {
  try {
    await request.post('/workorders/init-subtypes')
  } catch (e) {
    // 忽略错误，可能已经初始化过
  }
}
</script>

<style lang="scss" scoped>
.workorder-page {
  padding: 0;

  /* 流程引导卡片 */
  .workflow-guide-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    color: #fff;
  }
  .guide-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  .stage-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .stage-name {
    font-size: 18px;
    font-weight: bold;
  }
  .guide-desc {
    font-size: 14px;
    opacity: 0.9;
  }
  .stage-progress {
    display: flex;
    justify-content: space-between;
    margin: 15px 0;
  }
  .stage-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
  }
  .stage-dot {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-bottom: 5px;
    transition: all 0.3s;
  }
  .stage-item.active .stage-dot {
    background: #fff;
    color: #667eea;
    box-shadow: 0 0 10px rgba(255,255,255,0.5);
  }
  .stage-item.done .stage-dot {
    background: #67c23a;
    color: #fff;
  }
  .stage-label {
    font-size: 12px;
    opacity: 0.8;
  }
  .stage-item.active .stage-label {
    opacity: 1;
    font-weight: bold;
  }
  .next-action-hint {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.2);
    padding: 10px 15px;
    border-radius: 8px;
    font-size: 14px;
  }

  /* 详情页底部操作栏 */
  .detail-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
  }
  .primary-actions {
    display: flex;
    gap: 10px;
  }
  .more-actions {
    flex: 1;
    text-align: center;
  }
  .common-actions {
    display: flex;
    gap: 10px;
  }

  /* 统计卡片 */
  .stat-row {
    margin-bottom: 16px;

    .stat-card {
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-2px);
      }

      .stat-content {
        text-align: center;

        .stat-label {
          font-size: 13px;
          color: #909399;
          margin-bottom: 8px;
        }

        .stat-value {
          font-size: 28px;
          font-weight: bold;
          line-height: 1;

          &.color-warning { color: #e6a23c; }
          &.color-primary { color: #409eff; }
          &.color-success { color: #67c23a; }
          &.color-danger { color: #f56c6c; }
          &.color-default { color: #303133; }
        }
      }
    }
  }

  /* 卡片头部 */
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .card-title {
      font-size: 16px;
      font-weight: bold;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  /* 批量操作工具栏 */
  .batch-toolbar {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #ebeef5;
    display: flex;
    align-items: center;
  }

  /* 搜索表单 */
  .search-form {
    margin-bottom: 16px;
  }

  /* 分页 */
  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}

/* 详情页左右布局 */
.detail-layout {
  display: flex;
  gap: 0;

  .detail-main {
    flex: 1;
    min-width: 0;
  }

  .detail-sidebar {
    flex-shrink: 0;
  }
}
</style>
