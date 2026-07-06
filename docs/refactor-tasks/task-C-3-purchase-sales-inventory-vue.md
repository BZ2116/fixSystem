# Task C-3: 采购 / 销售 / 库存 / 仓库视图 v-permission

## 目标
业务量大的一组视图，按权限藏按钮。

## 涉及文件
- `source-code/frontend/src/views/purchase/index.vue`
- `source-code/frontend/src/views/purchase/invoices.vue`（如果存在）
- `source-code/frontend/src/views/sales/index.vue`
- `source-code/frontend/src/views/inventory/index.vue`
- `source-code/frontend/src/views/inventory/in.vue`
- `source-code/frontend/src/views/inventory/out.vue`
- `source-code/frontend/src/views/inventory/check.vue`
- `source-code/frontend/src/views/inventory/transfer.vue`
- `source-code/frontend/src/views/inventory/cost-adjust.vue`
- `source-code/frontend/src/views/warehouse/index.vue`
- `source-code/frontend/src/views/inventory/logs.vue`

## 预先依赖
B-6 + B-7 已完成。

## 改法（每个视图按其权限码）

| 视图 | 新增 | 导入 | 导出 | 行内编辑 | 行内删除/审核 | 业务动作 |
|------|------|------|------|----------|--------------|----------|
| purchase/index | `purchase:add` | `purchase:add` | `purchase:view` | `purchase:edit` | `purchase:delete` / `purchase:edit` | — |
| purchase/invoices | `purchase-invoice:add` | — | `purchase-invoice:view` | `purchase-invoice:edit` | — | — |
| sales/index | `sales:add` | `sales:add` | `sales:view` | `sales:edit` | `sales:delete` / `sales:edit` | — |
| inventory/index | — | — | `inventory:view` | — | — | — |
| inventory/in | `inventory-in:add` | — | `inventory-in:view` | `inventory-in:edit` | `inventory-in:edit` | — |
| inventory/out | `inventory-out:add` | — | `inventory-out:view` | `inventory-out:edit` | `inventory-out:edit` | — |
| inventory/check | `inventory-check:add` | — | `inventory-check:view` | `inventory-check:edit` | `inventory-check:edit` | — |
| inventory/transfer | `transfer:add` | — | `transfer:view` | `transfer:edit` | `transfer:edit` | — |
| inventory/cost-adjust | `cost-adjust:add` | — | `cost-adjust:view` | `cost-adjust:edit` | `cost-adjust:edit` | — |
| warehouse/index | `warehouse:add` | — | `warehouse:view` | `warehouse:edit` | `warehouse:delete` | — |
| inventory/logs | — | — | `inventory-log:view` | — | — | — |

**模板**：
```vue
<el-button :icon="Plus" v-permission="'purchase:add'" @click="handleAdd">新增采购</el-button>
```

## 不要碰
- 不要改 `<script>`
- 不要改 views 下业务逻辑

## 验证
```bash
cd source-code/frontend
npm run build
```
浏览器：用 `test1`（技师）进入这些页面应看不到所有按钮（技师没有 inventory:* 写入权限）。

## 提交
```
feat(frontend): 采购/销售/库存/仓库视图加 v-permission
```

## 回滚
```bash
git checkout source-code/frontend/src/views/purchase/ \
          source-code/frontend/src/views/sales/ \
          source-code/frontend/src/views/inventory/ \
          source-code/frontend/src/views/warehouse/
```
