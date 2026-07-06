# Task B-4: asset.py RBAC 加固

## 目标
关掉 asset 蓝图漏洞。

## 涉及文件
- `source-code/backend/app/blueprints/asset.py`（14 个路由）

## 预先依赖
A-3 完成。

## 改法
权限码从 `init_db.py:87-90` 行确认。

```python
from app.security import permission
```

| 行号 | 方法 | 路径 | 加装饰器 |
|------|------|------|---------|
| 79 | GET | `/api/asset/types` | `@permission('asset:view')` |
| 104 | GET | `/api/assets` | `@permission('asset:view')` |
| 180 | GET | `/api/assets/<int:id>` | `@permission('asset:view')` |
| 203 | POST | `/api/assets` | `@permission('asset:add')` |
| 289 | PUT | `/api/assets/<int:id>` | `@permission('asset:edit')` |
| 348 | DELETE | `/api/assets/<int:id>` | `@permission('asset:delete')` |
| 372 | POST | `/api/assets/<int:id>/scrap` | `@permission('asset:delete')` |
| 400 | POST | `/api/assets/import` | `@permission('asset:add')` |
| 505 | GET | `/api/assets/export` | `@permission('asset:view')` |
| 583 | GET | `/api/assets/by-customer` | `@permission('asset:view')` |
| 624 | POST | `/api/sales/orders/<int:order_id>/assets` | `@permission('sales:add')`（属销售功能） |
| 703 | POST | `/api/sales/returns/<int:return_id>/unbind-assets` | `@permission('sales-return:edit')` |
| 737 | GET | `/api/sales/orders/<int:order_id>/assets` | `@permission('sales:view')` |

## 不要碰
任何其他文件。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```

## 提交
```
feat(asset): 后端 RBAC 加固

- 14 个路由加 @permission 装饰器
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/asset.py
```
