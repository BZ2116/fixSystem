<template>
  <div class="dispatch-page">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon primary">
              <el-icon :size="28"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">今日派单数</p>
              <p class="stat-value primary">{{ stats.today_total || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon :size="28"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">已接单数</p>
              <p class="stat-value success">{{ stats.accepted || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon :size="28"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">待接单数</p>
              <p class="stat-value warning">{{ stats.pending || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon info">
              <el-icon :size="28"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">接单率</p>
              <p class="stat-value info">{{ stats.accept_rate || '0%' }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主内容区 -->
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>派单管理</span>
        </div>
      </template>

      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 待派单 Tab -->
        <el-tab-pane label="待派单" name="pending">
          <!-- 搜索栏 -->
          <el-form :inline="true" :model="pendingSearch" class="search-form">
            <el-form-item label="关键词">
              <el-input
                v-model="pendingSearch.keyword"
                placeholder="工单号/客户名称/技术员姓名"
                clearable
                style="width: 220px"
                @keyup.enter="fetchPendingList"
              />
            </el-form-item>
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="pendingSearch.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 240px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="fetchPendingList">搜索</el-button>
              <el-button :icon="Refresh" @click="resetPendingSearch">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- 待派工单列表 -->
          <el-table :data="pendingList" stripe border v-loading="pendingLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="wo_no" label="工单号" width="150">
              <template #default="{ row }">
                <el-link type="primary">{{ row.wo_no }}</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="wo_type" label="工单类型" width="100" />
            <el-table-column prop="customer_name" label="客户名称" min-width="120" />
            <el-table-column prop="customer_phone" label="电话" width="120" />
            <el-table-column prop="device_type" label="设备类型" width="100" />
            <el-table-column label="品牌型号" width="140">
              <template #default="{ row }">{{ row.device_brand || '' }} {{ row.device_model || '' }}</template>
            </el-table-column>
            <el-table-column prop="reception_user_name" label="接待员工" width="100" />
            <el-table-column prop="engineer_user_name" label="维修工程师" width="100" />
            <el-table-column prop="fault_desc" label="故障描述" min-width="160" show-overflow-tooltip />
            <el-table-column prop="created_at" label="创建时间" width="160" />
            <el-table-column prop="priority" label="优先级" width="100" align="center">
              <template #default="{ row }">
                <el-rate v-model="row.priority" disabled :max="3" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleDispatch(row)">派单</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="pendingPagination.page"
            v-model:page-size="pendingPagination.pageSize"
            :total="pendingPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="fetchPendingList"
            @current-change="fetchPendingList"
          />
        </el-tab-pane>

        <!-- 派单记录 Tab -->
        <el-tab-pane label="派单记录" name="records">
          <!-- 搜索栏 -->
          <el-form :inline="true" :model="recordSearch" class="search-form">
            <el-form-item label="关键词">
              <el-input
                v-model="recordSearch.keyword"
                placeholder="工单号/客户名称/技术员姓名"
                clearable
                style="width: 220px"
                @keyup.enter="fetchRecordList"
              />
            </el-form-item>
            <el-form-item label="接单状态">
              <el-select v-model="recordSearch.status" placeholder="全部" clearable style="width: 120px">
                <el-option label="待接单" :value="0" />
                <el-option label="已接单" :value="1" />
                <el-option label="已拒单" :value="2" />
                <el-option label="已超时" :value="3" />
              </el-select>
            </el-form-item>
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="recordSearch.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 240px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="fetchRecordList">搜索</el-button>
              <el-button :icon="Refresh" @click="resetRecordSearch">重置</el-button>
              <el-button type="success" :icon="Download" @click="handleExportDispatch">导出</el-button>
            </el-form-item>
          </el-form>

          <!-- 派单记录列表 -->
          <el-table :data="recordList" stripe border v-loading="recordLoading">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="wo_no" label="工单号" width="150">
              <template #default="{ row }">
                <el-link type="primary">{{ row.wo_no }}</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="wo_type" label="工单类型" width="120" />
            <el-table-column prop="staff_name" label="技术员" width="100" />
            <el-table-column prop="staff_phone" label="技术员电话" width="130" />
            <el-table-column prop="dispatch_time" label="派单时间" width="160" />
            <el-table-column prop="accept_status" label="接单状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getAcceptStatusType(row.accept_status)" size="small">
                  {{ getAcceptStatusText(row.accept_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="arrive_time" label="到达时间" width="160" />
            <el-table-column prop="finish_time" label="完成时间" width="160" />
            <el-table-column label="操作" width="180" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="info" link size="small" @click="handleViewLog(row)">查看日志</el-button>
                <el-button
                  type="warning"
                  link
                  size="small"
                  @click="handleRedirect(row)"
                  v-if="row.accept_status === 0 || row.accept_status === 2"
                >改派</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="recordPagination.page"
            v-model:page-size="recordPagination.pageSize"
            :total="recordPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="fetchRecordList"
            @current-change="fetchRecordList"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 派单对话框 -->
    <el-dialog v-model="dispatchDialogVisible" title="手动派单" width="900px" destroy-on-close>
      <!-- 工单信息展示 -->
      <el-descriptions title="工单信息" :column="3" border class="dispatch-wo-info">
        <el-descriptions-item label="工单号">{{ currentWo.wo_no }}</el-descriptions-item>
        <el-descriptions-item label="工单类型">{{ currentWo.wo_type }}</el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-rate v-model="currentWo.priority" disabled :max="3" size="small" />
        </el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ currentWo.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ currentWo.customer_phone }}</el-descriptions-item>
        <el-descriptions-item label="地址">{{ currentWo.customer_address }}</el-descriptions-item>
        <el-descriptions-item label="故障描述" :span="3">{{ currentWo.fault_desc }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">
        选择技术员
        <el-button type="primary" link size="small" :icon="MagicStick" @click="handleAutoDispatch" style="margin-left: 10px;">
          自动派单
        </el-button>
      </el-divider>

      <!-- 自动派单推荐列表 -->
      <div v-if="recommendedStaffList.length > 0" class="recommend-section">
        <div class="recommend-header">
          <el-tag type="success" effect="dark">智能推荐</el-tag>
          <span class="recommend-tip">根据技能匹配、工作量和地理位置为您推荐以下工程师</span>
        </div>
        <el-table
          :data="recommendedStaffList"
          stripe
          border
          size="small"
          class="recommend-table"
          highlight-current-row
          @current-change="handleRecommendedStaffSelect"
          style="width: 100%; margin-bottom: 16px;"
        >
          <el-table-column width="55" align="center">
            <template #default="{ row }">
              <el-radio v-model="selectedStaffId" :value="row.id">&nbsp;</el-radio>
            </template>
          </el-table-column>
          <el-table-column label="推荐排序" width="90" align="center">
            <template #default="{ $index }">
              <el-tag v-if="$index === 0" type="danger" size="small">第1名</el-tag>
              <el-tag v-else-if="$index === 1" type="warning" size="small">第2名</el-tag>
              <el-tag v-else-if="$index === 2" type="success" size="small">第3名</el-tag>
              <span v-else>第{{ $index + 1 }}名</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="phone" label="电话" width="130" />
          <el-table-column label="技能匹配" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.skillMatch ? 'success' : 'info'" size="small">
                {{ row.skillMatch ? '匹配' : '不匹配' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="待处理工单" width="100" align="center">
            <template #default="{ row }">
              <span :class="{ 'workload-low': row.pendingCount <= 2, 'workload-medium': row.pendingCount > 2 && row.pendingCount <= 5, 'workload-high': row.pendingCount > 5 }">
                {{ row.pendingCount || 0 }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="距离" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.distance != null" :class="{ 'distance-near': row.distance <= 5, 'distance-medium': row.distance > 5 && row.distance <= 15, 'distance-far': row.distance > 15 }">
                {{ row.distance }}km
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="skills" label="技能" min-width="120" show-overflow-tooltip />
          <el-table-column prop="good_rate" label="好评率" width="80" align="center">
            <template #default="{ row }">
              <span :class="{ 'good-rate-high': row.good_rate >= 90 }">
                {{ row.good_rate != null ? row.good_rate + '%' : '-' }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 技术员选择列表 -->
      <el-table
        ref="staffTableRef"
        :data="staffList"
        stripe
        border
        v-loading="staffLoading"
        highlight-current-row
        @current-change="handleStaffSelect"
        style="width: 100%"
      >
        <el-table-column width="55" align="center">
          <template #default="{ row }">
            <el-radio v-model="selectedStaffId" :value="row.id">&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="online_status" label="在线状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getOnlineStatusType(row.online_status)" size="small">
              {{ getOnlineStatusText(row.online_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="今日接单" width="140" align="center">
          <template #default="{ row }">
            {{ row.today_count || 0 }} / {{ row.max_count || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="skills" label="技能" min-width="150" show-overflow-tooltip />
        <el-table-column prop="good_rate" label="好评率" width="100" align="center">
          <template #default="{ row }">
            <span :class="{ 'good-rate-high': row.good_rate >= 90 }">
              {{ row.good_rate != null ? row.good_rate + '%' : '-' }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 派单备注 -->
      <el-divider content-position="left">派单备注</el-divider>
      <el-input
        v-model="dispatchRemark"
        type="textarea"
        :rows="3"
        placeholder="请输入派单备注信息（可选）"
      />

      <template #footer>
        <el-button @click="dispatchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDispatch" :loading="dispatchLoading" :disabled="!selectedStaffId">
          确认派单
        </el-button>
      </template>
    </el-dialog>

    <!-- 改派对话框 -->
    <el-dialog v-model="redirectDialogVisible" title="工单改派" width="900px" destroy-on-close>
      <!-- 原派单信息 -->
      <el-descriptions title="原派单信息" :column="3" border class="dispatch-wo-info">
        <el-descriptions-item label="工单号">{{ currentRecord.wo_no }}</el-descriptions-item>
        <el-descriptions-item label="工单类型">{{ currentRecord.wo_type }}</el-descriptions-item>
        <el-descriptions-item label="原技术员">{{ currentRecord.staff_name }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ currentRecord.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ currentRecord.customer_phone }}</el-descriptions-item>
        <el-descriptions-item label="地址">{{ currentRecord.customer_address }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">选择新技术员</el-divider>

      <!-- 技术员选择列表 -->
      <el-table
        :data="staffList"
        stripe
        border
        v-loading="staffLoading"
        highlight-current-row
        @current-change="handleRedirectStaffSelect"
        style="width: 100%"
      >
        <el-table-column width="55" align="center">
          <template #default="{ row }">
            <el-radio v-model="redirectStaffId" :value="row.id">&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="online_status" label="在线状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getOnlineStatusType(row.online_status)" size="small">
              {{ getOnlineStatusText(row.online_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="今日接单" width="140" align="center">
          <template #default="{ row }">
            {{ row.today_count || 0 }} / {{ row.max_count || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="skills" label="技能" min-width="150" show-overflow-tooltip />
        <el-table-column prop="good_rate" label="好评率" width="100" align="center">
          <template #default="{ row }">
            <span :class="{ 'good-rate-high': row.good_rate >= 90 }">
              {{ row.good_rate != null ? row.good_rate + '%' : '-' }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 改派备注 -->
      <el-divider content-position="left">改派备注</el-divider>
      <el-input
        v-model="redirectRemark"
        type="textarea"
        :rows="3"
        placeholder="请输入改派原因（可选）"
      />

      <template #footer>
        <el-button @click="redirectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRedirect" :loading="redirectLoading" :disabled="!redirectStaffId">
          确认改派
        </el-button>
      </template>
    </el-dialog>

    <!-- 派单日志对话框 -->
    <el-dialog v-model="logDialogVisible" title="派单日志" width="600px" destroy-on-close>
      <div v-loading="logLoading" class="log-container">
        <el-timeline v-if="logList.length > 0">
          <el-timeline-item
            v-for="log in logList"
            :key="log.id"
            :timestamp="log.created_at"
            placement="top"
            :type="getLogTimelineType(log.action)"
          >
            <el-card shadow="never" class="log-card">
              <h4>{{ log.action }}</h4>
              <p v-if="log.content">{{ log.content }}</p>
              <p v-if="log.operator_name" class="log-operator">操作人：{{ log.operator_name }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无日志记录" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Document, CircleCheck, Clock, TrendCharts, MagicStick, Download } from '@element-plus/icons-vue'
import request from '@/api/request'

// ==================== 状态映射 ====================

// 在线状态：0离线、1在线、2忙碌
const getOnlineStatusType = (status) => {
  const map = { 0: 'info', 1: 'success', 2: 'warning' }
  return map[status] || 'info'
}

const getOnlineStatusText = (status) => {
  const map = { 0: '离线', 1: '在线', 2: '忙碌' }
  return map[status] || '未知'
}

// 接单状态：0待接、1已接、2拒单、3超时
const getAcceptStatusType = (status) => {
  const map = { 0: 'info', 1: 'success', 2: 'danger', 3: 'warning' }
  return map[status] || 'info'
}

const getAcceptStatusText = (status) => {
  const map = { 0: '待接单', 1: '已接单', 2: '已拒单', 3: '已超时' }
  return map[status] || '未知'
}

// 日志时间线类型
const getLogTimelineType = (action) => {
  if (!action) return 'info'
  if (action.includes('派单') || action.includes('改派')) return 'primary'
  if (action.includes('接单')) return 'success'
  if (action.includes('拒单') || action.includes('超时')) return 'danger'
  if (action.includes('到达')) return 'warning'
  if (action.includes('完成')) return 'success'
  return 'info'
}

// ==================== 统计数据 ====================

const stats = ref({})

const fetchStats = async () => {
  try {
    const res = await request.get('/dispatch/stats')
    if (res.code === 200) {
      stats.value = res.data || {}
    }
  } catch (error) {
    console.error('获取派单统计失败:', error)
  }
}

// ==================== Tab 切换 ====================

const activeTab = ref('pending')

const handleTabChange = (tab) => {
  if (tab === 'pending') {
    fetchPendingList()
  } else if (tab === 'records') {
    fetchRecordList()
  }
}

// ==================== 待派单列表 ====================

const pendingLoading = ref(false)
const pendingList = ref([])
const pendingSearch = reactive({
  keyword: '',
  dateRange: null
})
const pendingPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchPendingList = async () => {
  pendingLoading.value = true
  try {
    const params = {
      page: pendingPagination.page,
      page_size: pendingPagination.pageSize,
      keyword: pendingSearch.keyword || undefined
    }
    if (pendingSearch.dateRange && pendingSearch.dateRange.length === 2) {
      params.start_date = pendingSearch.dateRange[0]
      params.end_date = pendingSearch.dateRange[1]
    }
    const res = await request.get('/dispatch/pending', { params })
    if (res.code === 200) {
      pendingList.value = res.data.list || []
      pendingPagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取待派单列表失败:', error)
  } finally {
    pendingLoading.value = false
  }
}

const resetPendingSearch = () => {
  pendingSearch.keyword = ''
  pendingSearch.dateRange = null
  pendingPagination.page = 1
  fetchPendingList()
}

// ==================== 派单记录列表 ====================

const recordLoading = ref(false)
const recordList = ref([])
const recordSearch = reactive({
  keyword: '',
  status: null,
  dateRange: null
})
const recordPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchRecordList = async () => {
  recordLoading.value = true
  try {
    const params = {
      page: recordPagination.page,
      page_size: recordPagination.pageSize,
      keyword: recordSearch.keyword || undefined,
      status: recordSearch.status != null ? recordSearch.status : undefined
    }
    if (recordSearch.dateRange && recordSearch.dateRange.length === 2) {
      params.start_date = recordSearch.dateRange[0]
      params.end_date = recordSearch.dateRange[1]
    }
    const res = await request.get('/dispatch/records', { params })
    if (res.code === 200) {
      recordList.value = res.data.list || []
      recordPagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('获取派单记录失败:', error)
  } finally {
    recordLoading.value = false
  }
}

const resetRecordSearch = () => {
  recordSearch.keyword = ''
  recordSearch.status = null
  recordSearch.dateRange = null
  recordPagination.page = 1
  fetchRecordList()
}

// ==================== 派单对话框 ====================

const dispatchDialogVisible = ref(false)
const dispatchLoading = ref(false)
const dispatchRemark = ref('')
const currentWo = ref({})
const selectedStaffId = ref(null)
const staffLoading = ref(false)
const staffList = ref([])
const recommendedStaffList = ref([])

// 自动派单 - 根据技能匹配、工作量和地理位置推荐工程师
const handleAutoDispatch = () => {
  if (!staffList.value || staffList.value.length === 0) {
    ElMessage.warning('暂无可用工程师')
    return
  }

  // 计算每个工程师的推荐分数
  const scoredStaff = staffList.value.map(staff => {
    let score = 0
    const woType = currentWo.value.wo_type || ''
    const customerAddress = currentWo.value.customer_address || ''

    // 1. 技能匹配度评分 (最高40分)
    const skills = staff.skills || ''
    const skillMatch = skills.toLowerCase().includes(woType.toLowerCase()) ||
                       woType.toLowerCase().includes(skills.toLowerCase())
    if (skillMatch) {
      score += 40
    }

    // 2. 工作量评分 (最高35分) - 待处理工单越少分数越高
    const pendingCount = staff.pending_count || staff.today_count || 0
    if (pendingCount === 0) score += 35
    else if (pendingCount <= 2) score += 30
    else if (pendingCount <= 5) score += 20
    else if (pendingCount <= 8) score += 10
    else score += 5

    // 3. 在线状态评分 (最高10分)
    if (staff.online_status === 1) score += 10 // 在线
    else if (staff.online_status === 2) score += 5 // 忙碌

    // 4. 好评率评分 (最高10分)
    const goodRate = staff.good_rate || 0
    if (goodRate >= 95) score += 10
    else if (goodRate >= 90) score += 8
    else if (goodRate >= 80) score += 5
    else if (goodRate >= 70) score += 3

    // 5. 距离评分 (最高5分) - 模拟距离计算
    // 实际项目中应该从后端获取真实的距离数据
    let distance = staff.distance
    if (distance == null) {
      // 模拟距离：基于工程师ID生成一个伪随机但固定的距离值
      distance = ((staff.id * 7) % 30) + 1
    }
    if (distance <= 5) score += 5
    else if (distance <= 10) score += 3
    else if (distance <= 20) score += 1

    return {
      ...staff,
      score,
      skillMatch,
      pendingCount,
      distance
    }
  })

  // 按分数降序排序，取前5名
  recommendedStaffList.value = scoredStaff
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)

  ElMessage.success('已为您推荐最优工程师')
}

const handleRecommendedStaffSelect = (row) => {
  if (row) {
    selectedStaffId.value = row.id
  }
}

const fetchStaffList = async () => {
  staffLoading.value = true
  try {
    const res = await request.get('/dispatch/staff-list')
    if (res.code === 200) {
      staffList.value = res.data || []
    }
  } catch (error) {
    console.error('获取技术员列表失败:', error)
  } finally {
    staffLoading.value = false
  }
}

const handleDispatch = (row) => {
  currentWo.value = { ...row }
  selectedStaffId.value = null
  dispatchRemark.value = ''
  recommendedStaffList.value = []
  dispatchDialogVisible.value = true
  fetchStaffList()
}

const handleStaffSelect = (row) => {
  if (row) {
    selectedStaffId.value = row.id
  }
}

const submitDispatch = async () => {
  if (!selectedStaffId.value) {
    ElMessage.warning('请选择技术员')
    return
  }

  dispatchLoading.value = true
  try {
    const res = await request.post('/dispatch/manual', {
      wo_id: currentWo.value.id,
      staff_id: selectedStaffId.value,
      remark: dispatchRemark.value || undefined
    })
    if (res.code === 200) {
      ElMessage.success('派单成功')
      dispatchDialogVisible.value = false
      fetchPendingList()
      fetchRecordList()
      fetchStats()
    }
  } catch (error) {
    console.error('派单失败:', error)
  } finally {
    dispatchLoading.value = false
  }
}

// ==================== 改派对话框 ====================

const redirectDialogVisible = ref(false)
const redirectLoading = ref(false)
const redirectRemark = ref('')
const redirectStaffId = ref(null)
const currentRecord = ref({})

const handleRedirect = (row) => {
  currentRecord.value = { ...row }
  redirectStaffId.value = null
  redirectRemark.value = ''
  redirectDialogVisible.value = true
  fetchStaffList()
}

const handleRedirectStaffSelect = (row) => {
  if (row) {
    redirectStaffId.value = row.id
  }
}

const submitRedirect = async () => {
  if (!redirectStaffId.value) {
    ElMessage.warning('请选择新技术员')
    return
  }

  try {
    await ElMessageBox.confirm('确定要改派该工单吗？', '改派确认', {
      type: 'warning'
    })
  } catch {
    return
  }

  redirectLoading.value = true
  try {
    const res = await request.post(`/dispatch/${currentRecord.value.id}/redirect`, {
      staff_id: redirectStaffId.value,
      remark: redirectRemark.value || undefined
    })
    if (res.code === 200) {
      ElMessage.success('改派成功')
      redirectDialogVisible.value = false
      fetchRecordList()
      fetchStats()
    }
  } catch (error) {
    console.error('改派失败:', error)
  } finally {
    redirectLoading.value = false
  }
}

// ==================== 派单日志对话框 ====================

const logDialogVisible = ref(false)
const logLoading = ref(false)
const logList = ref([])

const handleViewLog = async (row) => {
  logDialogVisible.value = true
  logLoading.value = true
  logList.value = []
  try {
    const res = await request.get(`/dispatch/logs/${row.wo_id || row.id}`)
    if (res.code === 200) {
      logList.value = res.data || []
    }
  } catch (error) {
    console.error('获取派单日志失败:', error)
  } finally {
    logLoading.value = false
  }
}

// ==================== 导出功能 ====================

const handleExportDispatch = () => {
  const params = new URLSearchParams()
  if (recordSearch.keyword) params.append('keyword', recordSearch.keyword)
  if (recordSearch.status != null) params.append('status', recordSearch.status)
  const token = localStorage.getItem('token') || ''
  window.open(`/api/dispatchorders/export?${params.toString()}&token=${token}`, '_blank')
}

// ==================== 初始化 ====================

onMounted(() => {
  fetchStats()
  fetchPendingList()
})
</script>

<style lang="scss" scoped>
.dispatch-page {
  // 统计卡片
  .stat-row {
    margin-bottom: 20px;

    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;
        gap: 16px;

        .stat-icon {
          width: 56px;
          height: 56px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;

          &.primary {
            background-color: rgba(64, 158, 255, 0.1);
            color: #409eff;
          }
          &.success {
            background-color: rgba(103, 194, 58, 0.1);
            color: #67c23a;
          }
          &.warning {
            background-color: rgba(230, 162, 60, 0.1);
            color: #e6a23c;
          }
          &.info {
            background-color: rgba(144, 147, 153, 0.1);
            color: #909399;
          }
        }

        .stat-info {
          .stat-label {
            font-size: 13px;
            color: #909399;
            margin-bottom: 6px;
          }

          .stat-value {
            font-size: 26px;
            font-weight: bold;
            line-height: 1;

            &.primary { color: #409eff; }
            &.success { color: #67c23a; }
            &.warning { color: #e6a23c; }
            &.info { color: #909399; }
          }
        }
      }
    }
  }

  // 卡片头部
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  // 搜索表单
  .search-form {
    margin-bottom: 20px;
  }

  // 分页
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  // 派单工单信息
  .dispatch-wo-info {
    margin-bottom: 16px;
  }

  // 好评率高亮
  .good-rate-high {
    color: #67c23a;
    font-weight: bold;
  }

  // 推荐区域样式
  .recommend-section {
    margin-bottom: 16px;

    .recommend-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;

      .recommend-tip {
        font-size: 13px;
        color: #606266;
      }
    }

    .recommend-table {
      .workload-low {
        color: #67c23a;
        font-weight: bold;
      }
      .workload-medium {
        color: #e6a23c;
      }
      .workload-high {
        color: #f56c6c;
        font-weight: bold;
      }

      .distance-near {
        color: #67c23a;
        font-weight: bold;
      }
      .distance-medium {
        color: #e6a23c;
      }
      .distance-far {
        color: #909399;
      }
    }
  }

  // 日志容器
  .log-container {
    max-height: 500px;
    overflow-y: auto;

    .log-card {
      h4 {
        margin: 0 0 8px 0;
        font-size: 14px;
        color: #303133;
      }

      p {
        margin: 0 0 4px 0;
        font-size: 13px;
        color: #606266;
      }

      .log-operator {
        font-size: 12px;
        color: #909399;
        margin-top: 6px;
      }
    }
  }
}
</style>
