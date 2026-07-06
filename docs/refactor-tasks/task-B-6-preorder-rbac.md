# Task B-6: preorder.py RBAC 加固

## 目标
关掉 preorder 蓝图漏洞。

## 涉及文件
- `source-code/backend/app/blueprints/preorder.py`（7 个路由）

## 预先依赖
A-3 完成。

## 改法
权限码从 `init_db.py:113-115, 103-105` 行确认（`preorder` 采购预订 + `preorder-sale` 销售预订两个独立权限）。

```python
from app.security import permission
```

| 行号 | 方法 | 路径 | 加装饰器 |
|------|------|------|---------|
| 31 | GET | `/api/pre-orders` | `@permission('preorder:view')` |
| 65 | GET | `/api/pre-orders/<int:id>` | `@permission('preorder:view')` |
| 76 | POST | `/api/pre-orders` | `@permission('preorder:add')` |
| 125 | PUT | `/api/pre-orders/<int:id>` | `@permission('preorder:edit')` |
| 164 | DELETE | `/api/pre-orders/<int:id>` | `@permission('preorder:delete')` |
| 176 | POST | `/api/pre-orders/<int:id>/convert` | `@permission('preorder:edit')` |

**注意**：本蓝图只覆盖采购预订（preorder），销售预订（preorder-sale）在 `preorder.py` 同文件但路由前缀不同（路径带 `/sale` 子路径）。如未找到，参考 `init_db.py:103-105` 添加 `preorder-sale:*` 装饰器。

## 不要碰
任何其他文件。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```

## 提交
```
feat(preorder): 后端 RBAC 加固

- 6 个路由加 @permission 装饰器
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/preorder.py
```
