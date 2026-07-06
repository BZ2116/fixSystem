<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo">
        <el-icon v-if="!isCollapse" style="font-size:24px;color:#409eff;margin-right:8px"><Tools /></el-icon>
        <span v-if="!isCollapse">维修系统</span>
        <el-icon v-else><Tools /></el-icon>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="menu"
      >
        <!-- 1. 首页 -->
        <el-menu-item v-if="hasMenuPermission('/dashboard')" index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <!-- 2. 前台管理 -->
        <el-sub-menu v-if="hasGroupPermission('front')" index="/workorder">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>前台管理</span>
          </template>
          <el-menu-item v-if="hasMenuPermission('/workorder')" index="/workorder">
            <el-icon><Tools /></el-icon>
            <template #title>工单管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/receive')" index="/receive">
            <el-icon><TakeawayBox /></el-icon>
            <template #title>接件管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/dispatch')" index="/dispatch">
            <el-icon><Van /></el-icon>
            <template #title>派单管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/quote')" index="/quote">
            <el-icon><Tickets /></el-icon>
            <template #title>报价管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/asset')" index="/asset">
            <el-icon><Box /></el-icon>
            <template #title>资产管理</template>
          </el-menu-item>
        </el-sub-menu>

        <!-- 3. 物资管理 -->
        <el-sub-menu v-if="hasGroupPermission('material')" index="/product">
          <template #title>
            <el-icon><ShoppingBag /></el-icon>
            <span>物资管理</span>
          </template>
          <el-menu-item v-if="hasMenuPermission('/product')" index="/product">
            <el-icon><Goods /></el-icon>
            <template #title>商品管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/sales')" index="/sales">
            <el-icon><ShoppingCart /></el-icon>
            <template #title>销售管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/purchase')" index="/purchase">
            <el-icon><ShoppingCartFull /></el-icon>
            <template #title>采购管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/preorder')" index="/preorder">
            <el-icon><List /></el-icon>
            <template #title>采购预订</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/preorder/sale')" index="/preorder/sale">
            <el-icon><Tickets /></el-icon>
            <template #title>销售预订</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/return')" index="/return">
            <el-icon><RefreshLeft /></el-icon>
            <template #title>采购退货</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/return/sale')" index="/return/sale">
            <el-icon><RefreshRight /></el-icon>
            <template #title>销售退货</template>
          </el-menu-item>
        </el-sub-menu>

        <!-- 4. 库房管理 -->
        <el-sub-menu v-if="hasGroupPermission('warehouse')" index="/inventory">
          <template #title>
            <el-icon><House /></el-icon>
            <span>库房管理</span>
          </template>
          <el-menu-item v-if="hasMenuPermission('/inventory')" index="/inventory">
            <el-icon><Box /></el-icon>
            <template #title>库存查询</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/inventory/in')" index="/inventory/in">
            <el-icon><Download /></el-icon>
            <template #title>入库管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/inventory/out')" index="/inventory/out">
            <el-icon><Upload /></el-icon>
            <template #title>出库管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/inventory/check')" index="/inventory/check">
            <el-icon><DocumentChecked /></el-icon>
            <template #title>库存盘点</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/warehouse')" index="/warehouse">
            <el-icon><OfficeBuilding /></el-icon>
            <template #title>仓库管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/inventory/logs')" index="/inventory/logs">
            <el-icon><List /></el-icon>
            <template #title>库存变动明细</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/inventory/transfer')" index="/inventory/transfer">
            <el-icon><Sort /></el-icon>
            <template #title>调拨管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/inventory/cost-adjust')" index="/inventory/cost-adjust">
            <el-icon><Money /></el-icon>
            <template #title>成本调价</template>
          </el-menu-item>
        </el-sub-menu>

        <!-- 5. 财务管理 -->
        <el-sub-menu v-if="hasGroupPermission('finance')" index="/finance">
          <template #title>
            <el-icon><Money /></el-icon>
            <span>财务管理</span>
          </template>
          <el-menu-item v-if="hasMenuPermission('/finance/receivables')" index="/finance/receivables">
            <el-icon><Wallet /></el-icon>
            <template #title>应收管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/finance/payables')" index="/finance/payables">
            <el-icon><CreditCard /></el-icon>
            <template #title>应付管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/finance')" index="/finance">
            <el-icon><Wallet /></el-icon>
            <template #title>账户管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/finance/receipt')" index="/finance/receipt">
            <el-icon><CreditCard /></el-icon>
            <template #title>收款管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/finance/payment')" index="/finance/payment">
            <el-icon><BankCard /></el-icon>
            <template #title>付款管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/finance/salary')" index="/finance/salary">
            <el-icon><Money /></el-icon>
            <template #title>工资发放</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/finance/expense')" index="/finance/expense">
            <el-icon><Wallet /></el-icon>
            <template #title>费用管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/finance/statistics')" index="/finance/statistics">
            <el-icon><TrendCharts /></el-icon>
            <template #title>业绩统计</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/finance/reconciliation')" index="/finance/reconciliation">
            <el-icon><Document /></el-icon>
            <template #title>对账管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/invoice')" index="/invoice">
            <el-icon><Stamp /></el-icon>
            <template #title>发票管理</template>
          </el-menu-item>
        </el-sub-menu>

        <!-- 6. 往来单位管理 -->
        <el-sub-menu v-if="hasGroupPermission('partner')" index="/customer">
          <template #title>
            <el-icon><User /></el-icon>
            <span>往来单位管理</span>
          </template>
          <el-menu-item v-if="hasMenuPermission('/customer')" index="/customer">
            <el-icon><Avatar /></el-icon>
            <template #title>客户管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/supplier')" index="/supplier">
            <el-icon><OfficeBuilding /></el-icon>
            <template #title>供应商管理</template>
          </el-menu-item>
        </el-sub-menu>

        <!-- 7. 系统管理 -->
        <el-sub-menu v-if="hasGroupPermission('system')" index="/settings">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item v-if="hasMenuPermission('/settings/users')" index="/settings/users">
            <el-icon><UserFilled /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          <el-menu-item index="/settings/roles">
            <el-icon><User /></el-icon>
            <template #title>角色管理</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/settings/log')" index="/settings/log">
            <el-icon><Notebook /></el-icon>
            <template #title>操作日志</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/settings/category')" index="/settings/category">
            <el-icon><Menu /></el-icon>
            <template #title>商品分类</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/settings/unit')" index="/settings/unit">
            <el-icon><Grid /></el-icon>
            <template #title>计量单位</template>
          </el-menu-item>
          <el-menu-item v-if="hasMenuPermission('/settings/print')" index="/settings/print">
            <el-icon><Printer /></el-icon>
            <template #title>打印模版</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 头部 -->
      <el-header class="header">
        <div class="header-top">
          <div class="header-left">
            <el-icon class="collapse-icon" @click="isCollapse = !isCollapse">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item
                v-for="(item, index) in breadcrumbItems"
                :key="index"
                :to="item.to"
              >
                {{ item.label }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-avatar :size="32" icon="UserFilled" />
                <span class="username">{{ userStore.realName || userStore.username }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        </el-header>

      <!-- 主内容区 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

// 面包屑分组名映射
const groupLabelMap = {
  front: '前台管理',
  material: '物资管理',
  warehouse: '库房管理',
  finance: '财务管理',
  partner: '往来单位管理',
  system: '系统管理',
}

const getGroupByPath = (path) => {
  const code = menuPermissionMap[path]
  if (!code) return null
  for (const [group, codes] of Object.entries(groupPermissionMap)) {
    if (codes.includes(code)) return group
  }
  return null
}

const breadcrumbItems = computed(() => {
  const items = [{ label: '首页', to: '/' }]
  if (route.path === '/dashboard') return items
  const group = getGroupByPath(route.path)
  if (group && groupLabelMap[group]) {
    items.push({ label: groupLabelMap[group] })
  }
  if (route.meta?.title) {
    items.push({ label: route.meta.title })
  }
  return items
})

// 菜单权限code映射
const menuPermissionMap = {
  '/dashboard': 'dashboard:view',
  '/workorder': 'workorder:view',
  '/receive': 'receive:view',
  '/dispatch': 'dispatch:view',
  '/quote': 'quote:view',
  '/asset': 'asset:view',
  '/product': 'product:view',
  '/sales': 'sales:view',
  '/purchase': 'purchase:view',
  '/preorder': 'preorder:view',
  '/preorder/sale': 'preorder-sale:view',
  '/return': 'purchase-return:view',
  '/return/sale': 'sales-return:view',
  '/inventory': 'inventory:view',
  '/inventory/in': 'inventory-in:view',
  '/inventory/out': 'inventory-out:view',
  '/inventory/check': 'inventory-check:view',
  '/warehouse': 'warehouse:view',
  '/inventory/logs': 'inventory-log:view',
  '/inventory/transfer': 'transfer:view',
  '/inventory/cost-adjust': 'cost-adjust:view',
  '/customer': 'customer:view',
  '/supplier': 'supplier:view',
  '/finance/receivable': 'finance:view',
  '/finance/receivables': 'finance-receivable:view',
  '/finance/payable': 'finance:view',
  '/finance/payables': 'finance-payable:view',
  '/finance': 'finance:view',
  '/finance/receipt': 'finance:view',
  '/finance/payment': 'finance:view',
  '/finance/salary': 'finance:view',
  '/finance/expense': 'finance:view',
  '/finance/statistics': 'finance:view',
  '/finance/reconciliation': 'finance:view',
  '/invoice': 'finance:view',
  '/settings/users': 'settings-users:view',
  '/settings/roles': 'settings-roles:view',
  '/settings/log': 'settings-log:view',
  '/settings/category': 'settings-category:view',
  '/settings/unit': 'settings-unit:view',
  '/settings/print': 'settings-print:view',
}

// 菜单分组与权限code的映射
const groupPermissionMap = {
  front: ['workorder:view', 'receive:view', 'dispatch:view', 'quote:view', 'asset:view'],
  material: ['product:view', 'sales:view', 'purchase:view', 'preorder:view', 'preorder-sale:view', 'purchase-return:view', 'sales-return:view'],
  warehouse: ['inventory:view', 'inventory-in:view', 'inventory-out:view', 'inventory-check:view', 'warehouse:view', 'inventory-log:view', 'transfer:view', 'cost-adjust:view'],
  finance: ['finance:view', 'finance-receivable:view', 'finance-payable:view', 'invoice:view'],
  partner: ['customer:view', 'supplier:view'],
  system: ['settings-users:view', 'settings-roles:view', 'settings-log:view', 'settings-category:view', 'settings-unit:view', 'settings-print:view'],
}

/**
 * 检查单个菜单是否有权限
 */
const hasMenuPermission = (path) => {
  if (userStore.isAdmin) return true
  const permissionCode = menuPermissionMap[path]
  if (!permissionCode) return true // 没有配置权限code的菜单默认显示
  return userStore.hasPermission(permissionCode)
}

/**
 * 检查菜单分组是否有权限（组内任一子菜单有权限即显示）
 */
const hasGroupPermission = (group) => {
  if (userStore.isAdmin) return true
  const codes = groupPermissionMap[group]
  if (!codes) return true
  return codes.some(code => userStore.permissions.includes(code))
}

const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        userStore.logout()
        router.push('/login')
      }).catch(() => {})
      break
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100vh;
}

.aside {
  background: var(--menu-bg);
  transition: width 0.3s;

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 18px;
    font-weight: bold;
    background: #38006b;

    img {
      width: 32px;
      height: 32px;
      margin-right: 8px;
    }
  }

  .menu {
    border-right: none;
    background: transparent;

    :deep(.el-menu) {
      background: transparent;
    }

    :deep(.el-sub-menu__title),
    :deep(.el-menu-item) {
      color: #E1BEE7;

      &:hover {
        background: #6A1B9A;
      }

      &.is-active {
        color: #fff;
        background: var(--primary-color);
      }
    }
  }
}

.header {
  background: #fff;
  display: flex;
  flex-direction: column;
  padding: 0;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  height: auto !important;

  .header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    height: 60px;
  }

  .header-left {
    display: flex;
    align-items: center;

    .collapse-icon {
      font-size: 20px;
      cursor: pointer;
      margin-right: 20px;
      color: #666;

      &:hover {
        color: var(--primary-color);
      }
    }
  }

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      cursor: pointer;

      .username {
        margin: 0 8px;
        color: #333;
      }
    }
  }
}

.main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
