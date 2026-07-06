# Task A-3: 登录 token 带 permissions / role_code

## 目标
把 permissions / role_code 写进 JWT claims，并让 permission_helpers 在旧 token 缺字段时回退查库。

## 涉及文件
- `source-code/backend/app/blueprints/auth.py:53`（在文件最后 `import` 区域附近）
- `source-code/backend/app/services/permission_helpers.py:25-31`

## 改法

### 1. `auth.py` 第 53 行
原：
```python
access_token = create_access_token(identity=str(user.id))
```

改：
```python
access_token = create_access_token(
    identity=str(user.id),
    additional_claims={
        'permissions': permissions,
        'role_code': role_code,
    },
)
```

### 2. `permission_helpers.py` 的 `claims_to_perms`
原（行 25-31）：
```python
def claims_to_perms(claims) -> list:
    """从 JWT claims 提取 permissions 列表。"""
    if claims is None:
        return []
    if isinstance(claims, dict):
        return claims.get('permissions', []) or []
    return []
```

改为：
```python
def claims_to_perms(claims) -> list:
    """从 JWT claims 提取 permissions 列表。"""
    if claims is None or not isinstance(claims, dict):
        return []
    perms = claims.get('permissions') or []
    if perms:
        return perms
    # 旧 token 兼容：claims 缺 permissions 时回退查库
    from flask_jwt_extended import get_jwt_identity
    from models.system import SysUser, SysRole
    uid = get_jwt_identity()
    if uid:
        user = SysUser.query.get(int(uid))
        if user and user.role_id:
            role = SysRole.query.get(user.role_id)
            if role and role.permissions:
                return list(role.permissions)
    return perms
```

## 不要碰
除这两段以外的其他代码。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```
全部测试应仍通过。

**手动验证**：
1. 重启后端，`grep InsecureKeyLengthWarning data/logs/flask.log` 应 = 0（前提 A-1 已做完；如果 A-1 没做完，会看到 warning）。
2. 用 `test1` 登录（密码 123456）→ 复制返回的 token → 在 jwt.io 解码 → claims 应包含 `permissions` 与 `role_code: "technician"`。
3. 旧 token（如果还有保留）调任意 `@permission` 装饰的 API，仍能 200 通过（fallback 生效）。

## 提交
```
feat(auth): 登录 token 携带 permissions / role_code

- auth.py:53 增加 additional_claims
- permission_helpers.claims_to_perms 在缺字段时回退查库
- 旧 token 仍可用，升级期兼容
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/auth.py \
          source-code/backend/app/services/permission_helpers.py
```
