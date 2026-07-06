# Task C-2: 商品 / 资产视图 v-permission 补全

## 目标
商品管理与资产管理视图，按权限藏按钮。

## 涉及文件
- `source-code/frontend/src/views/product/index.vue`
- `source-code/frontend/src/views/product/category.vue`（如果存在）
- `source-code/frontend/src/views/asset/index.vue`

## 预先依赖
B-3 + B-4 已完成。

## 改法

### product/index.vue

| 按钮 | 加 |
|------|-----|
| 新增商品 | `v-permission="'product:add'"` |
| 批量更新分类 | `v-permission="'product:edit'"` |
| 批量调价 | `v-permission="'product:edit'"` |
| 批量启/禁 | `v-permission="'product:edit'"` |
| 批量删除 | `v-permission="'product:delete'"` |
| 导入/导出 | `v-permission="'product:add'"` / `'product:view'` |
| 行内编辑 | `v-permission="'product:edit'"` |
| 行内删除 | `v-permission="'product:delete'"` |

### product/category.vue（如果存在）
| 按钮 | 加 |
|------|-----|
| 新增分类 | `v-permission="'settings-category:add'"` |
| 行内编辑 | `v-permission="'settings-category:edit'"` |
| 行内删除 | `v-permission="'settings-category:delete'"` |

### asset/index.vue

| 按钮 | 加 |
|------|-----|
| 新增资产 | `v-permission="'asset:add'"` |
| 导入 | `v-permission="'asset:add'"` |
| 导出 | `v-permission="'asset:view'"` |
| 行内编辑 | `v-permission="'asset:edit'"` |
| 行内删除 | `v-permission="'asset:delete'"` |
| 报废 | `v-permission="'asset:delete'"` |

## 不要碰
- 不要改 `<script>` 区域
- 不要改其他 .vue

## 验证
```bash
cd source-code/frontend
npm run build
```
浏览器：用 `finance_test` 进商品管理（财务无 product:*）→ 应看不到所有按钮。

## 提交
```
feat(frontend): 商品/资产视图加 v-permission
```

## 回滚
```bash
git checkout source-code/frontend/src/views/product/ \
          source-code/frontend/src/views/asset/
```
