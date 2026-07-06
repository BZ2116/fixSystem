# Task D-3: preorder 蓝图 RBAC 测试

## 目标
给 B-6 新加的 preorder 装饰器写集成测试。

## 涉及文件
新建 1 个测试文件 `source-code/backend/tests/test_preorder_permission.py`。

## 改法
URL `/api/pre-orders/*`：

- test_tech_cannot_list_preorders (GET 应 403，技师无 preorder:view)
- test_tech_cannot_create_preorder (POST 应 403)
- test_warehouse_cannot_view_preorder（库管应也 403；库管有 purchase:view 但 preorder:view 是独立的）
- test_admin_can_*

注：preorder 是采购预订，不是采购单，独立权限码。技师、库管都不应有这个权限。

## 不要碰
任何其他文件。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/test_preorder_permission.py -v
```

## 提交
```
test(rbac): preorder 蓝图 RBAC 测试
```

## 回滚
```bash
rm source-code/backend/tests/test_preorder_permission.py
```
