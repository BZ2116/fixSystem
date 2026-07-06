# Task C-1: 客户 / 供应商视图 v-permission 补全

## 目标
前端客户管理、供应商管理视图，按权限藏按钮。

## 涉及文件
- `source-code/frontend/src/views/customer/index.vue`
- `source-code/frontend/src/views/supplier/index.vue`

## 预先依赖
B-1 + B-2 已完成（不然改了也没意义，后端一挡 403）。

## 改法

### customer/index.vue
现状 65 行已有一个 `v-permission="'customer:delete'"`。

**待加位置**：

| 位置 | 按钮 | 加 |
|------|------|-----|
| 顶部工具栏 | 新增客户 | `v-permission="'customer:add'"` |
| 顶部工具栏 | 导入 | `v-permission="'customer:add'"` |
| 顶部工具栏 | 导出 | `v-permission="'customer:view'"` |
| 顶部工具栏 | 批量删除 | `v-permission="'customer:delete'"` |
| 表格行内 | 编辑 | `v-permission="'customer:edit'"` |

**模板**：
```vue
<el-button type="primary" :icon="Plus" v-permission="'customer:add'" @click="handleAdd">新增客户</el-button>
```

### supplier/index.vue
基本结构同 customer（Vue 项目里这两个视图大概率结构一致）。

**待加位置**：

| 按钮 | 加 |
|------|-----|
| 新增供应商 | `v-permission="'supplier:add'"` |
| 导入 | `v-permission="'supplier:add'"` |
| 导出 | `v-permission="'supplier:view'"` |
| 批量删除 | `v-permission="'supplier:delete'"` |
| 行内编辑 | `v-permission="'supplier:edit'"` |

## 不要碰
- 不要改 `<script>` 区域的方法体
- 不要改其他 .vue 文件
- 不要动 `directives/permission.js`（已有）

## 验证
```bash
cd source-code/frontend
npm run build
# 必须无 warning
```
浏览器：
- 用 `test1`（技师）登录 → 客户管理应只看到「新增/编辑/导入」隐藏，「导出」可见（技师有 view）；批量删除也看不到。
- 用 `admin` 登录 → 应全部按钮可见。

## 提交
```
feat(frontend): 客户/供应商视图加 v-permission

- customer/index.vue: 新增/编辑/删除/导入/导出按钮按权限藏
- supplier/index.vue: 同上
```

## 回滚
```bash
git checkout source-code/frontend/src/views/customer/index.vue \
          source-code/frontend/src/views/supplier/index.vue
```
