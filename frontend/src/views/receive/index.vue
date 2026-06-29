<template>
  <div class="receive-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>接件管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
            <el-button type="primary" :icon="Plus" v-permission="'receive:add'" @click="handleAdd">新增接件</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="客户名称/电话/接件单号"
            clearable
            style="width: 220px"
            @keyup.enter="fetchData"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option
              v-for="(label, val) in statusMap"
              :key="val"
              :label="label"
              :value="Number(val)"
            />
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
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchData">搜索</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="receive_no" label="接件单号" width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.receive_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户名称" min-width="100" show-overflow-tooltip />
        <el-table-column prop="customer_phone" label="电话" width="120" />
        <el-table-column label="设备类型" width="100">
          <template #default="{ row }">
            {{ (row.devices && row.devices[0] && row.devices[0].device_type) || row.device_type || '' }}
          </template>
        </el-table-column>
        <el-table-column label="品牌型号" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            {{ (row.devices && row.devices[0]) ? ((row.devices[0].device_brand || '') + ((row.devices[0].device_model || row.devices[0].model) ? ' ' + (row.devices[0].device_model || row.devices[0].model) : '')) : ((row.device_brand || '') + (row.device_model ? ' ' + row.device_model : '')) }}
          </template>
        </el-table-column>
        <el-table-column label="接待员工" width="100" show-overflow-tooltip>
          <template #default="{ row }">{{ row.reception_user_name || row.receiver_name || '' }}</template>
        </el-table-column>
        <el-table-column label="维修工程师" width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ row.engineer_user_name || row.engineer_name || '' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="接件时间" width="170" />
        <el-table-column label="操作" width="300" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">查看</el-button>
            <el-button type="info" link size="small" @click="handleRePrint(row)">
              <el-icon style="margin-right: 2px;"><Printer /></el-icon>打印
            </el-button>
            <el-dropdown trigger="click" @command="(cmd) => handleLabelPrint(cmd, row)">
              <el-button type="success" link size="small">
                标签<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="device_label">设备标签</el-dropdown-item>
                  <el-dropdown-item command="customer_label">客户自带标签</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="warning" link size="small" @click="handleEdit(row)" v-if="canEdit(row.status)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleCancel(row)" v-if="canCancel(row.status)">取消</el-button>
            <!-- 已登记(0)：工程师检测 -->
            <el-button type="success" link size="small" @click="openDetectDialog(row)" v-if="row.status === 0">工程师检测</el-button>
            <!-- 检测中(1)：提交检测结果 -->
            <el-button type="success" link size="small" @click="openDetectDialog(row)" v-if="row.status === 1">提交检测结果</el-button>
            <!-- 待报价(2)：生成报价 -->
            <el-button type="warning" link size="small" @click="openQuoteDialog(row)" v-if="row.status === 2">生成报价</el-button>
            <!-- 待客户确认(3)：客户确认/拒绝 -->
            <el-button type="success" link size="small" @click="openConfirmDialog(row)" v-if="row.status === 3">客户确认</el-button>
            <!-- 待领料/采购(4)：领料、跳过领料 -->
            <el-button type="warning" link size="small" @click="openAllocateDialog(row)" v-if="row.status === 4">领料/采购</el-button>
            <el-button type="info" link size="small" @click="handleSkipAllocate(row)" v-if="row.status === 4">跳过领料</el-button>
            <!-- 维修中(5)：提交完工 -->
            <el-button type="success" link size="small" @click="openFinishDialog(row)" v-if="row.status === 5">提交完工</el-button>
            <!-- 待测试(6)：测试设备 -->
            <el-button type="warning" link size="small" @click="openTestDialog(row)" v-if="row.status === 6">测试设备</el-button>
            <!-- 待取件(7)：通知取件、完工结算 -->
            <el-button type="success" link size="small" @click="openNotifyDialog(row)" v-if="row.status === 7">通知取件</el-button>
            <el-button type="warning" link size="small" @click="openSettleDialog(row)" v-if="row.status === 7">完工结算</el-button>
            <!-- 待结算(8)：取件完成 -->
            <el-button type="primary" link size="small" @click="handleComplete(row)" v-if="row.status === 8">取件完成</el-button>
            <!-- 送修外店(10)：外店报价 -->
            <el-button type="warning" link size="small" @click="openExternalQuoteDialog(row)" v-if="row.status === 10">外店报价</el-button>
            <!-- 外店已报价(11)：给客户报价 -->
            <el-button type="warning" link size="small" @click="openCustomerQuoteDialog(row)" v-if="row.status === 11">给客户报价</el-button>
            <!-- 待外店维修(12)：确认送修 -->
            <el-button type="success" link size="small" @click="handleExternalConfirm(row)" v-if="row.status === 12">确认送修</el-button>
            <!-- 外店维修中(13)：取回设备 -->
            <el-button type="warning" link size="small" @click="openExternalReturnDialog(row)" v-if="row.status === 13">取回设备</el-button>
            <!-- 外店取回待测试(14)：测试设备 -->
            <el-button type="warning" link size="small" @click="openTestDialog(row)" v-if="row.status === 14">测试设备</el-button>
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

    <!-- ==================== 新增/编辑对话框 ==================== -->
    <el-dialog
      v-model="formDialogVisible"
      :title="formDialogTitle"
      width="900px"
      destroy-on-close
      top="3vh"
      :close-on-click-modal="false"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <!-- 客户信息区 -->
        <el-divider content-position="left">客户信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户名称" prop="customer_name">
              <el-autocomplete
                v-model="formData.customer_name"
                :fetch-suggestions="searchCustomer"
                placeholder="输入客户名称或电话搜索"
                @select="onCustomerSelect"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="customer_phone">
              <el-input v-model="formData.customer_phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="客户地址">
              <el-input v-model="formData.customer_address" placeholder="客户地址" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 员工信息区 -->
        <el-divider content-position="left">员工信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="接待员工" prop="reception_user_id">
              <el-select v-model="formData.reception_user_id" placeholder="选择接待员工" filterable style="width: 100%">
                <el-option
                  v-for="u in userList"
                  :key="u.id"
                  :label="u.name || u.username"
                  :value="u.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="维修工程师" prop="engineer_user_id">
              <el-select v-model="formData.engineer_user_id" placeholder="选择维修工程师" filterable clearable style="width: 100%">
                <el-option
                  v-for="u in userList"
                  :key="u.id"
                  :label="u.name || u.username"
                  :value="u.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 设备信息区（支持多设备） -->
        <el-divider content-position="left">
          设备信息
          <el-button type="primary" link size="small" :icon="Plus" @click="addDevice" style="margin-left: 10px">添加设备</el-button>
        </el-divider>
        <div v-for="(device, dIdx) in formData.devices" :key="dIdx" class="device-block">
          <div class="device-block-header">
            <span>设备 {{ dIdx + 1 }}</span>
            <el-button type="danger" link size="small" :icon="Delete" @click="removeDevice(dIdx)" v-if="formData.devices.length > 1">删除设备</el-button>
          </div>
          <el-row :gutter="20">
            <el-col :span="6">
              <el-form-item label="设备类型">
                <el-select v-model="device.device_type" placeholder="选择类型" style="width: 100%">
                  <el-option v-for="t in deviceTypeOptions" :key="t" :label="t" :value="t" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="设备名称">
                <el-input v-model="device.device_name" placeholder="设备名称" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="品牌">
                <el-input v-model="device.brand" placeholder="品牌" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="型号">
                <el-input v-model="device.model" placeholder="型号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="序列号">
                <el-input v-model="device.serial_number" placeholder="序列号/SN" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 根据设备类型动态显示字段 -->
          <template v-if="device.device_type === '电脑'">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="CPU">
                  <el-input v-model="device.cpu" placeholder="CPU" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="内存">
                  <el-input v-model="device.memory" placeholder="内存" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="硬盘">
                  <el-input v-model="device.hard_disk" placeholder="硬盘" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="系统">
                  <el-input v-model="device.os" placeholder="操作系统" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="系统版本">
                  <el-input v-model="device.os_version" placeholder="系统版本" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>
          <template v-if="device.device_type === '打印机'">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="硒鼓型号">
                  <el-input v-model="device.toner_model" placeholder="硒鼓型号" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="粉盒型号">
                  <el-input v-model="device.cartridge_model" placeholder="粉盒型号" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>
          <template v-if="device.device_type === '监控设备'">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="监控品牌">
                  <el-input v-model="device.monitor_brand" placeholder="监控品牌" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="摄像头数量">
                  <el-input-number v-model="device.camera_count" :min="0" controls-position="right" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>
          <template v-if="device.device_type === '网络设备'">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="端口数">
                  <el-input-number v-model="device.port_count" :min="0" controls-position="right" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="IP地址">
                  <el-input v-model="device.ip_address" placeholder="IP地址" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="固件版本">
                  <el-input v-model="device.firmware_version" placeholder="固件版本" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- 故障描述、外观描述 -->
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="故障描述">
                <el-input v-model="device.fault_desc" type="textarea" :rows="2" placeholder="该设备的故障描述" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="外观描述">
                <el-input v-model="device.appearance_desc" type="textarea" :rows="2" placeholder="该设备的外观描述" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 客户自带附件（仅登记留底，不进库存和结算） -->
          <div class="parts-section">
            <div class="parts-header">
              <span class="parts-title">客户自带附件</span>
              <el-tag type="info" size="small" style="margin-left: 10px;">仅登记留底，不进库存和结算</el-tag>
              <el-button type="primary" link size="small" :icon="Plus" @click="addPart(dIdx)" style="margin-left: auto;">添加附件</el-button>
            </div>
            <el-table :data="device.parts" border size="small" style="width: 100%">
              <el-table-column label="附件名称" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="row.name" size="small" placeholder="如：电源线、说明书等" />
                </template>
              </el-table-column>
              <el-table-column label="数量" width="100" align="center">
                <template #default="{ row }">
                  <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="状态" width="120" align="center">
                <template #default="{ row }">
                  <el-select v-model="row.status" size="small" style="width: 100%">
                    <el-option label="完好" value="完好" />
                    <el-option label="损坏" value="损坏" />
                    <el-option label="缺失" value="缺失" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="备注" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="row.remark" size="small" placeholder="备注" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70" align="center">
                <template #default="{ $index }">
                  <el-button type="danger" link size="small" :icon="Delete" @click="removePart(dIdx, $index)" />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 备注信息 -->
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="备注信息" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 详情对话框 ==================== -->
    <el-dialog
      v-model="detailDialogVisible"
      title="接件详情"
      width="1200px"
      top="2vh"
    >
      <div v-loading="detailLoading" class="detail-layout">
        <!-- 左侧主内容区 -->
        <div class="detail-main" style="flex: 1; max-height: 70vh; overflow-y: auto; padding-right: 15px;">
          <!-- 基本信息 -->
          <el-divider content-position="left">基本信息</el-divider>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="接件单号">{{ detailData.receive_no }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(detailData.status)">{{ getStatusText(detailData.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="客户名称">{{ detailData.customer_name }}</el-descriptions-item>
            <el-descriptions-item label="联系电话">{{ detailData.customer_phone }}</el-descriptions-item>
            <el-descriptions-item label="客户地址" :span="2">{{ detailData.customer_address || '无' }}</el-descriptions-item>
            <el-descriptions-item label="接待员工">{{ detailData.reception_user_name || detailData.receiver_name || '未分配' }}</el-descriptions-item>
            <el-descriptions-item label="维修工程师">{{ detailData.engineer_user_name || detailData.engineer_name || '未分配' }}</el-descriptions-item>
            <el-descriptions-item label="接件时间">{{ detailData.created_at }}</el-descriptions-item>
            <el-descriptions-item label="完成时间">{{ detailData.completed_at || '未完成' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 流程进度条 -->
          <el-divider content-position="left">流程进度</el-divider>
          <el-steps :active="getStepActive(detailData.status)" align-center finish-status="success">
            <el-step title="已登记" />
            <el-step title="检测" />
            <el-step title="报价" />
            <el-step title="客户确认" />
            <el-step title="领料" />
            <el-step title="维修" />
            <el-step title="测试" />
            <el-step title="取件" />
            <el-step title="完成" />
          </el-steps>
          <div v-if="isExternalFlow(detailData.status)" style="margin-top: 16px;">
            <el-alert title="当前为外店维修流程" type="warning" :closable="false" show-icon />
          </div>

          <!-- 设备信息 -->
          <el-divider content-position="left">设备信息</el-divider>
          <el-table :data="detailData.devices || []" border size="small" style="width: 100%">
            <el-table-column type="index" label="#" width="50" align="center" />
            <el-table-column prop="device_type" label="设备类型" width="100" />
            <el-table-column prop="device_name" label="设备名称" width="120" />
            <el-table-column prop="device_brand" label="品牌" width="100" />
            <el-table-column prop="device_model" label="型号" width="100" />
            <el-table-column prop="device_sn" label="序列号" width="140" />
            <el-table-column prop="fault_desc" label="故障描述" min-width="150" show-overflow-tooltip />
            <el-table-column prop="appearance_desc" label="外观描述" min-width="150" show-overflow-tooltip />
          </el-table>
          <el-empty v-if="!detailData.devices || !detailData.devices.length" description="暂无设备信息" :image-size="40" />

          <!-- 配件明细（分栏显示：客户自带附件 vs 维修领用配件） -->
          <el-divider content-position="left">配件明细</el-divider>
          <el-row :gutter="20">
            <!-- 左栏：客户自带附件（来自设备登记，仅登记留底，不进库存和结算） -->
            <el-col :span="12">
              <div style="border: 1px solid #e4e7ed; border-radius: 4px; padding: 10px; background: #fafafa;">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                  <span style="font-weight: bold; color: #606266;">客户自带附件</span>
                  <el-tag type="info" size="small" style="margin-left: 10px;">仅登记留底，不进库存和结算</el-tag>
                </div>
                <template v-if="getCustomerAccessories(detailData).length > 0">
                  <el-table :data="getCustomerAccessories(detailData)" size="small" border>
                    <el-table-column type="index" label="#" width="40" align="center" />
                    <el-table-column prop="name" label="附件名称" min-width="80" />
                    <el-table-column prop="quantity" label="数量" width="60" align="center" />
                    <el-table-column prop="status" label="状态" width="70" align="center">
                      <template #default="{ row }">
                        <el-tag :type="row.status === '完好' ? 'success' : row.status === '损坏' ? 'danger' : 'info'" size="small">{{ row.status }}</el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </template>
                <el-empty v-else description="暂无" :image-size="30" />
              </div>
            </el-col>
            <!-- 右栏：维修领用配件（关联领料、扣库、结算） -->
            <el-col :span="12">
              <div style="border: 1px solid #e4e7ed; border-radius: 4px; padding: 10px; background: #fff;">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                  <span style="font-weight: bold; color: #409eff;">维修领用配件</span>
                  <el-tag type="success" size="small" style="margin-left: 10px;">关联领料、扣库、结算</el-tag>
                </div>
                <template v-if="detailData.parts && detailData.parts.length > 0">
                  <el-table :data="detailData.parts" size="small" border>
                    <el-table-column type="index" label="#" width="40" align="center" />
                    <el-table-column prop="product_name" label="配件名称" min-width="80" />
                    <el-table-column prop="quantity" label="数量" width="60" align="center" />
                    <el-table-column prop="status" label="状态" width="70" align="center">
                      <template #default="{ row }">
                        <el-tag :type="row.status == 1 ? 'success' : row.status == 0 ? 'warning' : 'info'" size="small">{{ row.status == 1 ? '已领' : row.status == 0 ? '待领' : '已退' }}</el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </template>
                <el-empty v-else description="暂无" :image-size="30" />
              </div>
            </el-col>
          </el-row>

          <!-- 检测信息（状态>=1时显示） -->
          <template v-if="detailData.status >= 1 && detailData.detect_result">
            <el-divider content-position="left">检测信息</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="检测结果" :span="2">{{ detailData.detect_result }}</el-descriptions-item>
              <el-descriptions-item label="故障原因" :span="2">{{ detailData.detect_fault_reason || '无' }}</el-descriptions-item>
              <el-descriptions-item label="维修方案" :span="2">{{ detailData.detect_repair_plan || '无' }}</el-descriptions-item>
              <el-descriptions-item label="能否自修">{{ detailData.can_repair == 1 ? '可以自修' : '需送外店' }}</el-descriptions-item>
              <el-descriptions-item label="预估配件">{{ detailData.detect_parts || '无' }}</el-descriptions-item>
            </el-descriptions>
          </template>

          <!-- 报价信息（状态>=2时显示） -->
          <template v-if="detailData.status >= 2 && (detailData.quote_labor_cost || detailData.labor_cost)">
            <el-divider content-position="left">报价信息</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="人工费">¥{{ Number(detailData.quote_labor_cost || detailData.labor_cost || 0).toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="材料费">¥{{ Number(detailData.quote_material_cost || detailData.material_cost || 0).toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="其他费用">¥{{ Number(detailData.quote_other_cost || detailData.other_cost || 0).toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="总计">
                <span style="color: #f56c6c; font-weight: bold;">
                  ¥{{ Number(detailData.quote_total || 0).toFixed(2) }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="客户确认状态" v-if="detailData.status >= 3">
                <el-tag :type="detailData.quote_confirmed === 1 ? 'success' : 'danger'" size="small">
                  {{ detailData.quote_confirmed === 1 ? '已确认' : '已拒绝' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="拒绝原因" v-if="detailData.quote_confirmed === 2">{{ detailData.reject_reason || '无' }}</el-descriptions-item>
            </el-descriptions>
            <!-- 报价明细 -->
            <el-table v-if="detailData.quote_items && detailData.quote_items.length" :data="detailData.quote_items" border size="small" style="width: 100%; margin-top: 10px;">
              <el-table-column type="index" label="#" width="50" align="center" />
              <el-table-column prop="product_name" label="配件名称" min-width="120" />
              <el-table-column prop="specification" label="规格" width="100" />
              <el-table-column prop="unit" label="单位" width="70" align="center" />
              <el-table-column prop="quantity" label="数量" width="70" align="center" />
              <el-table-column prop="unit_price" label="单价" width="90" align="right">
                <template #default="{ row }">¥{{ Number(row.unit_price || 0).toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="subtotal" label="小计" width="90" align="right">
                <template #default="{ row }">¥{{ Number(row.subtotal || 0).toFixed(2) }}</template>
              </el-table-column>
            </el-table>
          </template>

          <!-- 外店信息（状态>=9时显示） -->
          <template v-if="detailData.status >= 9 && detailData.external_shop_name">
            <el-divider content-position="left">外店信息</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="外店名称">{{ detailData.external_shop_name }}</el-descriptions-item>
              <el-descriptions-item label="送修原因">{{ detailData.external_repair_reason || '无' }}</el-descriptions-item>
              <el-descriptions-item label="外店报价">¥{{ Number(detailData.external_quote || 0).toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="送修日期">{{ detailData.external_send_date || '无' }}</el-descriptions-item>
              <el-descriptions-item label="取回日期">{{ detailData.external_return_date || '无' }}</el-descriptions-item>
              <el-descriptions-item label="往返次数">{{ detailData.external_round || 0 }}</el-descriptions-item>
            </el-descriptions>
          </template>

          <!-- 完工信息（状态>=6时显示） -->
          <template v-if="detailData.status >= 6 && detailData.finish_report">
            <el-divider content-position="left">完工信息</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="完工报告" :span="2">{{ detailData.finish_report }}</el-descriptions-item>
              <el-descriptions-item label="测试结果" v-if="detailData.test_result !== undefined && detailData.test_result !== null">
                <el-tag :type="detailData.test_result === 1 ? 'success' : 'danger'" size="small">
                  {{ detailData.test_result === 1 ? '通过' : '未通过' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="测试备注" v-if="detailData.test_remark">{{ detailData.test_remark }}</el-descriptions-item>
            </el-descriptions>
            <!-- 完工照片 -->
            <div v-if="Array.isArray(detailData.finish_photos) && detailData.finish_photos.length" style="margin-top: 10px;">
              <span style="font-size: 13px; color: #606266; margin-right: 10px;">完工照片：</span>
              <el-image
                v-for="(photo, idx) in detailData.finish_photos"
                :key="idx"
                :src="photo.url || photo"
                :preview-src-list="(detailData.finish_photos || []).map(p => p.url || p)"
                fit="cover"
                style="width: 80px; height: 80px; margin-right: 8px; border-radius: 4px;"
                :preview-teleported="true"
              />
            </div>
          </template>
        </div>

        <!-- 右侧操作日志区 -->
        <div v-if="logs.length" class="detail-sidebar" style="width: 280px; max-height: 70vh; overflow-y: auto; padding-left: 15px; border-left: 1px solid #e4e7ed;">
          <div style="font-weight: bold; font-size: 14px; margin-bottom: 15px; color: #303133;">操作日志</div>
          <el-timeline>
            <el-timeline-item
              v-for="(log, idx) in logs"
              :key="idx"
              :timestamp="log.created_at"
              placement="top"
            >
              <el-card shadow="never" class="log-card">
                <p><strong>{{ log.action || log.status_text || '状态变更' }}</strong></p>
                <p v-if="log.remark" style="color: #909399; font-size: 13px;">{{ log.remark }}</p>
                <p v-if="log.operator_name" style="color: #909399; font-size: 12px;">操作人：{{ log.operator_name }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>

      <!-- 底部操作按钮区 -->
      <template #footer>
        <div class="detail-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <template v-if="detailData.status === 0">
            <el-button type="warning" @click="handleEditFromDetail">编辑</el-button>
            <el-button type="danger" @click="handleCancel(detailData)">取消</el-button>
            <el-button type="success" @click="openDetectDialog(detailData)">工程师检测</el-button>
          </template>
          <template v-if="detailData.status === 1">
            <el-button type="success" @click="openDetectDialog(detailData)">提交检测结果</el-button>
          </template>
          <template v-if="detailData.status === 2">
            <el-button type="warning" @click="openQuoteDialog(detailData)">生成报价</el-button>
          </template>
          <template v-if="detailData.status === 3">
            <el-button type="success" @click="openConfirmDialog(detailData)">客户确认</el-button>
          </template>
          <template v-if="detailData.status === 4">
            <el-button type="warning" @click="openAllocateDialog(detailData)">领料/采购</el-button>
            <el-button type="info" @click="handleSkipAllocate(detailData)">跳过领料</el-button>
          </template>
          <template v-if="detailData.status === 5">
            <el-button type="success" @click="openFinishDialog(detailData)">提交完工</el-button>
          </template>
          <template v-if="detailData.status === 6">
            <el-button type="warning" @click="openTestDialog(detailData)">测试设备</el-button>
          </template>
          <template v-if="detailData.status === 7">
            <el-button type="success" @click="openNotifyDialog(detailData)">通知取件</el-button>
            <el-button type="warning" @click="openSettleDialog(detailData)">完工结算</el-button>
          </template>
          <template v-if="detailData.status === 8">
            <el-button type="primary" @click="handleComplete(detailData)">取件完成</el-button>
          </template>
          <template v-if="detailData.status === 10">
            <el-button type="warning" @click="openExternalQuoteDialog(detailData)">外店报价</el-button>
          </template>
          <template v-if="detailData.status === 11">
            <el-button type="warning" @click="openCustomerQuoteDialog(detailData)">给客户报价</el-button>
          </template>
          <template v-if="detailData.status === 12">
            <el-button type="success" @click="handleExternalConfirm(detailData)">确认送修</el-button>
          </template>
          <template v-if="detailData.status === 13">
            <el-button type="warning" @click="openExternalReturnDialog(detailData)">取回设备</el-button>
          </template>
          <template v-if="detailData.status === 14">
            <el-button type="warning" @click="openTestDialog(detailData)">测试设备</el-button>
          </template>
        </div>
      </template>
    </el-dialog>

    <!-- ==================== 工程师检测对话框 ==================== -->
    <el-dialog v-model="detectDialogVisible" title="工程师检测" width="650px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="detectForm" label-width="100px">
        <el-form-item label="检测结果">
          <el-input v-model="detectForm.detect_result" type="textarea" :rows="3" placeholder="请输入检测结果" />
        </el-form-item>
        <el-form-item label="故障原因">
          <el-input v-model="detectForm.detect_fault_reason" type="textarea" :rows="3" placeholder="请输入故障原因" />
        </el-form-item>
        <el-form-item label="维修方案">
          <el-input v-model="detectForm.detect_repair_plan" type="textarea" :rows="3" placeholder="请输入维修方案" />
        </el-form-item>
        <el-form-item label="能否自修">
          <el-radio-group v-model="detectForm.can_repair">
            <el-radio label="1">可以自修</el-radio>
            <el-radio label="0">需送外店</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="预估配件">
          <el-input v-model="detectForm.detect_parts" type="textarea" :rows="2" placeholder="请输入预估需要的配件" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="detectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDetect" :loading="actionLoading">提交</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 报价对话框 ==================== -->
    <el-dialog v-model="quoteDialogVisible" title="生成报价" width="750px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="quoteForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="人工费">
              <el-input-number v-model="quoteForm.labor_cost" :min="0" :precision="2" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="材料费">
              <el-input-number v-model="quoteForm.material_cost" :min="0" :precision="2" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="其他费用">
              <el-input-number v-model="quoteForm.other_cost" :min="0" :precision="2" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="总计">
          <span style="color: #f56c6c; font-weight: bold; font-size: 16px;">
            ¥{{ quoteTotal.toFixed(2) }}
          </span>
        </el-form-item>
        <el-divider content-position="left">
          配件明细
          <el-button type="primary" link size="small" :icon="Plus" @click="addQuoteItem" style="margin-left: 10px">添加配件</el-button>
        </el-divider>
        <el-table :data="quoteForm.items" border size="small" style="width: 100%">
          <el-table-column type="index" label="#" width="50" align="center" />
          <el-table-column label="配件名称" min-width="100">
            <template #default="{ row }">
              <el-input v-model="row.product_name" size="small" placeholder="配件名称" />
            </template>
          </el-table-column>
          <el-table-column label="规格" width="80">
            <template #default="{ row }">
              <el-input v-model="row.specification" size="small" placeholder="规格" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100" align="center">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" style="width: 90px" @change="calcQuoteItemSubtotal(row)" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="60" align="center">
            <template #default="{ row }">
              <el-input v-model="row.unit" size="small" placeholder="单位" style="text-align: center" />
            </template>
          </el-table-column>
          <el-table-column label="库存" width="60" align="center">
            <template #default="{ row }">
              <span :style="{ color: (row.current_stock || 0) < (row.quantity || 0) ? '#f56c6c' : '#67c23a', fontSize: '12px' }">{{ row.current_stock || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="100" align="right">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" controls-position="right" style="width: 90px" @change="calcQuoteItemSubtotal(row)" />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="80" align="right">
            <template #default="{ row }">
              <span>¥{{ (row.subtotal || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row, $index }">
              <el-button type="primary" link size="small" @click="openQuoteProductSelector($index)">选配件</el-button>
              <el-button type="danger" link size="small" :icon="Delete" @click="quoteForm.items.splice($index, 1)" />
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="quoteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitQuote" :loading="actionLoading">提交报价</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 客户确认对话框 ==================== -->
    <el-dialog v-model="confirmDialogVisible" title="客户确认/拒绝" width="600px" destroy-on-close :close-on-click-modal="false">
      <el-descriptions :column="1" border style="margin-bottom: 20px;">
        <el-descriptions-item label="人工费">¥{{ Number(currentActionOrder.quote_labor_cost || currentActionOrder.labor_cost || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="材料费">¥{{ Number(currentActionOrder.quote_material_cost || currentActionOrder.material_cost || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="其他费用">¥{{ Number(currentActionOrder.quote_other_cost || currentActionOrder.other_cost || 0).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="总计">
          <span style="color: #f56c6c; font-weight: bold;">
            ¥{{ (Number(currentActionOrder.quote_total || currentActionOrder.total_cost || currentActionOrder.total_amount || 0)).toFixed(2) }}
          </span>
        </el-descriptions-item>
      </el-descriptions>
      <el-form :model="confirmForm" label-width="100px">
        <el-form-item label="确认结果">
          <el-radio-group v-model="confirmForm.confirmed">
            <el-radio label="1">客户确认</el-radio>
            <el-radio label="2">客户拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="拒绝原因" v-if="confirmForm.confirmed === '2'">
          <el-input v-model="confirmForm.reject_reason" type="textarea" :rows="3" placeholder="请输入拒绝原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="confirmDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitConfirm" :loading="actionLoading">提交</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 领料对话框 ==================== -->
    <el-dialog v-model="allocateDialogVisible" title="领料/采购" width="750px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="allocateForm" label-width="100px">
        <!-- 报价清单（来自生成报价时的配件清单） -->
        <template v-if="allocateForm.items.some(item => item.from_quote)">
          <el-divider content-position="left">
            <span style="color: #409eff; font-weight: bold;">报价清单</span>
            <el-tag type="info" size="small" style="margin-left: 10px;">勾选确认要领用的配件</el-tag>
          </el-divider>
          <el-table :data="allocateForm.items.filter(item => item.from_quote)" border size="small" style="width: 100%; margin-bottom: 15px;">
            <el-table-column label="勾选" width="55" align="center">
              <template #default="{ row }">
                <el-checkbox v-model="row.selected" />
              </template>
            </el-table-column>
            <el-table-column label="配件名称" min-width="120">
              <template #default="{ row }">
                <span>{{ row.product_name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="规格" width="100">
              <template #default="{ row }">
                <span>{{ row.specification || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="报价数量" width="90" align="center">
              <template #default="{ row }">
                <span>{{ row.quantity }}</span>
              </template>
            </el-table-column>
            <el-table-column label="实际领用" width="120" align="center">
              <template #default="{ row }">
                <el-input-number v-model="row.allocate_quantity" :min="0" :max="row.quantity" size="small" controls-position="right" style="width: 100px" :disabled="!row.selected" />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.selected" type="success" size="small">已选</el-tag>
                <el-tag v-else type="info" size="small">未选</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </template>
        
        <!-- 额外添加的配件 -->
        <el-divider content-position="left">
          <span>额外配件</span>
          <el-button type="primary" link size="small" :icon="Plus" @click="addAllocateItem" style="margin-left: 10px">添加配件</el-button>
        </el-divider>
        <el-table :data="allocateForm.items.filter(item => !item.from_quote)" border size="small" style="width: 100%">
          <el-table-column label="选择商品" min-width="180">
            <template #default="{ row }">
              <el-select v-model="row.product_id" placeholder="搜索选择商品" filterable remote :remote-method="(q) => searchProduct(q, row)" style="width: 100%" @change="onProductSelect(row)">
                <el-option v-for="p in productList" :key="p.id" :label="p.product_name" :value="p.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="120" align="center">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" size="small" controls-position="right" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="库存数量" width="100" align="center">
            <template #default="{ row }">
              <span :style="{ color: (row.stock_quantity || 0) < row.quantity ? '#f56c6c' : '#67c23a' }">
                {{ row.stock_quantity || 0 }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" :icon="Delete" @click="allocateForm.items.splice($index, 1)" />
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="allocateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAllocate" :loading="actionLoading">确认领料</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 完工对话框 ==================== -->
    <el-dialog v-model="finishDialogVisible" title="提交完工" width="650px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="finishForm" label-width="100px">
        <el-form-item label="完工报告">
          <el-input v-model="finishForm.finish_report" type="textarea" :rows="4" placeholder="请输入完工报告" />
        </el-form-item>
        <el-form-item label="完工照片">
          <el-upload
            :action="uploadAction"
            :headers="uploadHeaders"
            list-type="picture-card"
            :limit="9"
            :on-success="onFinishPhotoSuccess"
            :file-list="finishPhotoList"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="finishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFinish" :loading="actionLoading">提交完工</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 测试对话框 ==================== -->
    <el-dialog v-model="testDialogVisible" title="测试设备" width="500px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="testForm" label-width="100px">
        <el-form-item label="测试结果">
          <el-radio-group v-model="testForm.test_result">
            <el-radio label="1">通过</el-radio>
            <el-radio label="2">未通过</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="测试备注">
          <el-input v-model="testForm.test_remark" type="textarea" :rows="3" placeholder="请输入测试备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTest" :loading="actionLoading">提交</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 通知取件对话框 ==================== -->
    <el-dialog v-model="notifyDialogVisible" title="通知取件" width="450px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="notifyForm" label-width="100px">
        <el-form-item label="通知方式">
          <el-radio-group v-model="notifyForm.notify_method">
            <el-radio label="sms">短信</el-radio>
            <el-radio label="wechat">微信</el-radio>
            <el-radio label="phone">电话</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="notifyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitNotify" :loading="actionLoading">发送通知</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 完工结算对话框 ==================== -->
    <el-dialog v-model="settleDialogVisible" title="完工结算" width="750px" destroy-on-close :close-on-click-modal="false">
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
        <el-button type="primary" @click="submitSettle" :loading="actionLoading">确认结算</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 送修外店对话框 ==================== -->
    <el-dialog v-model="externalSendDialogVisible" title="送修外店" width="550px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="externalSendForm" label-width="100px">
        <el-form-item label="选择外店">
          <el-select v-model="externalSendForm.external_shop_id" placeholder="选择外店" filterable style="width: 100%">
            <el-option v-for="s in externalShopList" :key="s.id" :label="s.supplier_name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="送修原因">
          <el-input v-model="externalSendForm.external_repair_reason" type="textarea" :rows="3" placeholder="请输入送修原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="externalSendDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitExternalSend" :loading="actionLoading">确认送修</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 外店报价对话框 ==================== -->
    <el-dialog v-model="externalQuoteDialogVisible" title="外店报价" width="450px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="externalQuoteForm" label-width="100px">
        <el-form-item label="外店报价">
          <el-input-number v-model="externalQuoteForm.external_quote" :min="0" :precision="2" controls-position="right" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="externalQuoteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitExternalQuote" :loading="actionLoading">提交</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 给客户报价对话框 ==================== -->
    <el-dialog v-model="customerQuoteDialogVisible" title="给客户报价" width="500px" :close-on-click-modal="false">
      <el-form label-width="100px">
        <el-form-item label="人工费">
          <el-input v-model="customerQuoteForm.labor_cost" placeholder="请输入人工费" type="number" />
        </el-form-item>
        <el-form-item label="材料费">
          <el-input v-model="customerQuoteForm.material_cost" placeholder="请输入材料费" type="number" />
        </el-form-item>
        <el-form-item label="其他费用">
          <el-input v-model="customerQuoteForm.other_cost" placeholder="请输入其他费用" type="number" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customerQuoteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCustomerQuote" :loading="actionLoading">提交</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 报价配件选择对话框（关联库存） ==================== -->
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

    <!-- ==================== 取回设备对话框 ==================== -->
    <el-dialog v-model="externalReturnDialogVisible" title="取回设备" width="450px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="externalReturnForm" label-width="100px">
        <el-form-item label="取回日期">
          <el-date-picker v-model="externalReturnForm.external_return_date" type="date" placeholder="选择取回日期" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="externalReturnDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitExternalReturn" :loading="actionLoading">确认取回</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 取消对话框 ==================== -->
    <el-dialog v-model="cancelDialogVisible" title="取消接件单" width="500px" destroy-on-close :close-on-click-modal="false">
      <el-form :model="cancelForm" label-width="100px">
        <el-form-item label="取消原因">
          <el-input v-model="cancelForm.reason" type="textarea" :rows="3" placeholder="请输入取消原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">暂不取消</el-button>
        <el-button type="danger" @click="submitCancel" :loading="actionLoading">确认取消</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 统一打印对话框 ==================== -->
    <!-- 客户联打印 -->
    <PrintDialog
      v-model:visible="printDialogVisible"
      :template-type="printTemplateType"
      :print-data="printData"
    />

    <!-- 设备标签/客户自带标签打印（统一使用PrintDialog） -->
    <PrintDialog
      v-model:visible="labelPrintVisible"
      :template-type="labelPrintType"
      :print-mode="'label'"
      :label-type="labelPrintType === 'device_label' ? 'device' : 'customer'"
      :label-data="labelPrintList"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Delete, Printer, Ticket, PriceTag, Download, ArrowDown } from '@element-plus/icons-vue'
import PrintDialog from '@/components/PrintDialog.vue'
import { useUserStore } from '@/stores/user'
import {
  getReceiveList, getReceiveDetail, createReceive, updateReceive,
  detectReceive, quoteReceive, confirmReceive, allocateReceive,
  finishReceive, testReceive, notifyReceive, completeReceive, cancelReceive,
  externalSendReceive, externalQuoteReceive, customerQuoteReceive,
  externalConfirmReceive, externalReturnReceive, externalRetestReceive,
  getReceiveLogs
} from '@/api/receive'
import { getCustomerList } from '@/api/customer'
import { getUserList } from '@/api/user'
import { getSupplierList } from '@/api/supplier'
import { getProductList } from '@/api/product'
import { getStockList } from '@/api/inventory'

// ==================== 状态映射 ====================
const statusMap = {
  0: '已登记',
  1: '检测中',
  2: '待报价',
  3: '待客户确认',
  4: '待领料/采购',
  5: '维修中',
  6: '待测试',
  7: '待取件',
  8: '待结算',
  9: '已完成',
  10: '送修外店',
  11: '外店已报价',
  12: '待外店维修',
  13: '外店维修中',
  14: '外店取回待测试',
  15: '已取消'
}

/** 获取状态文本 */
const getStatusText = (status) => statusMap[status] || '未知'

/** 获取状态tag颜色类型 */
const getStatusType = (status) => {
  const types = {
    0: 'info',     // 已登记
    1: 'warning',  // 检测中
    2: 'warning',  // 待报价
    3: 'danger',   // 待客户确认
    4: 'warning',  // 待领料/采购
    5: 'primary',  // 维修中
    6: 'warning',  // 待测试
    7: 'success',  // 待取件
    8: 'warning',  // 待结算
    9: 'success',  // 已完成
    10: 'danger',   // 送修外店
    11: 'warning', // 外店已报价
    12: 'warning', // 待外店维修
    13: 'primary', // 外店维修中
    14: 'warning', // 外店取回待测试
    15: 'info'     // 已取消
  }
  return types[status] || 'info'
}

/** 判断是否为外店流程 */
const isExternalFlow = (status) => status >= 9 && status <= 13

/** 获取步骤条激活位置 */
const getStepActive = (status) => {
  if (status === 14) return -1 // 已取消
  if (isExternalFlow(status)) return 1 // 外店流程特殊显示
  const stepMap = { 0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8 }
  return stepMap[status] !== undefined ? stepMap[status] : 0
}

/** 判断是否可以编辑 */
const canEdit = (status) => status === 0

/** 判断是否可以取消 */
const canCancel = (status) => status !== 8 && status !== 14

// ==================== 设备类型选项 ====================
const deviceTypeOptions = ['电脑', '打印机', '监控设备', '网络设备', '其他']

// ==================== 列表数据 ====================
const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  keyword: '',
  status: null,
  dateRange: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

/** 获取列表数据 */
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword || undefined,
      status: searchForm.status !== null && searchForm.status !== '' ? searchForm.status : undefined
    }
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.date_start = searchForm.dateRange[0]
      params.date_end = searchForm.dateRange[1]
    }
    const res = await getReceiveList(params)
    tableData.value = res.data.list || res.data || []
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('获取接件列表失败:', error)
  } finally {
    loading.value = false
  }
}

/** 重置搜索 */
const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.status = null
  searchForm.dateRange = null
  pagination.page = 1
  fetchData()
}

/** 导出接件单 */
const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.status != null) params.append('status', searchForm.status)
  if (searchForm.dateRange?.[0]) params.append('date_start', searchForm.dateRange[0])
  if (searchForm.dateRange?.[1]) params.append('date_end', searchForm.dateRange[1])
  const token = localStorage.getItem('token') || ''
  window.open(`/api/receiveorders/export?${params.toString()}&token=${token}`, '_blank')
}

// ==================== 基础数据（客户、员工、供应商、商品） ====================
const userList = ref([])
const externalShopList = ref([])
const productList = ref([])

/** 加载员工列表 */
const loadUsers = async () => {
  try {
    const res = await getUserList({ page_size: 200 })
    userList.value = res.data.list || res.data || []
  } catch (e) {
    console.error('加载员工列表失败:', e)
  }
}

/** 加载外店列表（维修合作伙伴） */
const loadExternalShops = async () => {
  try {
    const res = await getSupplierList({ is_repair_partner: 1, page_size: 200 })
    externalShopList.value = res.data.list || res.data || []
  } catch (e) {
    console.error('加载外店列表失败:', e)
  }
}

/** 搜索商品 */
const searchProduct = async (keyword, row) => {
  if (!keyword) return
  try {
    const res = await getProductList({ keyword, page_size: 20 })
    productList.value = res.data.list || res.data || []
  } catch (e) {
    console.error('搜索商品失败:', e)
  }
}

/** 选择商品后查询库存 */
const onProductSelect = async (row) => {
  if (!row.product_id) return
  try {
    const res = await getStockList({ product_id: row.product_id, page_size: 1 })
    const stockList = res.data.list || res.data || []
    // 使用 available_quantity（可用库存）而不是 quantity（总库存）
    row.stock_quantity = stockList.length > 0 ? (stockList[0].available_quantity || 0) : 0
  } catch (e) {
    row.stock_quantity = 0
  }
}

// ==================== 新增/编辑对话框 ====================
const formDialogVisible = ref(false)
const formDialogTitle = ref('新增接件')
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const editId = ref(null)

/** 创建默认设备对象 */
const createDefaultDevice = () => ({
  device_type: '',
  device_name: '',
  brand: '',
  model: '',
  serial_number: '',
  cpu: '', memory: '', hard_disk: '', os: '', os_version: '',
  toner_model: '', cartridge_model: '',
  monitor_brand: '', camera_count: 0,
  port_count: 0, ip_address: '', firmware_version: '',
  appearance_desc: '',
  parts: []
})

/** 获取默认表单数据 */
const getDefaultFormData = () => ({
  customer_id: null,
  customer_name: '',
  customer_phone: '',
  customer_address: '',
  reception_user_id: null,
  engineer_user_id: null,
  devices: [createDefaultDevice()],
  remark: ''
})

const formData = reactive(getDefaultFormData())

const formRules = {
  customer_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  customer_phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
  reception_user_id: [{ required: true, message: '请选择接待员工', trigger: 'change' }]
}

/** 客户搜索（autocomplete） */
const searchCustomer = async (queryString, cb) => {
  if (!queryString) { cb([]); return }
  try {
    const res = await getCustomerList({ keyword: queryString, page_size: 10 })
    const results = (res.data.list || res.data || []).map(c => ({
      value: c.customer_name,
      id: c.id,
      phone: c.phone,
      address: c.address
    }))
    cb(results)
  } catch (error) { cb([]) }
}

/** 选中客户 */
const onCustomerSelect = (item) => {
  formData.customer_id = item.id
  formData.customer_name = item.value
  if (item.phone) formData.customer_phone = item.phone
  if (item.address) formData.customer_address = item.address
}

/** 添加设备 */
const addDevice = () => {
  formData.devices.push(createDefaultDevice())
}

/** 删除设备 */
const removeDevice = (index) => {
  formData.devices.splice(index, 1)
}

/** 添加配件 */
const addPart = (deviceIndex) => {
  formData.devices[deviceIndex].parts.push({ name: '', quantity: 1, status: '完好', remark: '' })
}

/** 删除配件 */
const removePart = (deviceIndex, partIndex) => {
  formData.devices[deviceIndex].parts.splice(partIndex, 1)
}

/** 打开新增对话框 */
const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  formDialogTitle.value = '新增接件'
  Object.assign(formData, getDefaultFormData())
  formDialogVisible.value = true
}

/** 打开编辑对话框 */
const handleEdit = async (row) => {
  try {
    const res = await getReceiveDetail(row.id)
    const detail = res.data
    isEdit.value = true
    editId.value = detail.id
    formDialogTitle.value = '编辑接件'

    // 将顶层配件按设备ID分组
    const partsMap = {}
    if (detail.parts && detail.parts.length) {
      detail.parts.forEach(p => {
        const key = p.receive_order_id || 'default'
        if (!partsMap[key]) partsMap[key] = []
        partsMap[key].push(p)
      })
    }

    // 映射设备字段名（后端 -> 前端）
    const mapDevice = (d) => ({
      id: d.id,
      device_type: d.device_type || '',
      device_name: d.device_name || '',
      brand: d.device_brand || d.brand || '',
      model: d.device_model || d.model || '',
      serial_number: d.device_sn || d.serial_number || '',
      cpu: d.cpu || '',
      memory: d.memory || '',
      hard_disk: d.disk || d.hard_disk || '',
      os: d.os || '',
      os_version: d.os_version || '',
      toner_model: d.toner_model || '',
      cartridge_model: d.drum_model || d.cartridge_model || '',
      monitor_brand: d.monitor_brand || '',
      camera_count: d.camera_count || '',
      port_count: d.port_count || '',
      ip_address: d.ip_address || '',
      firmware_version: d.firmware_version || '',
      appearance_desc: d.appearance_desc || '',
      parts: []
    })

    const devices = (detail.devices && detail.devices.length)
      ? detail.devices.map(mapDevice)
      : [createDefaultDevice()]

    // 将配件分配到对应设备
    if (detail.parts && detail.parts.length) {
      // 状态映射：数字 -> 字符串（与el-select的value对应）
      const statusNumToStr = { 0: '完好', 1: '损坏', 2: '缺失' }
      // 如果配件有 device_id 或关联到设备
      detail.parts.forEach(p => {
        const dev = devices.find(d => d.id === p.device_id)
        if (dev) {
          dev.parts.push({
            name: p.product_name || '',
            quantity: p.quantity || 0,
            status: typeof p.status === 'number' ? (statusNumToStr[p.status] || '完好') : (p.status || '完好'),
            remark: p.remark || ''
          })
        }
      })
    }

    Object.assign(formData, {
      customer_id: detail.customer_id || null,
      customer_name: detail.customer_name || '',
      customer_phone: detail.customer_phone || '',
      customer_address: detail.customer_address || '',
      reception_user_id: (detail.receiver_id || detail.reception_user_id) ? Number(detail.receiver_id || detail.reception_user_id) : null,
      engineer_user_id: (detail.engineer_id || detail.engineer_user_id) ? Number(detail.engineer_id || detail.engineer_user_id) : null,
      devices: devices,
      remark: detail.remark || ''
    })

    // 确保每个设备都有 parts 数组
    formData.devices.forEach(d => {
      if (!d.parts) d.parts = []
    })
    formDialogVisible.value = true
  } catch (error) {
    console.error('获取接件详情失败:', error)
  }
}

/** 提交表单 */
const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      const payload = { ...formData }
      // 转换配件 status 字段：字符串 -> 数字
      const statusMap = { '完好': 0, '损坏': 1, '缺失': 2 }
      payload.devices = payload.devices.map(device => ({
        ...device,
        parts: (device.parts || []).map(part => ({
          ...part,
          status: typeof part.status === 'string' ? (statusMap[part.status] || 0) : (part.status || 0)
        }))
      }))
      
      // 调试日志
      console.log('[DEBUG] 提交数据:', payload)
      console.log('[DEBUG] devices:', payload.devices)
      payload.devices.forEach((d, i) => {
        console.log(`[DEBUG] 设备 ${i}: parts =`, d.parts)
      })
      // 编辑时，确保 devices 和 parts 都包含在 payload 中
      if (isEdit.value) {
        // 确保 parts 数据正确（从设备的 parts 数组收集）
        const allParts = []
        if (payload.devices && payload.devices.length) {
          payload.devices.forEach(device => {
            if (device.parts && device.parts.length) {
              device.parts.forEach(part => {
                allParts.push(part)
              })
            }
          })
        }
        payload.parts = allParts
      }
      if (isEdit.value) {
        await updateReceive(editId.value, payload)
        ElMessage.success('更新成功')
        printData.value = {
          receive_no: editId.value ? '' : '',
          customer_name: payload.customer_name || '',
          customer_phone: payload.customer_phone || '',
          customer_address: payload.customer_address || '',
          devices: payload.devices || [],
          remark: payload.remark || '',
          created_at: new Date().toLocaleString('zh-CN')
        }
      } else {
        const res = await createReceive(payload)
        ElMessage.success('创建成功')
        // 使用后端返回的接件单号
        printData.value = {
          receive_no: res.data?.receive_no || '',
          customer_name: payload.customer_name || '',
          customer_phone: payload.customer_phone || '',
          customer_address: payload.customer_address || '',
          devices: payload.devices || [],
          remark: payload.remark || '',
          created_at: new Date().toLocaleString('zh-CN')
        }
      }
      formDialogVisible.value = false
      fetchData()
      printDialogVisible.value = true
    } catch (error) {
      // 错误已在拦截器中处理
    } finally {
      submitLoading.value = false
    }
  })
}

// ==================== 打印功能（统一接入PrintDialog） ====================
const printDialogVisible = ref(false)
const printData = ref({})
const printTemplateType = ref('receive')

/** 列表补打 */
const handleRePrint = async (row) => {
  try {
    const res = await getReceiveDetail(row.id)
    if (res.code === 200 && res.data) {
      const d = res.data
      const devices = d.devices || []
      const parts = d.parts || []
      
      // 由于数据库中配件没有 device_id 字段，
      // 将所有配件分配给第一个设备（或按顺序分配）
      if (devices.length > 0 && parts.length > 0) {
        // 简单策略：所有配件都归到第一个设备
        devices[0].parts = parts.map(p => ({
          name: p.part_name || p.name || '',
          quantity: p.quantity || 0,
          status: p.status ?? 0,
          remark: p.remark || ''
        }))
        // 其他设备配件为空
        for (let i = 1; i < devices.length; i++) {
          devices[i].parts = []
        }
      }
      
      printTemplateType.value = 'receive'
      printData.value = {
        receive_no: d.receive_no || '',
        customer_name: d.customer_name || '',
        customer_phone: d.customer_phone || '',
        customer_address: d.customer_address || '',
        devices: devices,
        fault_desc: d.fault_desc || '',
        remark: d.remark || '',
        created_at: d.created_at || ''
      }
      printDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('获取接件单详情失败')
  }
}

// ==================== 标签打印功能（统一接入LabelPrintDialog） ====================
const labelPrintVisible = ref(false)
const labelPrintType = ref('')
const labelPrintList = ref([])

const handleLabelPrint = async (templateType, row) => {
  try {
    const res = await getReceiveDetail(row.id)
    if (res.code === 200 && res.data) {
      const d = res.data
      const devices = d.devices || []

      if (templateType === 'device_label') {
        // 设备标签：为每个设备生成一个标签
        labelPrintList.value = devices.map(device => ({
          product_name: (device.device_brand || '') + ' ' + (device.device_model || ''),
          device_name: (device.device_brand || '') + ' ' + (device.device_model || ''),
          name: (device.device_brand || '') + ' ' + (device.device_model || ''),
          barcode: device.device_sn || d.receive_no || '',
          product_code: d.receive_no || '',
          code: device.device_sn || d.receive_no || '',
          specification: device.device_type || '',
          spec: device.device_type || '',
          model: device.device_model || '',
          sale_price: '',
          price: ''
        }))
        labelPrintType.value = 'device_label'
      } else if (templateType === 'customer_label') {
        // 客户自带标签：数据字段匹配后端模板变量
        labelPrintList.value = [{
          receive_no: d.receive_no || '',
          customer_name: d.customer_name || '',
          customer_phone: d.customer_phone || '',
          item_name: devices[0] ? ((devices[0].device_brand || '') + ' ' + (devices[0].device_model || '')) : '',
          receive_date: d.created_at || d.receive_date || '',
          // 同时提供备用字段
          product_name: devices[0] ? ((devices[0].device_brand || '') + ' ' + (devices[0].device_model || '')) : '',
          barcode: d.receive_no || '',
          specification: (devices[0] && devices[0].accessories) || d.accessories || '',
          product_code: d.receive_no || ''
        }]
        labelPrintType.value = 'customer_label'
      }

      labelPrintVisible.value = true
    }
  } catch (error) {
    ElMessage.error('获取接件单详情失败')
  }
}

/** 获取标签纸页面样式 - 三种尺寸自适应 */
const getLabelPageStyle = (size) => {
  const sizeMap = {
    '30x20': { w: '30mm', h: '20mm', font: '7pt', pad: '1.5mm', line: '1.1' },
    '40x30': { w: '40mm', h: '30mm', font: '8pt', pad: '2mm', line: '1.2' },
    '60x40': { w: '60mm', h: '40mm', font: '9pt', pad: '2.5mm', line: '1.3' }
  }
  const s = sizeMap[size] || sizeMap['60x40']
  return `
    @page { size: ${s.w} ${s.h}; margin: 0; }
    body { font-size: ${s.font}; line-height: ${s.line}; }
    .label { 
      width: ${s.w}; 
      height: ${s.h}; 
      padding: ${s.pad}; 
      display: flex; 
      flex-direction: column;
    }
    .label-title { 
      text-align: center; 
      font-weight: bold; 
      font-size: ${parseInt(s.font) + 1}pt;
      border-bottom: 0.5pt solid #000;
      padding-bottom: 0.5mm;
      margin-bottom: 1mm;
    }
    .label-row { 
      display: flex; 
      margin-bottom: 0.5mm;
      align-items: baseline;
    }
    .label-name { 
      font-weight: bold; 
      min-width: ${size === '30x20' ? '28%' : '25%'};
      text-align: right;
      padding-right: 1mm;
    }
    .label-value { 
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .label-divider { 
      border-top: 0.3pt solid #ccc; 
      margin: 0.5mm 0; 
    }
  `
}

/** 生成维修接件单HTML - A5紧凑排版 */
const generateCustomerReceipt = (data) => {
  const no = data.receive_no || '无'
  
  // 设备表格行
  let deviceRows = ''
  ;(data.devices || []).forEach((d, i) => {
    const brandModel = `${d.brand || ''} ${d.model || ''}`.trim() || '无'
    deviceRows += `<tr>
      <td style="text-align:center">${i + 1}</td>
      <td>${d.device_type || '无'}</td>
      <td>${d.device_name || '无'}</td>
      <td>${brandModel}</td>
      <td style="font-size:7pt">${d.serial_number || '无'}</td>
      <td style="font-size:7pt">${d.fault_desc || '无'}</td>
    </tr>`
  })
  if (!deviceRows) {
    deviceRows = `<tr><td colspan="6" style="text-align:center;color:#999">无设备信息</td></tr>`
  }

  return `<div class="sheet">
    <div class="sheet-header">
      <h1>维修接件单</h1>
      <div class="no">单号：${no}</div>
    </div>
    
    <div class="info-section">
      <div class="section-title">客户信息</div>
      <div class="info-grid">
        <div class="info-row"><span class="info-label">客户姓名：</span><span class="info-value">${data.customer_name || '无'}</span></div>
        <div class="info-row"><span class="info-label">联系电话：</span><span class="info-value">${data.customer_phone || '无'}</span></div>
        <div class="info-row info-full"><span class="info-label">客户地址：</span><span class="info-value">${data.customer_address || '无'}</span></div>
        <div class="info-row"><span class="info-label">接件时间：</span><span class="info-value">${data.created_at || '无'}</span></div>
      </div>
    </div>
    
    <div class="info-section">
      <div class="section-title">故障描述</div>
      <div style="font-size:9pt;min-height:15mm;border:0.5pt solid #000;padding:2mm">${data.fault_desc || '无'}</div>
    </div>
    
    <div class="info-section">
      <div class="section-title">设备清单</div>
      <table>
        <tr><th style="width:8%">#</th><th style="width:15%">类型</th><th style="width:20%">名称</th><th style="width:22%">品牌型号</th><th style="width:20%">序列号</th><th style="width:15%">故障</th></tr>
        ${deviceRows}
      </table>
    </div>
    
    <div class="info-section">
      <div class="section-title">备注</div>
      <div style="font-size:9pt;min-height:10mm;border:0.5pt solid #000;padding:2mm">${data.remark || '无'}</div>
    </div>
    
    <div class="sign-section">
      <div class="sign-item">客户签名：<span class="sign-line"></span></div>
      <div class="sign-item">接待确认：<span class="sign-line"></span></div>
    </div>
    
    <div class="footer">请妥善保管此单，取件时需出示</div>
  </div>`
}

/** 生成设备标签HTML - 单个标签 */
const generateDeviceLabel = (data) => {
  const no = data.receive_no || '无'
  return `<div class="label">
    <div class="label-title">${no}</div>
    <div class="label-row"><span class="label-name">品牌</span><span class="label-value">${data.device_brand || '无'}</span></div>
    <div class="label-divider"></div>
    <div class="label-row"><span class="label-name">型号</span><span class="label-value">${data.device_model || '无'}</span></div>
    <div class="label-divider"></div>
    <div class="label-row"><span class="label-name">SN</span><span class="label-value">${data.device_sn || '无'}</span></div>
    <div class="label-divider"></div>
    <div class="label-row"><span class="label-name">类型</span><span class="label-value">${data.device_type || '无'}</span></div>
  </div>`
}

/** 生成配件标签HTML - 单个标签 */
const generatePartsLabel = (data) => {
  const no = data.receive_no || '无'
  return `<div class="label">
    <div class="label-title">${no}</div>
    <div class="label-row"><span class="label-name">客户</span><span class="label-value">${data.customer_name || '无'}</span></div>
    <div class="label-divider"></div>
    <div class="label-row"><span class="label-name">电话</span><span class="label-value">${data.customer_phone || '无'}</span></div>
    <div class="label-divider"></div>
    <div class="label-row"><span class="label-name">物品</span><span class="label-value">${data.item_name || '无'}</span></div>
    <div class="label-divider"></div>
    <div class="label-row"><span class="label-name">日期</span><span class="label-value">${data.receive_date || '无'}</span></div>
  </div>`
}

/** 执行打印 */
const doPrint = () => {
  const type = printType.value
  const data = printData.value
  const paperSize = printPaperSize.value
  const labelSize = printLabelSize.value
  let printContent = ''
  let printTitle = ''
  let pageStyle = ''

  if (type === 'customer') {
    printTitle = '维修接件单'
    printContent = generateCustomerReceipt(data)
    pageStyle = `@page { size: ${paperSize === 'A4' ? '210mm 297mm' : '148mm 210mm'}; margin: 8mm; }`
  } else if (type === 'device') {
    printTitle = '设备标签'
    printContent = generateDeviceLabel(data)
    pageStyle = getLabelPageStyle(labelSize)
  } else if (type === 'parts') {
    printTitle = '配件标签'
    printContent = generatePartsLabel(data)
    pageStyle = getLabelPageStyle(labelSize)
  }

  const printWindow = window.open('', '_blank', 'width=800,height=600')
  printWindow.document.write(`<!DOCTYPE html>
<html><head><title>${printTitle}</title>
<style>
  ${pageStyle}
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Microsoft YaHei", "SimHei", "PingFang SC", sans-serif; color: #000; line-height: 1.4; }
  ${type === 'customer' ? `
  .sheet { width: 100%; padding: 2mm; }
  .sheet-header { text-align: center; margin-bottom: 4mm; }
  .sheet-header h1 { font-size: 16pt; font-weight: bold; letter-spacing: 2pt; margin-bottom: 2mm; }
  .sheet-header .no { font-size: 9pt; color: #333; }
  .info-section { margin-bottom: 4mm; }
  .section-title { font-size: 10pt; font-weight: bold; border-bottom: 1pt solid #000; padding-bottom: 1mm; margin-bottom: 2mm; }
  .info-grid { display: flex; flex-wrap: wrap; }
  .info-row { width: 50%; display: flex; margin-bottom: 1mm; font-size: 9pt; }
  .info-label { font-weight: bold; min-width: 60px; }
  .info-value { flex: 1; }
  .info-full { width: 100%; }
  table { width: 100%; border-collapse: collapse; font-size: 8pt; margin-bottom: 3mm; }
  th, td { border: 0.5pt solid #000; padding: 2mm 1.5mm; text-align: left; vertical-align: top; }
  th { background: #f5f5f5; font-weight: bold; text-align: center; }
  .sign-section { margin-top: 6mm; display: flex; justify-content: space-between; font-size: 10pt; }
  .sign-item { display: flex; align-items: baseline; }
  .sign-line { display: inline-block; width: 35mm; border-bottom: 0.5pt solid #000; margin-left: 2mm; }
  .footer { text-align: center; font-size: 8pt; color: #666; margin-top: 4mm; border-top: 0.5pt dashed #999; padding-top: 2mm; }
  ` : ''}
</style>
</head><body>${printContent}</body></html>`)
  printWindow.document.close()
  setTimeout(() => { printWindow.print() }, 300)
}

/** 执行标签打印 */
const doLabelPrint = () => {
  const type = labelPrintType.value
  const data = labelPrintData.value
  const labelSize = printLabelSize.value
  let printContent = ''
  let printTitle = ''

  if (type === 'device_label') {
    printTitle = '设备标签'
    printContent = generateDeviceLabel(data)
  } else if (type === 'customer_label') {
    printTitle = '客户自带标签'
    printContent = generatePartsLabel(data)
  }

  const pageStyle = getLabelPageStyle(labelSize)

  const printWindow = window.open('', '_blank', 'width=800,height=600')
  printWindow.document.write(`<!DOCTYPE html>
<html><head><title>${printTitle}</title>
<style>
  ${pageStyle}
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Microsoft YaHei", "SimHei", "PingFang SC", sans-serif; color: #000; line-height: 1.4; }
</style>
</head><body>${printContent}</body></html>`)
  printWindow.document.close()
  setTimeout(() => { printWindow.print() }, 300)
}


const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref({})
const logs = ref([])

/** 获取客户自带附件列表（从设备中提取） */
const getCustomerAccessories = (data) => {
  if (!data || !data.devices) return []
  const accessories = []
  data.devices.forEach(device => {
    if (device.parts && device.parts.length) {
      device.parts.forEach(part => {
        accessories.push({
          name: part.name || part.product_name || '-',
          quantity: part.quantity || 0,
          status: part.status || '完好'
        })
      })
    }
  })
  return accessories
}

/** 打开详情对话框 */
const handleView = async (row) => {
  detailData.value = {}
  logs.value = []
  detailDialogVisible.value = true
  detailLoading.value = true
  try {
    const res = await getReceiveDetail(row.id)
    detailData.value = res.data || {}
    // 加载操作日志
    try {
      const logRes = await getReceiveLogs(row.id)
      logs.value = logRes.data || []
    } catch (e) {
      logs.value = []
    }
  } catch (error) {
    console.error('获取接件详情失败:', error)
    detailData.value = {}
  } finally {
    detailLoading.value = false
  }
}

/** 从详情页打开编辑 */
const handleEditFromDetail = () => {
  detailDialogVisible.value = false
  // detailData.value 已经包含完整数据，直接使用
  const detail = detailData.value
  isEdit.value = true
  editId.value = detail.id
  formDialogTitle.value = '编辑接件'

  // 将配件按设备分组
  const partsMap = {}
  if (detail.parts && detail.parts.length) {
    detail.parts.forEach(p => {
      const key = p.device_id || 'default'
      if (!partsMap[key]) partsMap[key] = []
      partsMap[key].push(p)
    })
  }

  // 映射设备字段名（后端 -> 前端）
  const mapDevice = (d) => {
    const dev = {
      id: d.id,
      device_type: d.device_type || '',
      device_name: d.device_name || '',
      brand: d.device_brand || d.brand || '',
      model: d.device_model || d.model || '',
      serial_number: d.device_sn || d.serial_number || '',
      cpu: d.cpu || '',
      memory: d.memory || '',
      hard_disk: d.disk || d.hard_disk || '',
      os: d.os || '',
      os_version: d.os_version || '',
      toner_model: d.toner_model || '',
      cartridge_model: d.drum_model || d.cartridge_model || '',
      monitor_brand: d.monitor_brand || '',
      camera_count: d.camera_count || '',
      port_count: d.port_count || '',
      ip_address: d.ip_address || '',
      firmware_version: d.firmware_version || '',
      fault_desc: d.fault_desc || '',
      appearance_desc: d.appearance_desc || '',
      parts: partsMap[d.id] ? partsMap[d.id].map(p => ({
        name: p.product_name || '',
        quantity: p.quantity || 0,
        status: p.status || '完好',
        remark: p.remark || ''
      })) : []
    }
    return dev
  }

  const devices = (detail.devices && detail.devices.length)
    ? detail.devices.map(mapDevice)
    : [createDefaultDevice()]

  Object.assign(formData, {
    customer_id: detail.customer_id || null,
    customer_name: detail.customer_name || '',
    customer_phone: detail.customer_phone || '',
    customer_address: detail.customer_address || '',
    reception_user_id: detail.receiver_id || detail.reception_user_id || null,
    engineer_user_id: detail.engineer_id || detail.engineer_user_id || null,
    devices: devices,
    fault_desc: detail.fault_desc || '',
    remark: detail.remark || ''
  })

  // 确保每个设备都有 parts 数组
  formData.devices.forEach(d => {
    if (!d.parts) d.parts = []
  })
  formDialogVisible.value = true
}

// ==================== 通用操作变量 ====================
const actionLoading = ref(false)
const currentActionOrder = ref({})

// ==================== 工程师检测 ====================
const detectDialogVisible = ref(false)
const detectForm = reactive({
  detect_result: '',
  detect_fault_reason: '',
  detect_repair_plan: '',
  can_repair: '1',
  detect_parts: ''
})

const openDetectDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(detectForm, {
    detect_result: '',
    detect_fault_reason: '',
    detect_repair_plan: '',
    can_repair: '1',
    detect_parts: ''
  })
  detectDialogVisible.value = true
}

const submitDetect = async () => {
  actionLoading.value = true
  try {
    await detectReceive(currentActionOrder.value.id, { 
      ...detectForm,
      can_repair: parseInt(detectForm.can_repair)
    })
    ElMessage.success('检测提交成功')
    detectDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 报价 ====================
const quoteDialogVisible = ref(false)
const quoteForm = reactive({
  labor_cost: 0,
  material_cost: 0,
  other_cost: 0,
  items: []
})

const quoteTotal = computed(() => {
  return Number(quoteForm.labor_cost || 0) + Number(quoteForm.material_cost || 0) + Number(quoteForm.other_cost || 0)
})

const addQuoteItem = () => {
  quoteForm.items.push({ product_name: '', specification: '', unit: '', quantity: 1, unit_price: 0, subtotal: 0, current_stock: 0 })
}

const calcQuoteItemSubtotal = (row) => {
  row.subtotal = Number(row.quantity || 0) * Number(row.unit_price || 0)
}

// ==================== 报价配件选择（关联库存） ====================
const quoteProductSelectorVisible = ref(false)
const quoteProductKeyword = ref('')
const quoteProductList = ref([])
const quoteProductLoading = ref(false)
const currentQuoteItemIndex = ref(null)

const openQuoteProductSelector = (index) => {
  currentQuoteItemIndex.value = index
  quoteProductKeyword.value = ''
  quoteProductList.value = []
  quoteProductSelectorVisible.value = true
  fetchQuoteProducts()
}

const fetchQuoteProducts = async () => {
  quoteProductLoading.value = true
  try {
    const res = await getProductList({
      keyword: quoteProductKeyword.value,
      page: 1,
      page_size: 50
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

const selectQuoteProduct = (product) => {
  if (currentQuoteItemIndex.value !== null) {
    const item = quoteForm.items[currentQuoteItemIndex.value]
    item.product_name = product.product_name
    item.specification = product.specification
    item.unit = product.unit_name
    item.unit_price = product.sale_price || 0
    item.current_stock = product.current_stock || 0
    item.quantity = 1
    calcQuoteItemSubtotal(item)
  }
  quoteProductSelectorVisible.value = false
}

const openQuoteDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(quoteForm, { labor_cost: 0, material_cost: 0, other_cost: 0, items: [] })
  quoteDialogVisible.value = true
}

const submitQuote = async () => {
  actionLoading.value = true
  try {
    await quoteReceive(currentActionOrder.value.id, { ...quoteForm })
    ElMessage.success('报价提交成功')
    quoteDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 客户确认 ====================
const confirmDialogVisible = ref(false)
const confirmForm = reactive({
  confirmed: '1',
  reject_reason: ''
})

const openConfirmDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(confirmForm, { confirmed: '1', reject_reason: '' })
  confirmDialogVisible.value = true
}

const submitConfirm = async () => {
  actionLoading.value = true
  try {
    await confirmReceive(currentActionOrder.value.id, {
      confirmed: parseInt(confirmForm.confirmed),
      reject_reason: confirmForm.reject_reason
    })
    ElMessage.success(confirmForm.confirmed === '1' ? '客户已确认' : '已记录拒绝')
    confirmDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 领料 ====================
const allocateDialogVisible = ref(false)
const allocateForm = reactive({ items: [] })

const addAllocateItem = () => {
  allocateForm.items.push({ product_id: null, quantity: 1, stock_quantity: 0, from_quote: false })
}

const openAllocateDialog = async (row) => {
  currentActionOrder.value = row
  allocateForm.items = []
  
  // 获取接件详情，包含报价清单
  try {
    const res = await getReceiveDetail(row.id)
    if (res.code === 200 && res.data) {
      const quoteItems = res.data.quote_items || []
      if (quoteItems.length > 0) {
        // 将报价清单转为领料清单
        allocateForm.items = quoteItems.map(item => ({
          product_id: item.product_id || null,
          product_name: item.product_name || '',
          specification: item.specification || '',
          unit: item.unit || '',
          quantity: parseFloat(item.quantity) || 1,
          allocate_quantity: parseFloat(item.quantity) || 1, // 实际领用数量，默认同报价数量
          unit_price: parseFloat(item.unit_price) || 0,
          stock_quantity: 0,
          from_quote: true, // 标记来自报价
          selected: true // 默认选中
        }))
      }
    }
  } catch (e) {
    console.error('获取报价清单失败:', e)
  }
  
  allocateDialogVisible.value = true
}

const submitAllocate = async () => {
  actionLoading.value = true
  try {
    // 收集选中的报价配件（允许没有product_id，使用名称）
    const quoteItems = allocateForm.items
      .filter(i => i.from_quote && i.selected)
      .map(i => ({
        product_id: i.product_id,
        product_name: i.product_name,
        specification: i.specification,
        quantity: i.allocate_quantity || i.quantity
      }))
    
    // 收集额外添加的配件
    const extraItems = allocateForm.items
      .filter(i => !i.from_quote && i.product_id)
      .map(i => ({
        product_id: i.product_id,
        quantity: i.quantity
      }))
    
    const items = [...quoteItems, ...extraItems]
    
    if (!items.length) {
      ElMessage.warning('请至少选择或添加一项配件')
      actionLoading.value = false
      return
    }
    
    await allocateReceive(currentActionOrder.value.id, { items })
    ElMessage.success('领料成功')
    allocateDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

/** 跳过领料（不需要配件时使用） */
const handleSkipAllocate = async (row) => {
  try {
    await ElMessageBox.confirm('确认不需要领取配件，直接进入维修中？', '跳过领料', {
      confirmButtonText: '确认跳过',
      cancelButtonText: '取消',
      type: 'info'
    })
    actionLoading.value = true
    await request.post(`/receiveorders/${row.id}/status`, {
      status: 5,
      content: '无需领料，直接进入维修中'
    })
    ElMessage.success('已跳过领料')
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(row)
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败')
    }
  } finally {
    actionLoading.value = false
  }
}

// ==================== 完工 ====================
const finishDialogVisible = ref(false)
const finishForm = reactive({ finish_report: '', finish_photos: [] })
const finishPhotoList = ref([])

const userStore = useUserStore()
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))
const uploadAction = computed(() => {
  return `/api/receiveorders/${currentActionOrder.value.id}/finish`
})

const onFinishPhotoSuccess = (res) => {
  if (res.code === 200) {
    ElMessage.success('照片上传成功')
  }
}

const openFinishDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(finishForm, { finish_report: '', finish_photos: [] })
  finishPhotoList.value = []
  finishDialogVisible.value = true
}

const submitFinish = async () => {
  actionLoading.value = true
  try {
    await finishReceive(currentActionOrder.value.id, { ...finishForm })
    ElMessage.success('完工提交成功')
    finishDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 完工结算 ====================
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
const settlePartsList = ref([])
const accountList = ref([])

/** 计算人工费 */
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

/** 结算方式变化 */
const onSettleTypeChange = (val) => {
  if (val === 'cash') {
    settleForm.credit_remark = ''
  } else {
    settleForm.account_id = null
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
    row.used_quantity = 0
  } else {
    row.used_quantity = row.quantity
  }
  calcSettlePartsCost()
}

/** 打开结算对话框 */
const openSettleDialog = async (row) => {
  currentActionOrder.value = row
  settleForm.labor_hours = 0
  settleForm.labor_unit_price = 0
  settleForm.labor_cost_direct = 0
  settleForm.parts_cost = 0
  settleForm.other_cost = 0
  settleForm.account_id = null
  settleForm.settle_type = 'cash'
  settleForm.credit_remark = ''
  settlePartsList.value = []

  // 获取接件详情（包含已领配件列表）
  try {
    const res = await getReceiveDetail(row.id)
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
    console.error('获取接件详情失败', error)
  }

  // 获取账户列表
  try {
    const accRes = await request.get('/finance/accounts')
    if (accRes.code === 200) {
      accountList.value = accRes.data || []
    }
  } catch (error) {
    console.error('获取账户列表失败', error)
  }

  settleDialogVisible.value = true
}

/** 提交结算 */
const submitSettle = async () => {
  if (settleForm.settle_type === 'cash' && !settleForm.account_id) {
    ElMessage.warning('请选择结算账户')
    return
  }
  actionLoading.value = true
  try {
    const partsData = {}
    for (const part of settlePartsList.value) {
      partsData[`used_qty_${part.id}`] = part.used_quantity
    }
    const res = await request.post(`/receiveorders/${currentActionOrder.value.id}/settle`, {
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
        await handleView(currentActionOrder.value)
      }
    }
  } catch (error) {
    ElMessage.error('结算失败')
  } finally {
    actionLoading.value = false
  }
}

// ==================== 测试 ====================
const testDialogVisible = ref(false)
const testForm = reactive({ test_result: '1', test_remark: '' })

const openTestDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(testForm, { test_result: '1', test_remark: '' })
  testDialogVisible.value = true
}

const submitTest = async () => {
  actionLoading.value = true
  try {
    // 根据状态判断调用哪个测试接口
    const id = currentActionOrder.value.id
    const payload = {
      test_result: parseInt(testForm.test_result),
      test_remark: testForm.test_remark
    }
    if (currentActionOrder.value.status === 13) {
      // 外店取回后测试
      await externalRetestReceive(id, payload)
    } else {
      // 普通测试
      await testReceive(id, payload)
    }
    ElMessage.success('测试提交成功')
    testDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 通知取件 ====================
const notifyDialogVisible = ref(false)
const notifyForm = reactive({ notify_method: 'sms' })

const openNotifyDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(notifyForm, { notify_method: 'sms' })
  notifyDialogVisible.value = true
}

const submitNotify = async () => {
  actionLoading.value = true
  try {
    await notifyReceive(currentActionOrder.value.id, { ...notifyForm })
    ElMessage.success('通知发送成功')
    notifyDialogVisible.value = false
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 取件完成 ====================
const handleComplete = async (row) => {
  try {
    await ElMessageBox.confirm('确认客户已取件完成？', '取件确认', {
      confirmButtonText: '确认完成',
      cancelButtonText: '取消',
      type: 'info'
    })
    actionLoading.value = true
    await completeReceive(row.id, {})
    ElMessage.success('取件完成')
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(row)
    }
  } catch (e) {
    // 用户取消或错误
  } finally {
    actionLoading.value = false
  }
}

// ==================== 取消 ====================
const cancelDialogVisible = ref(false)
const cancelForm = reactive({ reason: '' })

const handleCancel = (row) => {
  currentActionOrder.value = row
  Object.assign(cancelForm, { reason: '' })
  cancelDialogVisible.value = true
}

const submitCancel = async () => {
  actionLoading.value = true
  try {
    await cancelReceive(currentActionOrder.value.id, { reason: cancelForm.reason })
    ElMessage.success('已取消')
    cancelDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 送修外店 ====================
const externalSendDialogVisible = ref(false)
const externalSendForm = reactive({ external_shop_id: null, external_repair_reason: '' })

const openExternalSendDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(externalSendForm, { external_shop_id: null, external_repair_reason: '' })
  externalSendDialogVisible.value = true
}

const submitExternalSend = async () => {
  actionLoading.value = true
  try {
    await externalSendReceive(currentActionOrder.value.id, { ...externalSendForm })
    ElMessage.success('送修外店成功')
    externalSendDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 外店报价 ====================
const externalQuoteDialogVisible = ref(false)
const externalQuoteForm = reactive({ external_quote: 0 })

const openExternalQuoteDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(externalQuoteForm, { external_quote: 0 })
  externalQuoteDialogVisible.value = true
}

const submitExternalQuote = async () => {
  actionLoading.value = true
  try {
    await externalQuoteReceive(currentActionOrder.value.id, { ...externalQuoteForm })
    ElMessage.success('外店报价提交成功')
    externalQuoteDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 给客户报价 ====================
const customerQuoteDialogVisible = ref(false)
const customerQuoteForm = ref({ labor_cost: 0, material_cost: 0, other_cost: 0 })

const openCustomerQuoteDialog = (row) => {
  currentActionOrder.value = row
  customerQuoteForm.value = { labor_cost: 0, material_cost: 0, other_cost: 0 }
  customerQuoteDialogVisible.value = true
}

const submitCustomerQuote = async () => {
  actionLoading.value = true
  try {
    const payload = {
      labor_cost: parseFloat(customerQuoteForm.value.labor_cost) || 0,
      material_cost: parseFloat(customerQuoteForm.value.material_cost) || 0,
      other_cost: parseFloat(customerQuoteForm.value.other_cost) || 0
    }
    await customerQuoteReceive(currentActionOrder.value.id, payload)
    ElMessage.success('客户报价提交成功')
    customerQuoteDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 确认送修 ====================
const handleExternalConfirm = async (row) => {
  try {
    await ElMessageBox.confirm('确认送修到外店？', '确认送修', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info'
    })
    actionLoading.value = true
    await externalConfirmReceive(row.id, {})
    ElMessage.success('已确认送修')
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(row)
    }
  } catch (e) {
    // 用户取消或错误
  } finally {
    actionLoading.value = false
  }
}

// ==================== 取回设备 ====================
const externalReturnDialogVisible = ref(false)
const externalReturnForm = reactive({ external_return_date: '' })

const openExternalReturnDialog = (row) => {
  currentActionOrder.value = row
  Object.assign(externalReturnForm, { external_return_date: '' })
  externalReturnDialogVisible.value = true
}

const submitExternalReturn = async () => {
  actionLoading.value = true
  try {
    await externalReturnReceive(currentActionOrder.value.id, { ...externalReturnForm })
    ElMessage.success('取回设备成功')
    externalReturnDialogVisible.value = false
    fetchData()
    if (detailDialogVisible.value) {
      await handleView(currentActionOrder.value)
    }
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    actionLoading.value = false
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchData()
  loadUsers()
  loadExternalShops()
})
</script>

<style lang="scss" scoped>
.receive-page {
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

// 设备区块
.device-block {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;

  .device-block-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-weight: bold;
    color: #303133;
  }
}

// 配件区域
.parts-section {
  margin-top: 10px;
  padding: 10px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;

  .parts-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;

    .parts-title {
      font-size: 13px;
      font-weight: bold;
      color: #606266;
    }
  }
}

// 详情底部操作区
.detail-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

// 操作日志卡片
.log-card {
  :deep(.el-card__body) {
    padding: 10px 14px;
  }

  p {
    margin: 0;
    line-height: 1.6;
  }
}

// 详情页左右布局
.detail-layout {
  display: flex;
  gap: 20px;
  min-height: 500px;

  .detail-main {
    flex: 1;
    min-width: 0;
  }

  .detail-sidebar {
    width: 280px;
    flex-shrink: 0;
    background: #f5f7fa;
    border-radius: 4px;
    padding: 15px;
    max-height: 600px;
    overflow-y: auto;

    .sidebar-header {
      font-weight: bold;
      font-size: 14px;
      color: #303133;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e4e7ed;
    }

    :deep(.el-timeline) {
      padding-left: 10px;
    }

    :deep(.el-timeline-item__node) {
      background-color: #409eff;
    }

    :deep(.el-timeline-item__timestamp) {
      color: #909399;
      font-size: 12px;
    }
  }
}
</style>
