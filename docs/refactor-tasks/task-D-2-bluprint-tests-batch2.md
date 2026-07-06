# Task D-2: dispatch / return_order / receive_actions 蓝图 RBAC 测试

## 目标
给 B-5/B-7/B-8 新加的装饰器写集成测试。

## 涉及文件
新建 3 个测试文件，全部路径 `source-code/backend/tests/`。

## 预先依赖
B-5 + B-7 + B-8 已完成。

## 改法

### `tests/test_dispatch_permission.py`
URL `/api/dispatch/*`，覆盖：
- test_tech_cannot_create_dispatch (`POST /api/dispatch/manual` 应 403)
- test_tech_cannot_redirect (`POST /api/dispatch/<id>/redirect` 应 403)
- test_tech_can_view_dispatch (`GET /api/dispatch/pending` 应 200，因为技师有 dispatch:view)
- test_admin_can_dispatch_*

### `tests/test_return_order_permission.py`
URL `/api/return-orders/*`：
- test_tech_cannot_create_return
- test_finance_can_view_return（财务应有 finance 相关权限但返单不在 finance 里 —— 看 init_db.py 确认财务是否有 purchase-return:view：**没有**，财务只有 purchase:view；这意味着财务也读不到返单，是符合产品定位的）
- test_warehouse_can_create_return（库管应能进）
- test_admin_can_*

### `tests/test_receive_actions_permission.py`
URL `/api/receiveorders/<id>/{detect,quote,finish,cancel,...}`：
- test_tech_can_detect（技师能检测：`POST /detect` 应 200）
- test_tech_cannot_cancel（技师不能取消：`POST /cancel` 应 403）
- test_warehouse_cannot_detect（库管不能检测：`POST /detect` 应 403）

模式同 D-1。

## 不要碰
- 不要修改被测蓝图代码（那是 B-5/B-7/B-8 的任务）
- 不要改 `test_cross_blueprint_permission.py`

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/test_dispatch_permission.py \
                          tests/test_return_order_permission.py \
                          tests/test_receive_actions_permission.py -v
```

## 提交
```
test(rbac): dispatch/return-order/receive-actions 蓝图 RBAC 测试
```

## 回滚
```bash
rm source-code/backend/tests/test_dispatch_permission.py \
   source-code/backend/tests/test_return_order_permission.py \
   source-code/backend/tests/test_receive_actions_permission.py
```
