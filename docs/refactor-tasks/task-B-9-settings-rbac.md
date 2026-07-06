# Task B-9: settings.py RBAC 加固（用户/角色管理）

## 目标
用户与角色管理接口加 RBAC，避免非 admin 能查/改用户列表。

## 涉及文件
- `source-code/backend/app/blueprints/settings.py`（29 处 @permission 已在）
- `source-code/backend/app/blueprints/users_admin.py`（1 处，user 列表）
- `source-code/backend/app/blueprints/user.py`（1 处 current user info）

**确认前提**：先 grep settings.py 是否已使用 `@permission`：
```bash
cd source-code/backend
grep -c "@permission" app/blueprints/settings.py
```

## 预先依赖
A-3 完成。

## 改法

### settings.py
每个路由前加 `@permission('settings-users:*')` 或 `@permission('settings-roles:*')` 或 `@permission('settings-category:*')` 等。

29 个路由的权限码列表见主方案 `REFACTOR_PLAN.md#P1-2` + `init_db.py:177-203`。

通用模板：
```python
@bp.route('/api/settings/users', methods=['GET'])
@jwt_required()
@permission('settings-users:view')
def list_users():
    ...
```

对应的 `add/edit/role/password/delete` 也按 `settings-users:add` / `:edit` / `:role` / `:password` / `:delete` 加。

### users_admin.py
第 10 行 GET `/api/users` 加 `@permission('settings-users:view')`：
```python
from app.security import permission

@bp.route('', methods=['GET'])
@jwt_required()
@permission('settings-users:view')
def get_users():
    ...
```

### user.py（current user info）
第 11 行 GET `/api/user/info` 是**当前用户自己**看自己信息，应**不要**加 `@permission`（不加它也已经被 `@jwt_required` 守护，所有登录用户都可以查自己）。**保持不动**。

## 不要碰
- 不要改 `permission_helpers.py`
- 不要改 settings.py 里非用户/角色的部分（如 settings-category / settings-unit / settings-print / settings-log）—— 它们已经是 settings:*:view 装饰，加不加都成；如要全加也行，权限码主方案里都有

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```
浏览器：以 `test1`（技师）登录 → GET `/api/users` 应 403。

## 提交
```
feat(settings): 用户/角色管理加 RBAC

- settings.py 加 settings-users:*/settings-roles:* 装饰器
- users_admin.py 加 settings-users:view
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/settings.py \
          source-code/backend/app/blueprints/users_admin.py
```
