# Task C-5: 财务子页视图 v-permission

## 目标
财务管理子页（应收/应付/收款/付款/工资/费用/对账/统计）按权限藏按钮。

## 涉及文件
- `source-code/frontend/src/views/finance/index.vue`
- `source-code/frontend/src/views/finance/receivable.vue`
- `source-code/frontend/src/views/finance/receivables.vue`
- `source-code/frontend/src/views/finance/payable.vue`
- `source-code/frontend/src/views/finance/payables.vue`
- `source-code/frontend/src/views/finance/receipt.vue`
- `source-code/frontend/src/views/finance/payment.vue`
- `source-code/frontend/src/views/finance/salary.vue`
- `source-code/frontend/src/views/finance/expense.vue`
- `source-code/frontend/src/views/finance/statistics.vue`
- `source-code/frontend/src/views/finance/reconciliation.vue`
- `source-code/frontend/src/views/finance/invoice.vue`

## 预先依赖
Stage B 已完成（finance.py 已经有 @permission）。

## 改法
权限码从 `init_db.py:159-174` 行确认。

| 子页 | 新增 | 编辑 | 审核 / 删除 |
|------|------|------|------------|
| finance/index | — | — | — |
| finance/receivable + receivables | `finance-receivable:add`（如果有） | `finance-receivable:edit` | — |
| finance/payable + payables | `finance-payable:add`（如果有） | `finance-payable:edit` | — |
| finance/receipt | `finance-receipt:add` | `finance-receipt:edit` | — |
| finance/payment | `finance-payment:add` | `finance-payment:edit` | — |
| finance/salary | `finance-salary:add` | `finance-salary:edit` | — |
| finance/expense | `finance-expense:add` | `finance-expense:edit` | — |
| finance/statistics | — | — | — |
| finance/reconciliation | `finance-reconciliation:add` | `finance-reconciliation:edit` | — |
| finance/invoice | `finance-invoice:add` | `finance-invoice:edit` | — |

注意：财务模块**没有 delete 权限**（文档明示），所有"删除"按钮应直接 `v-permission` 都不加，技师角色进不来，财务自己是不会删的。

### 模板
```vue
<el-button v-permission="'finance-receivable:edit'" @click="handleEdit(row)">编辑</el-button>
```

## 不要碰
- 不要改 `<script>`
- 不要改其他视图

## 验证
```bash
cd source-code/frontend
npm run build
```
浏览器：用 `admin` 登录 → 进财务应所有按钮可见；用 `test1`（技师）应进不来（菜单隐藏）。

## 提交
```
feat(frontend): 财务子页加 v-permission
```

## 回滚
```bash
git checkout source-code/frontend/src/views/finance/
```
