# Task A-2: JWT 黑名单 fail-closed

## 目标
`check_revoked` 出错时视为已撤销而不是放行。

## 涉及文件
- `source-code/backend/app/security.py:30-40`

## 改法
原代码：
```python
except Exception:
    logger.warning('check_revoked DB error (fail-open)', exc_info=True)
    return False  # ← 放行
```

改为：
```python
except Exception:
    logger.error('check_revoked DB error (fail-closed)', exc_info=True)
    return True  # ← 已撤销
```
并把上面的 `logger.warning` 改为 `logger.error`。

## 不要碰
除 `security.py` 第 30-40 行以外的任何代码。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/test_jwt_revocation.py -x -v
```
期望所有 `test_jwt_*` 在 DB 异常场景下断言 401。

**额外手动验证**：
```python
.venv/Scripts/python.exe -c "
from unittest.mock import patch
import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app('testing')
with app.test_client() as c, app.app_context():
    from extensions import db
    # 模拟 DB 异常
    with patch('app.security.db') as mock_db:
        mock_db.session.execute.side_effect = Exception('mock db error')
        # revoke 后 token 应判 401
"
```

## 提交
```
fix(security): JWT 黑名单查询改 fail-closed

- security.py:40 return False → True
- DB 异常时认证降级为拒绝而非放行
```

## 回滚
把 security.py 的 `return True` 改回 `return False`。
