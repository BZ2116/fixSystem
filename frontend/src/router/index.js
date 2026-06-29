import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '首页', icon: 'HomeFilled' }
      },
      {
        path: 'customer',
        name: 'Customer',
        component: () => import('@/views/customer/index.vue'),
        meta: { title: '客户管理', icon: 'UserFilled' }
      },
      {
        path: 'supplier',
        name: 'Supplier',
        component: () => import('@/views/supplier/index.vue'),
        meta: { title: '供应商管理', icon: 'OfficeBuilding' }
      },
      {
        path: 'product',
        name: 'Product',
        component: () => import('@/views/product/index.vue'),
        meta: { title: '商品管理', icon: 'GoodsFilled' }
      },
      {
        path: 'workorder',
        name: 'WorkOrder',
        component: () => import('@/views/workorder/index.vue'),
        meta: { title: '工单管理', icon: 'Tools' }
      },
      {
        path: 'receive',
        name: 'Receive',
        component: () => import('@/views/receive/index.vue'),
        meta: { title: '接件管理', icon: 'Document' }
      },
      {
        path: 'dispatch',
        name: 'Dispatch',
        component: () => import('@/views/dispatch/index.vue'),
        meta: { title: '派单管理', icon: 'Van' }
      },
      {
        path: 'quote',
        name: 'Quote',
        component: () => import('@/views/quote/index.vue'),
        meta: { title: '报价管理', icon: 'Tickets' }
      },
      {
        path: 'preorder',
        name: 'PreOrder',
        component: () => import('@/views/preorder/index.vue'),
        meta: { title: '采购预订', icon: 'Notebook' }
      },
      {
        path: 'preorder/sale',
        name: 'PreOrderSale',
        component: () => import('@/views/preorder/sale.vue'),
        meta: { title: '销售预订', icon: 'Notebook' }
      },
      {
        path: 'return',
        name: 'Return',
        component: () => import('@/views/return/index.vue'),
        meta: { title: '采购退货', icon: 'RefreshLeft' }
      },
      {
        path: 'return/sale',
        name: 'ReturnSale',
        component: () => import('@/views/return/sale.vue'),
        meta: { title: '销售退货', icon: 'RefreshLeft' }
      },
      {
        path: 'asset',
        name: 'Asset',
        component: () => import('@/views/asset/index.vue'),
        meta: { title: '资产管理', icon: 'Box' }
      },
      {
        path: 'invoice',
        name: 'Invoice',
        component: () => import('@/views/finance/invoice.vue'),
        meta: { title: '发票管理', icon: 'Stamp', group: 'finance' }
      },
      {
        path: 'purchase',
        name: 'Purchase',
        component: () => import('@/views/purchase/index.vue'),
        meta: { title: '采购管理', icon: 'ShoppingCart' }
      },
      {
        path: 'purchase/invoices',
        name: 'PurchaseInvoices',
        component: () => import('@/views/purchase/invoices.vue'),
        meta: { title: '采购发票', icon: 'Stamp', group: 'purchase' }
      },
      {
        path: 'sales',
        name: 'Sales',
        component: () => import('@/views/sales/index.vue'),
        meta: { title: '销售管理', icon: 'Sell' }
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('@/views/inventory/index.vue'),
        meta: { title: '库存查询', icon: 'Box' }
      },
      {
        path: 'inventory/in',
        name: 'InventoryIn',
        component: () => import('@/views/inventory/in.vue'),
        meta: { title: '入库管理', icon: 'Box' }
      },
      {
        path: 'inventory/out',
        name: 'InventoryOut',
        component: () => import('@/views/inventory/out.vue'),
        meta: { title: '出库管理', icon: 'Box' }
      },
      {
        path: 'inventory/check',
        name: 'InventoryCheck',
        component: () => import('@/views/inventory/check.vue'),
        meta: { title: '库存盘点', icon: 'Box' }
      },
      {
        path: 'warehouse',
        name: 'Warehouse',
        component: () => import('@/views/warehouse/index.vue'),
        meta: { title: '仓库管理', icon: 'OfficeBuilding', group: 'warehouse' }
      },
      {
        path: 'inventory/logs',
        name: 'InventoryLogs',
        component: () => import('@/views/inventory/logs.vue'),
        meta: { title: '库存变动明细', icon: 'List', group: 'warehouse' }
      },
      {
        path: 'inventory/transfer',
        name: 'Transfer',
        component: () => import('@/views/inventory/transfer.vue'),
        meta: { title: '调拨管理', icon: 'Sort', group: 'warehouse' }
      },
      {
        path: 'inventory/cost-adjust',
        name: 'CostAdjust',
        component: () => import('@/views/inventory/cost-adjust.vue'),
        meta: { title: '成本调价', icon: 'Money', group: 'warehouse' }
      },
      {
        path: 'finance',
        name: 'Finance',
        component: () => import('@/views/finance/index.vue'),
        meta: { title: '财务管理', icon: 'Money' }
      },
      {
        path: 'finance/receivable',
        name: 'FinanceReceivable',
        component: () => import('@/views/finance/receivable.vue'),
        meta: { title: '应收管理', icon: 'Money' }
      },
      {
        path: 'finance/receivables',
        name: 'FinanceReceivables',
        component: () => import('@/views/finance/receivables.vue'),
        meta: { title: '应收管理', icon: 'Wallet', group: 'finance' }
      },
      {
        path: 'finance/payable',
        name: 'FinancePayable',
        component: () => import('@/views/finance/payable.vue'),
        meta: { title: '应付管理', icon: 'Money' }
      },
      {
        path: 'finance/payables',
        name: 'FinancePayables',
        component: () => import('@/views/finance/payables.vue'),
        meta: { title: '应付管理', icon: 'CreditCard', group: 'finance' }
      },
      {
        path: 'finance/receipt',
        name: 'FinanceReceipt',
        component: () => import('@/views/finance/receipt.vue'),
        meta: { title: '收款管理', icon: 'Money' }
      },
      {
        path: 'finance/payment',
        name: 'FinancePayment',
        component: () => import('@/views/finance/payment.vue'),
        meta: { title: '付款管理', icon: 'Money' }
      },
      {
        path: 'finance/salary',
        name: 'FinanceSalary',
        component: () => import('@/views/finance/salary.vue'),
        meta: { title: '工资发放', icon: 'Money', group: 'finance' }
      },
      {
        path: 'finance/expense',
        name: 'FinanceExpense',
        component: () => import('@/views/finance/expense.vue'),
        meta: { title: '费用管理', icon: 'Money', group: 'finance' }
      },
      {
        path: 'finance/statistics',
        name: 'FinanceStatistics',
        component: () => import('@/views/finance/statistics.vue'),
        meta: { title: '业绩统计', icon: 'TrendCharts', group: 'finance' }
      },
      {
        path: 'finance/reconciliation',
        name: 'FinanceReconciliation',
        component: () => import('@/views/finance/reconciliation.vue'),
        meta: { title: '对账管理', icon: 'Document', group: 'finance' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/index.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      },
      {
        path: 'settings/category',
        name: 'SettingsCategory',
        component: () => import('@/views/settings/category.vue'),
        meta: { title: '商品分类', icon: 'Setting' }
      },
      {
        path: 'settings/unit',
        name: 'SettingsUnit',
        component: () => import('@/views/settings/unit.vue'),
        meta: { title: '计量单位', icon: 'Setting' }
      },
      {
        path: 'settings/print',
        name: 'SettingsPrint',
        component: () => import('@/views/settings/print.vue'),
        meta: { title: '打印模版', icon: 'Setting' }
      },
      {
        path: 'settings/users',
        name: 'SettingsUsers',
        component: () => import('@/views/settings/users.vue'),
        meta: { title: '用户管理', icon: 'Setting' }
      },
      {
        path: 'settings/roles',
        name: 'SettingsRoles',
        component: () => import('@/views/settings/roles.vue'),
        meta: { title: '角色管理', icon: 'User' }
      },
      {
        path: 'settings/log',
        name: 'SettingsLog',
        component: () => import('@/views/settings/log.vue'),
        meta: { title: '操作日志', icon: 'Setting' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.public) {
    next()
    return
  }
  
  if (!userStore.token) {
    next('/login')
    return
  }
  
  // 如果有token但没有用户信息，重新获取
  if (userStore.token && !userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }
  
  next()
})

export default router
