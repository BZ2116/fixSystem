<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409eff">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">客户总数</p>
              <p class="stat-value">{{ stats.customer_count || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a">
              <el-icon><OfficeBuilding /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">供应商数量</p>
              <p class="stat-value">{{ stats.supplier_count || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c">
              <el-icon><GoodsFilled /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">商品总数</p>
              <p class="stat-value">{{ stats.product_count || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f56c6c">
              <el-icon><Tools /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">今日收入</p>
              <p class="stat-value">¥{{ (stats.today_income || 0).toFixed(2) }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 工单统计 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card small">
          <div class="stat-content">
            <div class="stat-info">
              <p class="stat-label">待处理工单</p>
              <p class="stat-value warning">{{ stats.wo_pending || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card small">
          <div class="stat-content">
            <div class="stat-info">
              <p class="stat-label">已完成工单</p>
              <p class="stat-value success">{{ stats.wo_completed || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card small">
          <div class="stat-content">
            <div class="stat-info">
              <p class="stat-label">今日新工单</p>
              <p class="stat-value primary">{{ stats.wo_today || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card small">
          <div class="stat-content">
            <div class="stat-info">
              <p class="stat-label">工单总数</p>
              <p class="stat-value">{{ stats.wo_total || 0 }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快捷入口 -->
    <el-card class="quick-entry" shadow="never">
      <template #header>
        <div class="card-header">
          <span>快捷入口</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="4" v-for="item in quickEntries" :key="item.path">
          <div class="quick-item" @click="router.push(item.path)">
            <div class="quick-icon" :style="{ background: item.color }">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <p>{{ item.title }}</p>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>工单趋势（最近7天）</span>
            </div>
          </template>
          <div ref="woChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>收入趋势（最近7天）</span>
            </div>
          </template>
          <div ref="incomeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 系统信息 -->
    <el-row :gutter="20" class="info-row">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>系统信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="系统版本">v2.0.0</el-descriptions-item>
            <el-descriptions-item label="数据库">MySQL 8.0</el-descriptions-item>
            <el-descriptions-item label="后端框架">Flask 2.3</el-descriptions-item>
            <el-descriptions-item label="前端框架">Vue 3.3</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>当前用户</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用户名">{{ userStore.username }}</el-descriptions-item>
            <el-descriptions-item label="真实姓名">{{ userStore.realName }}</el-descriptions-item>
            <el-descriptions-item label="登录时间">{{ currentTime }}</el-descriptions-item>
            <el-descriptions-item label="系统状态">
              <el-tag type="success" size="small">运行中</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'
import * as echarts from 'echarts'

const router = useRouter()
const userStore = useUserStore()

const woChartRef = ref(null)
const incomeChartRef = ref(null)
let woChart = null
let incomeChart = null

const stats = reactive({
  customer_count: 0,
  supplier_count: 0,
  product_count: 0,
  wo_total: 0,
  wo_pending: 0,
  wo_completed: 0,
  wo_today: 0,
  today_income: 0,
  wo_status_stats: {}
})

const currentTime = computed(() => {
  return new Date().toLocaleString('zh-CN')
})

const quickEntries = [
  { title: '客户管理', path: '/customer', icon: 'UserFilled', color: '#409eff' },
  { title: '供应商管理', path: '/supplier', icon: 'OfficeBuilding', color: '#67c23a' },
  { title: '商品管理', path: '/product', icon: 'GoodsFilled', color: '#e6a23c' },
  { title: '工单管理', path: '/workorder', icon: 'Tools', color: '#f56c6c' },
  { title: '库存管理', path: '/inventory', icon: 'Box', color: '#909399' },
  { title: '财务管理', path: '/finance', icon: 'Money', color: '#c71585' }
]

const fetchStats = async () => {
  try {
    const res = await request.get('/dashboard/stats')
    if (res.code === 200) {
      Object.assign(stats, res.data)
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchWoTrend = async () => {
  try {
    const res = await request.get('/dashboard/workorder-trend')
    if (res.code === 200) {
      renderWoChart(res.data)
    }
  } catch (error) {
    console.error('获取工单趋势失败:', error)
  }
}

const fetchIncomeTrend = async () => {
  try {
    const res = await request.get('/dashboard/income-trend')
    if (res.code === 200) {
      renderIncomeChart(res.data)
    }
  } catch (error) {
    console.error('获取收入趋势失败:', error)
  }
}

const renderWoChart = (data) => {
  if (!woChartRef.value) return
  
  woChart = echarts.init(woChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['新增工单', '完成工单']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '新增工单',
        type: 'line',
        data: data.map(d => d.count),
        smooth: true,
        itemStyle: { color: '#409eff' }
      },
      {
        name: '完成工单',
        type: 'line',
        data: data.map(d => d.completed),
        smooth: true,
        itemStyle: { color: '#67c23a' }
      }
    ]
  }
  woChart.setOption(option)
}

const renderIncomeChart = (data) => {
  if (!incomeChartRef.value) return
  
  incomeChart = echarts.init(incomeChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>收入: ¥{c}'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date)
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '¥{value}'
      }
    },
    series: [
      {
        name: '收入',
        type: 'bar',
        data: data.map(d => d.income),
        itemStyle: { color: '#67c23a' }
      }
    ]
  }
  incomeChart.setOption(option)
}

const handleResize = () => {
  woChart?.resize()
  incomeChart?.resize()
}

onMounted(async () => {
  await fetchStats()
  await nextTick()
  fetchWoTrend()
  fetchIncomeTrend()
  window.addEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stat-row {
    margin-bottom: 20px;

    .stat-card {
      background: linear-gradient(135deg, #fff 0%, #F3E5F5 100%);
      border: 1px solid #E1BEE7;

      .stat-content {
        display: flex;
        align-items: center;

        .stat-icon {
          width: 60px;
          height: 60px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);

          .el-icon {
            font-size: 28px;
            color: #fff;
          }
        }

        .stat-info {
          margin-left: 20px;

          .stat-label {
            font-size: 14px;
            color: #999;
            margin-bottom: 8px;
          }

          .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #333;

            &.warning { color: #e6a23c; }
            &.primary { color: #409eff; }
            &.success { color: #67c23a; }
            &.danger { color: #f56c6c; }
          }
        }
      }

      &.small {
        .stat-content {
          justify-content: center;

          .stat-info {
            margin-left: 0;
            text-align: center;

            .stat-value {
              font-size: 24px;
            }
          }
        }
      }
    }
  }
  
  .quick-entry {
    margin-bottom: 20px;
    
    .quick-item {
      text-align: center;
      cursor: pointer;
      padding: 20px 0;
      transition: transform 0.3s;
      
      &:hover {
        transform: translateY(-5px);
      }
      
      .quick-icon {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px;
        
        .el-icon {
          font-size: 24px;
          color: #fff;
        }
      }
      
      p {
        font-size: 14px;
        color: #666;
      }
    }
  }
  
  .chart-row {
    margin-bottom: 20px;
    
    .chart-container {
      height: 300px;
    }
  }
  
  .info-row {
    .card-header {
      font-weight: bold;
    }
  }
}
</style>
