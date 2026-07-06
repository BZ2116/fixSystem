# Agent 任务分发索引

> **使用方式**：每次派发 = `CONTEXT.md` + 当前任务 md。两个文件一起喂给 agent。

## 依赖图

```
Stage A（4 个，可独立并行）
├── A-0 dispatch 三行 bug
├── A-1 JWT secret 升级
├── A-2 JWT fail-closed
└── A-3 token 加 permissions 字段

Stage B（9 个 RBAC，A 全完后可全并发）
├── B-1 customer
├── B-2 supplier
├── B-3 product
├── B-4 asset
├── B-5 dispatch    ← 还要等 A-0
├── B-6 preorder
├── B-7 return_order
├── B-8 receive_actions
└── B-9 settings

Stage C（5 个前端 v-permission，B 完成后可分批）
├── C-1 客户 / 供应商
├── C-2 商品 / 资产
├── C-3 采购 / 销售 / 库存 / 仓库
├── C-4 派单
└── C-5 财务子页

Stage D（3 个测试，与 B 并行）
├── D-1 customer / supplier / asset / product 测试
├── D-2 dispatch / return_order / receive_actions 测试
└── D-3 preorder 测试

Stage E（2 个辅助，任何时候可发）
├── E-1 backend/.env.example 清理
└── E-2 init_db.py 加 --force
```

## Stage A：基础设施修复（必须先全部完成）

| 任务 | 文件 | 依赖 |
|------|------|------|
| A-0 | `task-A-0-dispatch-bug.md` | 独立 |
| A-1 | `task-A-1-jwt-secret.md` | 独立 |
| A-2 | `task-A-2-jwt-fail-closed.md` | 独立 |
| A-3 | `task-A-3-token-claims.md` | 独立 |

## Stage B：后端 RBAC（A 全完后可全并发）

| 任务 | 蓝图 | 文件 |
|------|------|------|
| B-1 | customer | `task-B-1-customer-rbac.md` |
| B-2 | supplier | `task-B-2-supplier-rbac.md` |
| B-3 | product | `task-B-3-product-rbac.md` |
| B-4 | asset | `task-B-4-asset-rbac.md` |
| B-5 | dispatch | `task-B-5-dispatch-rbac.md`（等 A-0 完成） |
| B-6 | preorder | `task-B-6-preorder-rbac.md` |
| B-7 | return_order | `task-B-7-return-order-rbac.md` |
| B-8 | receive_actions | `task-B-8-receive-actions-rbac.md` |
| B-9 | settings | `task-B-9-settings-rbac.md` |

## Stage C：前端 v-permission（B 完成后分批）

| 任务 | 模块组 | 文件 |
|------|--------|------|
| C-1 | 客户 / 供应商 | `task-C-1-customer-supplier-vue.md` |
| C-2 | 商品 / 资产 | `task-C-2-product-asset-vue.md` |
| C-3 | 采购 / 销售 / 库存 / 仓库 | `task-C-3-purchase-sales-inventory-vue.md` |
| C-4 | 派单 | `task-C-4-dispatch-vue.md` |
| C-5 | 财务子页 | `task-C-5-finance-vue.md` |

## Stage D：测试（B 完成后并行）

| 任务 | 涵盖 | 文件 |
|------|------|------|
| D-1 | customer / supplier / asset / product | `task-D-1-bluprint-tests-batch1.md` |
| D-2 | dispatch / return_order / receive_actions | `task-D-2-bluprint-tests-batch2.md` |
| D-3 | preorder | `task-D-3-preorder-tests.md` |

## Stage E：辅助任务（任何时候可发）

| 任务 | 改 | 文件 |
|------|-----|------|
| E-1 | backend/.env.example 清理 | `task-E-1-env-example-cleanup.md` |
| E-2 | init_db.py 加 --force | `task-E-2-init-db-force.md` |

## 怎么分发

1. 从 Stage A 开始，按表派发 4 个 agent，每个收到 `CONTEXT.md` + 任务 md。
2. A-0/A-1/A-2/A-3 之间无依赖，**同一批发出**。
3. Stage A 全部回报后，从 Stage B 派发（最多 9 个 agent，**B-5 等 A-0 完成**）。
4. Stage D 测试可在 Stage B 派发的同时发出（独立写新测试文件，不冲突）。
5. Stage C 前端在 Stage B 后分批发（C-1 ~ C-5）。
6. 全部完成后跑 `REFACTOR_PLAN.md` 末尾的"收尾验证清单"。
