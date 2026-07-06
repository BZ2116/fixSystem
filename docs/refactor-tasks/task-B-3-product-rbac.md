# Task B-3: product.py RBAC 加固

## 目标
关掉 product 蓝图漏洞。

## 涉及文件
- `source-code/backend/app/blueprints/product.py`（14 个路由）

## 预先依赖
A-3 完成。

## 改法
权限码从 `init_db.py:93-96` 行确认。

```python
from app.security import permission
```

| 行号 | 方法 | 路径 | 加装饰器 |
|------|------|------|---------|
| 85 | GET | `''` | `@permission('product:view')` |
| 158 | GET | `/<int:pid>` | `@permission('product:view')` |
| 200 | POST | `''` | `@permission('product:add')` |
| 297 | PUT | `/<int:pid>` | `@permission('product:edit')` |
| 341 | DELETE | `/<int:pid>` | `@permission('product:delete')` |
| 360 | GET | `/export` | `@permission('product:view')` |
| 405 | POST | `/import` | `@permission('product:add')` |
| 548 | POST | `/batch-update-category` | `@permission('product:edit')` |
| 574 | POST | `/batch-update-price` | `@permission('product:edit')` |
| 603 | POST | `/batch-update-stock-warning` | `@permission('product:edit')` |
| 630 | POST | `/batch-update-sort` | `@permission('product:edit')` |
| 654 | POST | `/batch-disable` | `@permission('product:edit')` |
| 675 | POST | `/batch-enable` | `@permission('product:edit')` |
| 696 | POST | `/batch-delete` | `@permission('product:delete')` |

## 不要碰
任何其他文件。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```
浏览器：以 `finance_test` 登录 → POST `/api/products` 应 403（财务不应有 product:add）。

## 提交
```
feat(product): 后端 RBAC 加固

- 14 个路由加 @permission 装饰器
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/product.py
```
