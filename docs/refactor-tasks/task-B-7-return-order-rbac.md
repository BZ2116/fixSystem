# Task B-7: return_order.py RBAC 加固

## 目标
关掉 return_order 蓝图漏洞（采购退货 + 销售退货）。

## 涉及文件
- `source-code/backend/app/blueprints/return_order.py`（7 个路由）

## 预先依赖
A-3 完成。

## 改法
权限码从 `init_db.py:117-119, 121-123` 行确认。`return_type=1` 采购退货对应 `purchase-return:*`，`return_type=2` 销售退货对应 `sales-return:*`。代码里有显式路由区分。

```python
from app.security import permission
```

| 行号 | 方法 | 路径 | 加装饰器 |
|------|------|------|---------|
| 43 | GET | `/api/return-orders` | `@permission('purchase-return:view', 'sales-return:view')` |
| 71 | GET | `/api/return-orders/<int:id>` | `@permission('purchase-return:view', 'sales-return:view')` |
| 82 | POST | `/api/return-orders` | `@permission('purchase-return:add', 'sales-return:add')` |
| 138 | POST | `/api/return-orders/<int:id>/audit` | `@permission('purchase-return:edit', 'sales-return:edit')` |
| 417 | POST | `/api/return-orders/<int:id>/stock-in` | `@permission('purchase-return:edit', 'sales-return:edit')` |
| 513 | DELETE | `/api/return-orders/<int:id>` | `@permission('purchase-return:delete', 'sales-return:delete')` |

`@permission(a, b)` 同时接受两个权限码，**任一通过即可**（`permission` 装饰器源码在 `security.py:164-178`）。

如果路由里靠 `return_type` 区分，业务逻辑已经分得很清，那一个 `@permission('purchase-return:*')` 就够了 —— **简化原则**：每个路由最低限度地给一个对应类目的 `view/add/edit/delete` 装饰器。

## 不要碰
任何其他文件。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```

## 提交
```
feat(return-order): 后端 RBAC 加固

- 6 个路由加 @permission 装饰器
- purchase-return 与 sales-return 权限码分离
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/return_order.py
```
