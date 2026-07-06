# Task C-4: 派单视图 v-permission

## 目标
派单管理视图按权限藏按钮。

## 涉及文件
- `source-code/frontend/src/views/dispatch/index.vue`（如果存在）
- `source-code/frontend/src/views/workorder/index.vue`（如果里面有派单按钮）

## 预先依赖
B-5 已完成。

## 改法

### 派单相关按钮
| 按钮 | 加 |
|------|-----|
| 新建派单 | `v-permission="'dispatch:edit'"` |
| 改派 | `v-permission="'dispatch:edit'"` |
| 接受 / 拒绝 / 抵达 / 完成派单 | `v-permission="'dispatch:edit'"` |

只读的列表页（视图主体）应被技师可见（技师有 `dispatch:view`），没有 view 的角色连菜单都看不到（前置 MainLayout.vue 过滤）。

### 模板
```vue
<el-button type="primary" v-permission="'dispatch:edit'" @click="handleDispatch">派单</el-button>
```

## 不要碰
- 不要改 `<script>`
- 不要改其他 .vue

## 验证
```bash
cd source-code/frontend
npm run build
```
浏览器：用 `test1` 登录 → 进派单管理应看不到新建/改派按钮（技师无 dispatch:edit）。

## 提交
```
feat(frontend): 派单视图加 v-permission
```

## 回滚
```bash
git checkout source-code/frontend/src/views/dispatch/
```
