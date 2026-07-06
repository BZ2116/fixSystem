# Task B-5: dispatch.py RBAC 加固

## 目标
关掉 dispatch 蓝图漏洞（派单管理）。

## 涉及文件
- `source-code/backend/app/blueprints/dispatch.py`

## 预先依赖
**A-0（dispatch 三行 bug 修复）+ A-3** 都必须先完成。

## 改法
权限码从 `init_db.py:79-80` 行确认。

```python
from app.security import permission
```

| 行号 | 方法 | 路径 | 加装饰器 |
|------|------|------|---------|
| 67 | POST | `/api/dispatch/manual` | `@permission('dispatch:edit')` |
| 118 | POST | `/api/dispatch/<int:record_id>/accept` | `@permission('dispatch:edit')` |
| 145 | POST | `/api/dispatch/<int:record_id>/reject` | `@permission('dispatch:edit')` |
| 168 | POST | `/api/dispatch/<int:record_id>/arrive` | `@permission('dispatch:edit')` |
| 188 | POST | `/api/dispatch/<int:record_id>/finish` | `@permission('dispatch:edit')` |
| 215 | POST | `/api/dispatch/<int:record_id>/redirect` | `@permission('dispatch:edit')` |
| 263 | GET | `/api/dispatch/records` | `@permission('dispatch:view')` |
| 314 | GET | `/api/dispatch/records/<int:wo_id>` | `@permission('dispatch:view')` |
| 328 | GET | `/api/dispatch/logs/<int:wo_id>` | `@permission('dispatch:view')` |
| 342 | GET | `/api/dispatch/staff-list` | `@permission('dispatch:view')` |
| 378 | GET | `/api/dispatch/pending` | `@permission('dispatch:view')` |
| 439 | GET | `/api/dispatch/stats` | `@permission('dispatch:view')` |
| 480 | GET | `/api/dispatchorders/export` | `@permission('dispatch:view')` |

**注意**：A-0 已经修改了 410/411/422 三行；本任务不要触碰这些行（已经修好）。

## 不要碰
- `dispatch.py` 410-422 行（A-0 已修）
- 不要改 dispatch 函数体内逻辑
- 不要改其他蓝图

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```
浏览器：以 `test1`（技师）登录 → 进入派单管理（应仍可读 view）→ 试 `POST /api/dispatch/manual` 应 403。

## 提交
```
feat(dispatch): 后端 RBAC 加固

- 13 个路由加 @permission 装饰器
- view 类给技师只读；edit 类要求管理员或调度员
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/dispatch.py
```
