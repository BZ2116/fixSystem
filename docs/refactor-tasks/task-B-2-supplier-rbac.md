# Task B-2: supplier.py RBAC 加固

## 目标
关掉 supplier 蓝图"任何登录用户能改/删"的漏洞。

## 涉及文件
- `source-code/backend/app/blueprints/supplier.py`（8 个路由）

## 预先依赖
A 组（特别是 A-3）已完成。

## 改法
权限码从 `init_db.py:153-156` 行确认。

```python
from app.security import permission  # 加在 imports 区域
```

| 行号 | 方法 | 路径 | 加装饰器 |
|------|------|------|---------|
| 33 | GET | `/api/suppliers` | `@permission('supplier:view')` |
| 85 | GET | `/api/suppliers/<int:sid>` | `@permission('supplier:view')` |
| 99 | POST | `/api/suppliers` | `@permission('supplier:add')` |
| 136 | PUT | `/api/suppliers/<int:sid>` | `@permission('supplier:edit')` |
| 161 | DELETE | `/api/suppliers/<int:sid>` | `@permission('supplier:delete')` |
| 176 | GET | `/api/suppliers/export` | `@permission('supplier:view')` |
| 212 | POST | `/api/suppliers/import` | `@permission('supplier:add')` |
| 298 | POST | `/api/suppliers/batch-delete` | `@permission('supplier:delete')` |

## 不要碰
任何其他文件。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```
浏览器：以 `finance_test`（库管不在文档的可访问列表）登录 → POST `/api/suppliers` 应 403。

## 提交
```
feat(supplier): 后端 RBAC 加固

- 8 个路由加 @permission 装饰器
- 权限码：supplier:view / :add / :edit / :delete
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/supplier.py
```
