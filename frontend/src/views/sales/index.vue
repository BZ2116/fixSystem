<template>
  <div class="sales-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>销售管理</span>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
            <el-button type="warning" :icon="Upload" @click="handleImport">导入</el-button>
            <el-button type="primary" :icon="Plus" @click="handleAdd">新建销售单</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="销售单号/客户" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="客户">
          <el-select v-model="searchForm.customer_id" placeholder="选择客户" clearable filterable style="width: 180px">
            <el-option v-for="c in customers" :key="c.id" :label="c.customer_name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="待审核" :value="0" />
            <el-option label="已审核" :value="1" />
            <el-option label="已出库" :value="2" />
            <el-option label="已取消" :value="9" />
          </el-select>
        </el-form-item>
        <el-form-item label="开票">
          <el-select v-model="searchForm.has_invoice" placeholder="开票状态" clearable style="width: 120px" @change="fetchData">
            <el-option label="已开票" :value="1" />
            <el-option label="未开票" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="收据">
          <el-select v-model="searchForm.has_receipt" placeholder="收据状态" clearable style="width: 120px" @change="fetchData">
            <el-option label="已开收据" :value="1" />
            <el-option label="未开收据" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe border v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="sales_no" label="销售单号" width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.sales_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户" min-width="150" />
        <el-table-column prop="sales_date" label="销售日期" width="120" />
        <el-table-column prop="total_quantity" label="数量" width="80" align="center" />
        <el-table-column prop="total_amount" label="销售金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="paid_amount" label="已收金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ row.paid_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="发票" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_invoice === 1" type="success" size="small">已开票</el-tag>
            <el-tag v-else type="info" size="small">未开票</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收据" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_receipt === 1" type="warning" size="small">已开收据</el-tag>
            <el-tag v-else type="info" size="small">未开收据</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="资产" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_asset === 1" type="success" size="small">已关联</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">详情</el-button>
            <el-button type="primary" link size="small" @click="handleEdit(row)" v-if="row.status === 0">编辑</el-button>
            <el-button type="success" link size="small" @click="handleAudit(row)" v-if="row.status === 0">审核</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)" v-if="row.status === 0">删除</el-button>
            <el-button type="info" link size="small" @click="handlePrint(row)">打印</el-button>
            <el-button v-if="row.has_invoice === 1" type="primary" link size="small" @click="openInvoiceDialog(row)">发票</el-button>
            <el-button v-if="row.has_receipt === 1" type="warning" link size="small" @click="openReceiptDialog(row)">收据</el-button>
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
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 新增/编辑销售单弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑销售单' : '新建销售单'" width="900px" destroy-on-close>
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="客户" prop="customer_id">
              <el-select
                v-model="formData.customer_id"
                placeholder="选择客户"
                filterable
                style="width: 100%"
                @change="handleCustomerChange"
              >
                <el-option v-for="c in customers" :key="c.id" :label="c.customer_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="关联资产">
              <el-radio-group v-model="formData.has_asset" @change="handleAssetSwitch">
                <el-radio :label="0">否</el-radio>
                <el-radio :label="1">是</el-radio>
              </el-radio-group>
              <div v-if="formData.has_asset === 1" class="asset-tip">
                <el-icon><InfoFilled /></el-icon>
                <span>选择"是"后，保存订单时将同步创建资产档案</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="销售日期" prop="sales_date">
              <el-date-picker v-model="formData.sales_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="客户电话">
              <el-input v-model="formData.customer_phone" placeholder="客户电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="客户地址">
              <el-input v-model="formData.customer_address" placeholder="客户地址" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系人">
              <el-input v-model="formData.contact_name" placeholder="联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="销售人员">
              <el-select v-model="formData.salesperson_id" placeholder="选择销售人员" filterable style="width: 100%">
                <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="付款方式">
              <el-select v-model="formData.payment_method" placeholder="选择付款方式" style="width: 100%">
                <el-option label="现金" value="cash" />
                <el-option label="转账" value="transfer" />
                <el-option label="支付宝" value="alipay" />
                <el-option label="微信" value="wechat" />
                <el-option label="赊账" value="credit" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="交货方式">
              <el-select v-model="formData.delivery_method" placeholder="选择交货方式" style="width: 100%">
                <el-option label="自提" value="self_pickup" />
                <el-option label="送货" value="delivery" />
                <el-option label="快递" value="express" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="运费">
              <el-input-number v-model="formData.freight_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="折扣金额">
              <el-input-number v-model="formData.discount_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="备注">
              <el-input v-model="formData.remark" placeholder="备注" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="是否开票">
              <el-radio-group v-model="formData.has_invoice">
                <el-radio :label="1">是</el-radio>
                <el-radio :label="0">否</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否开收据">
              <el-radio-group v-model="formData.has_receipt">
                <el-radio :label="1">是</el-radio>
                <el-radio :label="0">否</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">销售明细</el-divider>

        <div class="items-header">
          <el-button type="primary" size="small" :icon="Plus" @click="addItem">添加商品</el-button>
        </div>

        <el-table :data="formData.items" border size="small" class="items-table">
          <el-table-column type="index" label="序号" width="50" align="center" />
          <el-table-column label="商品" min-width="200">
            <template #default="{ row, $index }">
              <el-select v-model="row.product_id" placeholder="选择商品" filterable @change="(val) => onProductChange(val, $index)" style="width: 100%">
                <el-option v-for="p in products" :key="p.id" :label="p.product_name + ' (库存:' + (p.current_stock || 0) + ')'" :value="p.id">
                  <span style="float: left">{{ p.product_name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">库存: {{ p.current_stock || 0 }}</span>
                </el-option>
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="规格" width="100">
            <template #default="{ row }">
              <span>{{ row.specification || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="单位" width="80">
            <template #default="{ row }">
              <span>{{ row.unit || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="库存" width="80" align="center">
            <template #default="{ row }">
              <span :style="{ color: (row.current_stock || 0) < (row.quantity || 0) ? '#f56c6c' : '#67c23a' }">{{ row.current_stock || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="120">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.quantity" :min="1" :precision="0" style="width: 100%" @change="calculateItemAmount($index)" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" style="width: 100%" @change="calculateItemAmount($index)" />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.amount?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="amount-summary">
          <el-row :gutter="20">
            <el-col :span="6">
              <span>数量合计: <strong>{{ totalQuantity }}</strong></span>
            </el-col>
            <el-col :span="6">
              <span>金额合计: <strong>¥{{ totalAmount.toFixed(2) }}</strong></span>
            </el-col>
          </el-row>
        </div>

        <!-- 资产录入区域 -->
        <div v-if="formData.has_asset === 1" class="asset-section">
          <div class="section-title">
            <span>资产信息</span>
            <el-button type="primary" size="small" @click="addAssetItem">添加资产</el-button>
          </div>

          <div v-for="(asset, index) in formData.assets" :key="index" class="asset-item">
            <div class="asset-header">
              <span>资产 #{{ index + 1 }}</span>
              <el-button type="danger" link @click="removeAssetItem(index)">删除</el-button>
            </div>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item :label="`资产类型`" :required="true">
                  <el-select v-model="asset.asset_type_id" placeholder="选择类型" @change="handleAssetTypeChange(asset)">
                    <el-option v-for="type in assetTypeList" :key="type.id" :label="type.type_name" :value="type.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="`资产名称`" :required="true">
                  <el-input v-model="asset.asset_name" placeholder="资产名称" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="`设备编号`">
                  <el-input v-model="asset.device_no" placeholder="设备编号" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item :label="`SN序列号`">
                  <el-input v-model="asset.sn_code" placeholder="SN序列号" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="`IP地址`">
                  <el-input v-model="asset.ip_address" placeholder="IP地址" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="`登录密码`">
                  <el-input v-model="asset.login_password" placeholder="登录密码" show-password />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item :label="`存放位置`">
                  <el-input v-model="asset.location" placeholder="存放位置" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="`质保到期日`">
                  <el-date-picker v-model="asset.warranty_expire_date" type="date" placeholder="选择日期" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="`使用责任人`">
                  <el-input v-model="asset.responsible_person" placeholder="使用责任人" />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 专属字段（根据类型动态显示） -->
            <el-row v-if="asset.asset_type_id" :gutter="20">
              <el-col v-for="field in getAssetTypeFields(asset.asset_type_id)" :key="field.key" :span="8">
                <el-form-item :label="field.label">
                  <el-input v-model="asset.asset_data[field.key]" :placeholder="field.label" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="备注">
              <el-input v-model="asset.remark" type="textarea" rows="2" placeholder="备注信息" />
            </el-form-item>
          </div>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 销售单详情弹窗 -->
    <el-dialog v-model="detailVisible" title="销售单详情" width="800px" destroy-on-close>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="销售单号">{{ currentOrder.sales_no }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ currentOrder.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentOrder.status)">{{ getStatusText(currentOrder.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="销售日期">{{ currentOrder.sales_date }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentOrder.operator_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentOrder.created_at }}</el-descriptions-item>
        <el-descriptions-item label="发票状态">
          <el-tag v-if="currentOrder.has_invoice === 1" type="success" size="small">已开票</el-tag>
          <el-tag v-else type="info" size="small">未开票</el-tag>
          <el-button v-if="currentOrder.has_invoice === 1" type="primary" link size="small" style="margin-left: 8px" @click="openInvoiceDialog(currentOrder)">查看发票</el-button>
        </el-descriptions-item>
        <el-descriptions-item label="收据状态">
          <el-tag v-if="currentOrder.has_receipt === 1" type="warning" size="small">已开收据</el-tag>
          <el-tag v-else type="info" size="small">未开收据</el-tag>
          <el-button v-if="currentOrder.has_receipt === 1" type="primary" link size="small" style="margin-left: 8px" @click="openReceiptDialog(currentOrder)">查看收据</el-button>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">销售明细</el-divider>

      <el-table :data="currentOrder.items || []" border size="small">
        <el-table-column type="index" label="序号" width="50" align="center" />
        <el-table-column prop="product_name" label="商品名称" min-width="150" />
        <el-table-column prop="specification" label="规格" width="100" />
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column prop="unit_price" label="单价" width="100" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">¥{{ row.amount?.toFixed(2) }}</template>
        </el-table-column>
      </el-table>

      <div class="detail-summary">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="数量合计" :value="currentOrder.total_quantity || 0" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="金额合计" :value="currentOrder.total_amount || 0" :precision="2" prefix="¥" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="已收金额" :value="currentOrder.paid_amount || 0" :precision="2" prefix="¥" />
          </el-col>
        </el-row>
      </div>

      <el-divider content-position="left">备注</el-divider>
      <p>{{ currentOrder.remark || '无' }}</p>

      <!-- 关联资产 -->
      <template v-if="currentOrder.has_asset === 1">
        <el-divider content-position="left">关联资产</el-divider>
        <el-table :data="currentOrder.assets || []" border size="small">
          <el-table-column prop="asset_no" label="资产编号" width="120" />
          <el-table-column prop="asset_name" label="资产名称" min-width="150" />
          <el-table-column prop="asset_type_name" label="资产类型" width="120" />
          <el-table-column prop="sn_code" label="SN码" width="150" />
          <el-table-column prop="asset_status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getAssetStatusType(row.asset_status)">{{ getAssetStatusText(row.asset_status) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="导入销售单" width="500px">
      <el-upload
        ref="uploadRef"
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".xlsx,.xls,.csv"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx, .xls, .csv 格式文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importLoading">导入</el-button>
      </template>
    </el-dialog>

    <PrintDialog
      v-model:visible="printDialogVisible"
      template-type="sale"
      :print-data="printData"
    />

    <!-- 发票录入对话框 -->
    <el-dialog v-model="invoiceDialogVisible" title="发票录入" width="1000px" destroy-on-close>
      <el-form :model="invoiceForm" label-width="120px" ref="invoiceFormRef">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="发票类型">
              <el-select v-model="invoiceForm.invoice_type" placeholder="选择发票类型" style="width: 100%">
                <el-option label="普通发票" value="normal" />
                <el-option label="增值税专用发票" value="vat_special" />
                <el-option label="电子发票" value="electronic" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开票日期">
              <el-date-picker v-model="invoiceForm.invoice_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="发票编号">
              <el-input v-model="invoiceForm.invoice_no" placeholder="发票编号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="开票状态">
              <el-select v-model="invoiceForm.invoice_status" placeholder="选择状态" style="width: 100%">
                <el-option label="未开票" :value="0" />
                <el-option label="已开票" :value="1" />
                <el-option label="作废" :value="2" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">客户开票信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发票抬头">
              <el-input v-model="invoiceForm.invoice_title" placeholder="发票抬头" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税号">
              <el-input v-model="invoiceForm.tax_no" placeholder="税号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="地址">
              <el-input v-model="invoiceForm.invoice_address" placeholder="地址" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="invoiceForm.invoice_phone" placeholder="电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开户行">
              <el-input v-model="invoiceForm.bank_name" placeholder="开户行" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="银行账号">
              <el-input v-model="invoiceForm.bank_account" placeholder="银行账号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">发票明细</el-divider>
        <el-table :data="invoiceForm.items" border size="small" class="items-table">
          <el-table-column type="index" label="序号" width="50" align="center" />
          <el-table-column label="商品名称" min-width="150">
            <template #default="{ row }">
              <el-input v-model="row.product_name" placeholder="商品名称" />
            </template>
          </el-table-column>
          <el-table-column label="规格" width="100">
            <template #default="{ row }">
              <el-input v-model="row.specification" placeholder="规格" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="80">
            <template #default="{ row }">
              <el-input v-model="row.unit" placeholder="单位" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" :precision="0" size="small" style="width: 100%" @change="calcInvoiceItem(row)" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" style="width: 100%" @change="calcInvoiceItem(row)" />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="120" align="right">
            <template #default="{ row }">
              <span>{{ row.amount?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="税率(%)" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.tax_rate" :min="0" :max="100" :precision="0" size="small" style="width: 100%" @change="calcInvoiceItem(row)" />
            </template>
          </el-table-column>
          <el-table-column label="税额" width="100" align="right">
            <template #default="{ row }">
              <span>{{ row.tax_amount?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="价税合计" width="120" align="right">
            <template #default="{ row }">
              <span>{{ row.total_with_tax?.toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>

        <div class="amount-summary">
          <el-row :gutter="20">
            <el-col :span="6">
              <span>金额合计: <strong>¥{{ invoiceTotalAmount.toFixed(2) }}</strong></span>
            </el-col>
            <el-col :span="6">
              <span>税额合计: <strong>¥{{ invoiceTotalTax.toFixed(2) }}</strong></span>
            </el-col>
            <el-col :span="6">
              <span>价税合计: <strong>¥{{ invoiceGrandTotal.toFixed(2) }}</strong></span>
            </el-col>
          </el-row>
        </div>

        <el-row :gutter="20" style="margin-top: 15px">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="invoiceForm.remark" type="textarea" :rows="2" placeholder="备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="invoiceDialogVisible = false">关闭</el-button>
        <el-button type="danger" v-if="invoiceForm.invoice_status === 1" @click="handleVoidInvoice">作废发票</el-button>
        <el-button type="primary" @click="submitInvoice" :loading="invoiceLoading">保存发票</el-button>
      </template>
    </el-dialog>

    <!-- 收据预览/开具对话框 -->
    <el-dialog v-model="receiptDialogVisible" title="收据" width="850px" destroy-on-close>
      <div id="receiptPrintArea" class="receipt-area">
        <!-- 收据标题 -->
        <div class="receipt-header" style="text-align: center; margin-bottom: 20px; border-bottom: 2px solid #8B4513; padding-bottom: 10px;">
          <h2 style="font-size: 28px; color: #8B4513; margin: 0; letter-spacing: 8px;">收 款 收 据</h2>
        </div>
        
        <!-- 编号和日期 -->
        <div class="receipt-meta" style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 15px; border-bottom: 1px dashed #999; padding-bottom: 10px;">
          <span><strong>编号: NO.</strong> {{ receiptForm.receipt_no }}</span>
          <span><strong>日期:</strong> {{ receiptForm.receipt_date }}</span>
        </div>
        
        <!-- 付款方信息 -->
        <div class="receipt-info" style="margin-bottom: 15px; font-size: 14px; line-height: 2;">
          <div style="display: flex; margin-bottom: 5px;">
            <span style="min-width: 80px;"><strong>付款方:</strong></span>
            <span style="flex: 1; border-bottom: 1px solid #333; padding-left: 5px;">{{ receiptForm.customer_name || '&nbsp;' }}</span>
          </div>
          <div style="display: flex; margin-bottom: 5px;">
            <span style="min-width: 80px;"><strong>收款方式:</strong></span>
            <span style="flex: 1; border-bottom: 1px solid #333; padding-left: 5px;">{{ receiptForm.payment_method_text || '&nbsp;' }}</span>
          </div>
          <div style="display: flex;">
            <span style="min-width: 80px;"><strong>销售单号:</strong></span>
            <span style="flex: 1; border-bottom: 1px solid #333; padding-left: 5px;">{{ receiptForm.sales_no || '&nbsp;' }}</span>
          </div>
        </div>
        
        <!-- 商品明细表格 -->
        <table class="receipt-table" style="width: 100%; border-collapse: collapse; margin-bottom: 15px; border: 1px solid #333;">
          <thead>
            <tr style="background: #f5f5f5;">
              <th style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px; width: 50px;">序号</th>
              <th style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px;">项目</th>
              <th style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px; width: 120px;">规格</th>
              <th style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px; width: 60px;">单位</th>
              <th style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px; width: 60px;">数量</th>
              <th style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px; width: 90px;">单价(¥)</th>
              <th style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px; width: 100px;">金额(¥)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in receiptForm.items" :key="index">
              <td style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px;">{{ index + 1 }}</td>
              <td style="border: 1px solid #333; padding: 8px; font-size: 13px;">{{ item.product_name }}</td>
              <td style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px;">{{ item.specification || '-' }}</td>
              <td style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px;">{{ item.unit || '-' }}</td>
              <td style="border: 1px solid #333; padding: 8px; text-align: center; font-size: 13px;">{{ item.quantity }}</td>
              <td style="border: 1px solid #333; padding: 8px; text-align: right; font-size: 13px;">{{ (item.unit_price || 0).toFixed(2) }}</td>
              <td style="border: 1px solid #333; padding: 8px; text-align: right; font-size: 13px;">{{ (item.amount || 0).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
        
        <!-- 金额合计 -->
        <div class="receipt-total" style="text-align: right; font-size: 14px; margin-bottom: 15px; border-top: 1px dashed #999; padding-top: 10px;">
          <div style="margin-bottom: 5px;">
            <strong>合计(小写): ¥ {{ receiptForm.paid_amount?.toFixed(2) }}</strong>
          </div>
          <div style="margin-bottom: 5px;">
            <strong>合计(大写): {{ amountToChinese(receiptForm.paid_amount) }}</strong>
          </div>
        </div>
        
        <!-- 备注 -->
        <div class="receipt-remark" style="font-size: 14px; margin-bottom: 20px; border-top: 1px dashed #999; padding-top: 10px;">
          <div style="display: flex;">
            <span style="min-width: 60px;"><strong>备注:</strong></span>
            <span style="flex: 1; border-bottom: 1px solid #333; padding-left: 5px; min-height: 24px;">{{ receiptForm.remark || '&nbsp;' }}</span>
          </div>
        </div>
        
        <!-- 收款方信息 -->
        <div class="receipt-company" style="font-size: 14px; margin-bottom: 20px; line-height: 2;">
          <div style="display: flex; margin-bottom: 5px;">
            <span style="min-width: 100px;"><strong>收款单位:</strong></span>
            <span style="flex: 1; border-bottom: 1px solid #333; padding-left: 5px;">{{ receiptForm.company_name || '&nbsp;' }}</span>
          </div>
        </div>
        
        <!-- 签名区域 -->
        <div class="receipt-footer" style="display: flex; justify-content: space-between; font-size: 14px; margin-top: 30px; padding-top: 20px;">
          <div style="width: 45%;">
            <span><strong>收款人(签章):</strong></span>
            <span style="display: inline-block; width: 150px; border-bottom: 1px solid #333; margin-left: 5px;">&nbsp;</span>
          </div>
          <div style="width: 45%;">
            <span><strong>客户确认:</strong></span>
            <span style="display: inline-block; width: 150px; border-bottom: 1px solid #333; margin-left: 5px;">&nbsp;</span>
          </div>
        </div>
        
        <!-- 底部说明 -->
        <div class="receipt-notice" style="text-align: center; font-size: 12px; color: #666; margin-top: 30px; padding-top: 15px; border-top: 1px solid #999;">
          <p>本收据经盖章/签字生效 | 感谢惠顾</p>
          <p>电子收据 与原件等效</p>
        </div>
      </div>

      <template #footer>
        <el-button @click="receiptDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="submitReceipt" :loading="receiptLoading">开具保存</el-button>
        <el-button type="success" @click="printReceiptDialog">打印收据</el-button>
      </template>
    </el-dialog>

    <!-- 收据打印对话框 -->
    <PrintDialog v-model:visible="receiptPrintDialogVisible" template-type="receipt" :print-data="receiptPrintData" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Upload, Download } from '@element-plus/icons-vue'
import { getSalesList, createSales, updateSales, deleteSales, auditSales } from '@/api/sales'
import { saveInvoice, getInvoiceDetail, updateInvoiceStatus, createReceipt, getReceiptPrint, voidReceipt } from '@/api/sales'
import { getCustomerList } from '@/api/customer'
import { getProductList } from '@/api/product'
import { getUserList } from '@/api/user'
import { getAssetTypeList, createSalesOrderAssets, getSalesOrderAssets } from '@/api/asset'
import request from '@/api/request'
import { InfoFilled } from '@element-plus/icons-vue'
import PrintDialog from '@/components/PrintDialog.vue'

const loading = ref(false)
const submitLoading = ref(false)
const importLoading = ref(false)
const tableData = ref([])
const customers = ref([])
const products = ref([])
const users = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const uploadRef = ref(null)
const currentOrder = ref({})
const importFile = ref(null)

// 打印相关
const printDialogVisible = ref(false)
const printData = ref({})

// 发票相关
const invoiceDialogVisible = ref(false)
const invoiceLoading = ref(false)
const invoiceFormRef = ref(null)
const invoiceForm = reactive({
  order_id: null,
  sales_id: null,
  invoice_type: 'normal',
  invoice_date: new Date().toISOString().split('T')[0],
  invoice_no: '',
  invoice_status: 0,
  invoice_title: '',
  tax_no: '',
  invoice_address: '',
  invoice_phone: '',
  bank_name: '',
  bank_account: '',
  remark: '',
  items: []
})

// 收据相关
const receiptDialogVisible = ref(false)
const receiptLoading = ref(false)
const receiptForm = reactive({
  sales_id: null,
  receipt_no: '',
  receipt_date: new Date().toISOString().split('T')[0],
  customer_name: '',
  customer_phone: '',
  sales_no: '',
  items: [],
  total_amount: 0,
  paid_amount: 0,
  payment_method: '',
  payment_method_text: '',
  remark: '',
  payee: '',
  company_name: '云科汇网络'
})

// 收据打印相关
const receiptPrintDialogVisible = ref(false)
const receiptPrintData = ref({})

// 资产相关
const assetTypeList = ref([])

// 专属字段配置
const typeFields = {
  1: [ // network
    { key: 'brand', label: '品牌' },
    { key: 'model', label: '型号' },
    { key: 'subnet_mask', label: '子网掩码' },
    { key: 'gateway', label: '网关' }
  ],
  2: [ // computer
    { key: 'cpu', label: '处理器' },
    { key: 'memory', label: '内存' },
    { key: 'disk', label: '硬盘' },
    { key: 'os_version', label: '系统版本' }
  ]
}

const searchForm = reactive({
  keyword: '',
  customer_id: null,
  status: null,
  has_invoice: null,
  has_receipt: null,
  date_range: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  customer_id: null,
  sales_date: new Date().toISOString().split('T')[0],
  customer_phone: '',
  customer_address: '',
  contact_name: '',
  salesperson_id: null,
  payment_method: '',
  delivery_method: '',
  freight_amount: 0,
  discount_amount: 0,
  remark: '',
  has_invoice: 0,
  has_receipt: 0,
  has_asset: 0,
  assets: [],
  items: []
})

const rules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  sales_date: [{ required: true, message: '请选择销售日期', trigger: 'change' }]
}

const totalQuantity = computed(() => {
  return formData.items.reduce((sum, item) => sum + (item.quantity || 0), 0)
})

const totalAmount = computed(() => {
  return formData.items.reduce((sum, item) => sum + (item.amount || 0), 0)
})

const getStatusType = (status) => {
  const types = { 0: 'warning', 1: 'success', 2: 'info', 9: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '待审核', 1: '已审核', 2: '已出库', 9: '已取消' }
  return texts[status] || '未知'
}

// 资产状态
const getAssetStatusType = (status) => {
  const types = { 0: 'info', 1: 'success', 2: 'warning', 3: 'danger' }
  return types[status] || 'info'
}

const getAssetStatusText = (status) => {
  const texts = { 0: '闲置', 1: '使用中', 2: '维修中', 3: '报废' }
  return texts[status] || '未知'
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      customer_id: searchForm.customer_id,
      status: searchForm.status,
      has_invoice: searchForm.has_invoice,
      has_receipt: searchForm.has_receipt,
      start_date: searchForm.date_range?.[0],
      end_date: searchForm.date_range?.[1]
    }
    const res = await getSalesList(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      pagination.total = res.data.total
    }
  } catch (error) {
    console.error('获取销售单列表失败:', error)
    ElMessage.error('获取销售单列表失败')
  } finally {
    loading.value = false
  }
}

const fetchCustomers = async () => {
  try {
    const res = await getCustomerList({ page_size: 1000 })
    if (res.code === 200) {
      customers.value = res.data.list
    }
  } catch (error) {
    console.error('获取客户列表失败:', error)
  }
}

const fetchProducts = async () => {
  try {
    const res = await getProductList({ page_size: 1000 })
    if (res.code === 200) {
      products.value = res.data.list
    }
  } catch (error) {
    console.error('获取商品列表失败:', error)
  }
}

const fetchUsers = async () => {
  try {
    const res = await getUserList({ page_size: 1000 })
    if (res.code === 200) {
      users.value = res.data.list
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

// 加载资产类型
const loadAssetTypes = async () => {
  try {
    const res = await getAssetTypeList()
    assetTypeList.value = res.data || []
  } catch (error) {
    console.error('获取资产类型失败:', error)
  }
}

// 资产开关切换
const handleAssetSwitch = (val) => {
  if (val === 1 && formData.assets.length === 0) {
    addAssetItem()
  }
}

// 添加资产项
const addAssetItem = () => {
  formData.assets.push({
    asset_type_id: null,
    asset_type_name: '',
    asset_name: '',
    device_no: '',
    sn_code: '',
    ip_address: '',
    login_password: '',
    location: '',
    warranty_expire_date: '',
    responsible_person: '',
    asset_data: {},
    remark: ''
  })
}

// 删除资产项
const removeAssetItem = (index) => {
  formData.assets.splice(index, 1)
}

// 获取资产类型专属字段
const getAssetTypeFields = (typeId) => {
  return typeFields[typeId] || []
}

// 资产类型变更
const handleAssetTypeChange = (asset) => {
  const type = assetTypeList.value.find(t => t.id === asset.asset_type_id)
  asset.asset_type_name = type?.type_name || ''
  asset.asset_data = {}  // 清空专属字段
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.customer_id = null
  searchForm.status = null
  searchForm.has_invoice = null
  searchForm.has_receipt = null
  searchForm.date_range = null
  handleSearch()
}

// 客户选择变化处理
const handleCustomerChange = (customerId) => {
  if (!customerId) return
  const customer = customers.value.find(c => c.id === customerId)
  if (customer) {
    formData.customer_name = customer.customer_name
    formData.customer_phone = customer.phone || customer.customer_phone || ''
    formData.customer_address = customer.address || customer.customer_address || ''
    formData.contact_name = customer.contact_name || customer.customer_name || ''
  }
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    customer_id: null,
    sales_date: new Date().toISOString().split('T')[0],
    customer_phone: '',
    customer_address: '',
    contact_name: '',
    salesperson_id: null,
    payment_method: '',
    delivery_method: '',
    freight_amount: 0,
    discount_amount: 0,
    remark: '',
    has_invoice: 0,
    has_receipt: 0,
    has_asset: 0,
    assets: [],
    items: []
  })
  loadAssetTypes()
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  currentOrder.value = row
  try {
    const { getSalesDetail } = await import('@/api/sales')
    const res = await getSalesDetail(row.id)
    if (res.code === 200) {
      const order = res.data
      const editItems = (order.items || []).map(item => {
        const product = products.value.find(p => p.id === item.product_id)
        return {
          ...item,
          unit_price: item.unit_price || item.price || 0,
          amount: item.amount || 0,
          current_stock: product ? (product.current_stock || 0) : 0
        }
      })
      Object.assign(formData, {
        customer_id: order.customer_id,
        sales_date: order.order_date,
        customer_phone: order.customer_phone || '',
        customer_address: order.customer_address || '',
        contact_name: order.contact_name || '',
        salesperson_id: order.salesperson_id || null,
        payment_method: order.payment_method || '',
        delivery_method: order.delivery_method || '',
        freight_amount: order.freight_amount || 0,
        discount_amount: order.discount_amount || 0,
        remark: order.remark,
        has_invoice: order.has_invoice || 0,
        has_receipt: order.has_receipt || 0,
        has_asset: order.has_asset || 0,
        assets: order.assets || [],
        items: editItems
      })
      loadAssetTypes()
      dialogVisible.value = true
    }
  } catch (error) {
    console.error('获取销售单详情失败:', error)
    ElMessage.error('获取销售单详情失败')
  }
}

const handleView = async (row) => {
  try {
    const { getSalesDetail } = await import('@/api/sales')
    const res = await getSalesDetail(row.id)
    if (res.code === 200) {
      currentOrder.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('获取销售单详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该销售单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deleteSales(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleAudit = (row) => {
  ElMessageBox.confirm('确定要审核该销售单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await auditSales(row.id)
      if (res.code === 200) {
        ElMessage.success('审核成功')
        fetchData()
      }
    } catch (error) {
      ElMessage.error('审核失败')
    }
  }).catch(() => {})
}

// 打开打印
const handlePrint = async (row) => {
  try {
    const res = await request.get(`/sales/orders/${row.id}/print`)
    if (res.code === 200) {
      const data = res.data
      // 格式化商品明细表格
      let itemsHtml = ''
      if (data.items && data.items.length > 0) {
        itemsHtml = '<table class="print-table"><thead><tr><th>商品</th><th>规格</th><th>单位</th><th>数量</th><th>单价</th><th>金额</th></tr></thead><tbody>' +
          data.items.map(item => `<tr><td>${item.product_name || ''}</td><td>${item.specification || ''}</td><td>${item.unit || ''}</td><td>${item.quantity || 0}</td><td>${(item.price || 0).toFixed(2)}</td><td>${(item.amount || 0).toFixed(2)}</td></tr>`).join('') +
          '</tbody></table>'
      }
      printData.value = {
        order_no: data.order_no || '',
        order_date: data.order_date || '',
        customer_name: data.customer_name || '',
        customer_phone: data.customer_phone || '',
        customer_address: data.customer_address || '',
        total_amount: (data.total_amount || 0).toFixed(2),
        freight_amount: (data.freight_amount || 0).toFixed(2),
        discount_amount: (data.discount_amount || 0).toFixed(2),
        actual_amount: (data.actual_amount || 0).toFixed(2),
        items_detail: itemsHtml,
        remark: data.remark || '',
        status_name: data.status_name || '',
        operator_name: data.operator_name || ''
      }
      printDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取打印数据失败:', error)
    ElMessage.error('获取打印数据失败')
  }
}

const addItem = () => {
  formData.items.push({
    product_id: null,
    product_name: '',
    specification: '',
    unit: '',
    quantity: 1,
    unit_price: 0,
    amount: 0
  })
}

const removeItem = (index) => {
  formData.items.splice(index, 1)
}

const onProductChange = (productId, index) => {
  const product = products.value.find(p => p.id === productId)
  if (product) {
    formData.items[index].product_name = product.product_name
    formData.items[index].specification = product.specification
    formData.items[index].unit = product.unit_name || '个'
    formData.items[index].unit_price = product.sale_price || 0
    formData.items[index].current_stock = product.current_stock || 0
    calculateItemAmount(index)
  }
}

const calculateItemAmount = (index) => {
  const item = formData.items[index]
  item.amount = (item.quantity || 0) * (item.unit_price || 0)
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (formData.items.length === 0) {
      ElMessage.warning('请至少添加一个商品')
      return
    }

    // 库存校验
    for (const item of formData.items) {
      if (item.product_id) {
        const product = products.value.find(p => p.id === item.product_id)
        if (product && (product.current_stock || 0) < (item.quantity || 0)) {
          ElMessage.warning(`商品【${product.product_name}】库存不足，当前库存：${product.current_stock || 0}`)
          return
        }
      }
    }

    // 如果有资产，验证资产信息
    if (formData.has_asset === 1 && formData.assets.length > 0) {
      for (const asset of formData.assets) {
        if (!asset.asset_type_id) {
          ElMessage.warning('请选择资产类型')
          return
        }
        if (!asset.asset_name) {
          ElMessage.warning('请填写资产名称')
          return
        }
      }
      // 设置客户信息到资产
      formData.assets.forEach(asset => {
        asset.customer_id = formData.customer_id
        asset.customer_name = formData.customer_name
      })
    }

    submitLoading.value = true
    try {
      const data = {
        ...formData,
        total_quantity: totalQuantity.value,
        total_amount: totalAmount.value,
        items: formData.items.map(item => ({
          ...item,
          price: item.unit_price || item.price || 0
        }))
      }
      let res
      if (isEdit.value) {
        res = await updateSales(currentOrder.value.id, data)
      } else {
        res = await createSales(data)
      }
      if (res.code === 200) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      submitLoading.value = false
    }
  })
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  fetchData()
}

const handlePageChange = (val) => {
  pagination.page = val
  fetchData()
}

const handleImport = () => {
  importDialogVisible.value = true
  importFile.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const handleFileChange = (file) => {
  importFile.value = file.raw
}

const submitImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  importLoading.value = true
  try {
    const { importSales } = await import('@/api/sales')
    const res = await importSales(importFile.value)
    if (res.code === 200) {
      ElMessage.success('导入成功')
      importDialogVisible.value = false
      fetchData()
    }
  } catch (error) {
    ElMessage.error('导入失败')
  } finally {
    importLoading.value = false
  }
}

const handleExport = () => {
  const params = new URLSearchParams()
  if (searchForm.keyword) params.append('keyword', searchForm.keyword)
  if (searchForm.status !== '' && searchForm.status !== null && searchForm.status !== undefined) params.append('status', searchForm.status)
  if (searchForm.date_range && searchForm.date_range[0]) params.append('date_start', searchForm.date_range[0])
  if (searchForm.date_range && searchForm.date_range[1]) params.append('date_end', searchForm.date_range[1])
  const token = localStorage.getItem('token') || ''
  window.open(`/api/sales/orders/export?${params.toString()}&token=${token}`, '_blank')
}

// ========== 发票相关函数 ==========

// 发票金额计算
const invoiceTotalAmount = computed(() => {
  return invoiceForm.items.reduce((sum, item) => sum + (item.amount || 0), 0)
})

const invoiceTotalTax = computed(() => {
  return invoiceForm.items.reduce((sum, item) => sum + (item.tax_amount || 0), 0)
})

const invoiceGrandTotal = computed(() => {
  return invoiceForm.items.reduce((sum, item) => sum + (item.total_with_tax || 0), 0)
})

// 发票明细自动计算
const calcInvoiceItem = (row) => {
  row.amount = (row.quantity || 0) * (row.unit_price || 0)
  row.tax_amount = row.amount * ((row.tax_rate || 0) / 100)
  row.total_with_tax = row.amount + row.tax_amount
}

// 打开发票对话框
const openInvoiceDialog = async (row) => {
  try {
    // 先获取销售单详情
    const { getSalesDetail } = await import('@/api/sales')
    const res = await getSalesDetail(row.id)
    if (res.code === 200) {
      const order = res.data
      // 尝试获取已有发票信息
      let invoiceData = null
      try {
        const invRes = await getInvoiceDetail(row.id)
        if (invRes.code === 200) {
          invoiceData = invRes.data
        }
      } catch (e) {
        // 没有发票信息，使用默认值
      }

      Object.assign(invoiceForm, {
        order_id: row.id,
        sales_id: row.id,
        invoice_type: invoiceData?.invoice_type || 'normal',
        invoice_date: invoiceData?.invoice_date || new Date().toISOString().split('T')[0],
        invoice_no: invoiceData?.invoice_no || '',
        invoice_status: invoiceData?.invoice_status ?? 0,
        invoice_title: invoiceData?.invoice_title || order.customer_name || '',
        tax_no: invoiceData?.tax_no || '',
        invoice_address: invoiceData?.invoice_address || order.customer_address || '',
        invoice_phone: invoiceData?.invoice_phone || order.customer_phone || '',
        bank_name: invoiceData?.bank_name || '',
        bank_account: invoiceData?.bank_account || '',
        remark: invoiceData?.remark || '',
        items: invoiceData?.items || (order.items || []).map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          specification: item.specification || '',
          unit: item.unit || '',
          quantity: item.quantity,
          unit_price: item.unit_price || item.price || 0,
          amount: item.amount || (item.quantity * (item.unit_price || item.price || 0)),
          tax_rate: 0,
          tax_amount: 0,
          total_with_tax: item.amount || (item.quantity * (item.unit_price || item.price || 0))
        }))
      })
      invoiceDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取发票数据失败:', error)
    ElMessage.error('获取发票数据失败')
  }
}

// 提交发票
const submitInvoice = async () => {
  invoiceLoading.value = true
  try {
    const data = {
      ...invoiceForm,
      total_amount: invoiceTotalAmount.value,
      total_tax: invoiceTotalTax.value,
      grand_total: invoiceGrandTotal.value
    }
    const res = await saveInvoice(data)
    if (res.code === 200) {
      ElMessage.success('发票保存成功')
      invoiceDialogVisible.value = false
      fetchData()
    }
  } catch (error) {
    console.error('保存发票失败:', error)
    ElMessage.error('保存发票失败')
  } finally {
    invoiceLoading.value = false
  }
}

// 作废发票
const handleVoidInvoice = () => {
  ElMessageBox.confirm('确定要作废该发票吗？作废后不可恢复。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await updateInvoiceStatus(invoiceForm.sales_id, { invoice_status: 2 })
      if (res.code === 200) {
        ElMessage.success('发票已作废')
        invoiceForm.invoice_status = 2
        invoiceDialogVisible.value = false
        fetchData()
      }
    } catch (error) {
      ElMessage.error('作废发票失败')
    }
  }).catch(() => {})
}

// ========== 收据相关函数 ==========

// 打开收据对话框
const openReceiptDialog = async (row) => {
  try {
    const { getSalesDetail } = await import('@/api/sales')
    const res = await getSalesDetail(row.id)
    if (res.code === 200) {
      const order = res.data
      const paymentMethodMap = {
        cash: '现金',
        transfer: '银行转账',
        alipay: '支付宝',
        wechat: '微信支付',
        credit: '赊账'
      }
      
      // 处理商品明细，确保金额正确计算
      const items = (order.items || []).map(item => ({
        product_name: item.product_name || '',
        specification: item.specification || '',
        unit: item.unit || '',
        quantity: item.quantity || 0,
        unit_price: parseFloat(item.unit_price || item.price) || 0,
        amount: parseFloat(item.amount) || 0
      }))
      
      // 计算实际应收金额
      const actualAmount = parseFloat(order.actual_amount) || parseFloat(order.total_amount) || 0
      const paidAmount = parseFloat(order.paid_amount) || actualAmount
      
      Object.assign(receiptForm, {
        sales_id: row.id,
        receipt_no: order.receipt_no || `SK${new Date().toISOString().slice(0,10).replace(/-/g,'')}${String(Math.floor(Math.random()*10000)).padStart(4,'0')}`,
        receipt_date: new Date().toISOString().split('T')[0],
        customer_name: order.customer_name || '',
        customer_phone: order.customer_phone || '',
        sales_no: order.order_no || '',
        items: items,
        total_amount: actualAmount,
        paid_amount: paidAmount,
        payment_method: order.payment_method || '',
        payment_method_text: paymentMethodMap[order.payment_method] || order.payment_method || '现金',
        remark: order.remark || '',
        payee: order.salesperson_name || '',
        company_name: '云科汇网络'
      })
      receiptDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取收据数据失败:', error)
    ElMessage.error('获取收据数据失败')
  }
}

// 开具收据
const submitReceipt = async () => {
  receiptLoading.value = true
  try {
    const res = await createReceipt({
      order_id: receiptForm.sales_id,
      receipt_no: receiptForm.receipt_no,
      receipt_date: receiptForm.receipt_date,
      remark: receiptForm.remark
    })
    if (res.code === 200) {
      ElMessage.success('收据开具成功')
      receiptDialogVisible.value = false
      fetchData()
    }
  } catch (error) {
    console.error('开具收据失败:', error)
    ElMessage.error('开具收据失败')
  } finally {
    receiptLoading.value = false
  }
}

// 金额转大写
const amountToChinese = (amount) => {
  if (!amount || isNaN(amount)) return '零元整'
  const num = parseFloat(amount)
  if (num === 0) return '零元整'
  
  const cnNums = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
  const cnUnits = ['', '拾', '佰', '仟']
  const cnBigUnits = ['', '万', '亿', '万亿']
  
  let str = ''
  let integerPart = Math.floor(num)
  let decimalPart = Math.round((num - integerPart) * 100)
  
  // 处理整数部分
  if (integerPart === 0) {
    str = '零'
  } else {
    let unitPos = 0
    let bigUnitPos = 0
    let needZero = false
    
    while (integerPart > 0) {
      let section = integerPart % 10000
      if (needZero && section > 0) {
        str = '零' + str
      }
      
      let sectionStr = ''
      let zeroFlag = false
      for (let i = 0; i < 4; i++) {
        let digit = section % 10
        if (digit === 0) {
          if (!zeroFlag && sectionStr !== '') {
            zeroFlag = true
          }
        } else {
          if (zeroFlag) {
            sectionStr = cnNums[0] + sectionStr
            zeroFlag = false
          }
          sectionStr = cnNums[digit] + cnUnits[i] + sectionStr
        }
        section = Math.floor(section / 10)
      }
      
      if (sectionStr !== '') {
        str = sectionStr + cnBigUnits[bigUnitPos] + str
      }
      
      needZero = (integerPart % 10000) < 1000 && (integerPart % 10000) > 0
      integerPart = Math.floor(integerPart / 10000)
      bigUnitPos++
    }
  }
  
  str += '元'
  
  // 处理小数部分
  if (decimalPart === 0) {
    str += '整'
  } else {
    const jiao = Math.floor(decimalPart / 10)
    const fen = decimalPart % 10
    if (jiao > 0) {
      str += cnNums[jiao] + '角'
    }
    if (fen > 0) {
      str += cnNums[fen] + '分'
    }
  }
  
  return str
}

// 打印收据 - 使用PrintDialog
const printReceiptDialog = () => {
  const items = receiptForm.items || []
  const itemsHtml = items.length > 0
    ? `<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;margin-bottom:15px;border:1px solid #333;">
        <thead style="background:#f5f5f5;">
          <tr>
            <th style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;width:50px;">序号</th>
            <th style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;">项目</th>
            <th style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;width:120px;">规格</th>
            <th style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;width:60px;">单位</th>
            <th style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;width:60px;">数量</th>
            <th style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;width:90px;">单价(¥)</th>
            <th style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;width:100px;">金额(¥)</th>
          </tr>
        </thead>
        <tbody>
          ${items.map((item, index) => `
            <tr>
              <td style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;">${index + 1}</td>
              <td style="border:1px solid #333;padding:8px;font-size:13px;">${item.product_name || ''}</td>
              <td style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;">${item.specification || '-'}</td>
              <td style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;">${item.unit || '-'}</td>
              <td style="border:1px solid #333;padding:8px;text-align:center;font-size:13px;">${item.quantity || 0}</td>
              <td style="border:1px solid #333;padding:8px;text-align:right;font-size:13px;">${(item.unit_price || 0).toFixed(2)}</td>
              <td style="border:1px solid #333;padding:8px;text-align:right;font-size:13px;">${(item.amount || 0).toFixed(2)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>`
    : '<p style="color:#999;">暂无商品明细</p>'

  receiptPrintData.value = {
    receipt_no: receiptForm.receipt_no || '',
    receipt_date: receiptForm.receipt_date || '',
    customer_name: receiptForm.customer_name || '',
    customer_phone: receiptForm.customer_phone || '',
    sales_no: receiptForm.sales_no || '',
    payment_method: receiptForm.payment_method_text || '',
    items_html: itemsHtml,
    paid_amount: (receiptForm.paid_amount || 0).toFixed(2),
    paid_amount_chinese: amountToChinese(receiptForm.paid_amount),
    remark: receiptForm.remark || '',
    company_name: receiptForm.company_name || '云科汇网络',
    payee: receiptForm.payee || ''
  }
  receiptPrintDialogVisible.value = true
}

// 保留原printReceipt函数供可能的其他调用（实际不再使用）
const printReceipt = () => {
  printReceiptDialog()
}

onMounted(() => {
  fetchData()
  fetchCustomers()
  fetchProducts()
  fetchUsers()
})
</script>

<style lang="scss" scoped>
.sales-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .items-header {
    margin-bottom: 10px;
  }

  .items-table {
    margin-bottom: 15px;
  }

  .amount-summary {
    margin-top: 15px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;
    text-align: right;

    strong {
      color: #f56c6c;
      font-size: 16px;
    }
  }

  .detail-summary {
    margin-top: 20px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 4px;
  }

  .receipt-area {
    padding: 20px;
    background: #fff;
    border: 1px dashed #dcdfe6;
    border-radius: 4px;
  }

  .asset-section {
    background: #f3e5f5;
    padding: 20px;
    border-radius: 8px;
    margin-top: 20px;
    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: bold;
      color: #7b1fa2;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e1bee7;
    }
    .asset-item {
      background: #fff;
      padding: 15px;
      border-radius: 8px;
      margin-bottom: 15px;
      .asset-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        font-weight: bold;
        color: #4a148c;
      }
    }
  }
  .asset-tip {
    margin-top: 8px;
    color: #7b1fa2;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 5px;
  }
}
</style>
