# Task B-8: receive_actions.py RBAC + 状态机权限区分

## 目标
接件单状态机 14 个动作路由（检测/报价/完工/外送修等）任何登录用户都能调，需补 RBAC。

## 涉及文件
- `source-code/backend/app/blueprints/receive_actions.py`（14 个路由）

## 预先依赖
A-3 完成。

## 改法
权限码从 `init_db.py:74-77` 行确认。

```python
from app.security import permission
```

**通用规则**：
- 接件单 CRUD 已存在的权限码（`receive:add` / `:edit` / `:delete`）足以覆盖大部分动作。
- `settle`（结算 → 生成销售/应收）权限更严，建议业务权限 + 财务权限双重校验。
- `cancel` 用 `receive:delete`。

| 行号 | 方法 | 路径 | 加装饰器 |
|------|------|------|---------|
| 54 | POST | `/detect` | `@permission('receive:edit')` |
| 125 | POST | `/quote` | `@permission('receive:edit')` |
| 174 | POST | `/confirm` | `@permission('receive:edit')` |
| 236 | POST | `/allocate` | `@permission('receive:edit')` |
| 283 | POST | `/finish` | `@permission('receive:edit')` |
| 337 | POST | `/test` | `@permission('receive:edit')` |
| 400 | POST | `/notify` | `@permission('receive:edit')` |
| 447 | POST | `/settle` | `@permission('receive:edit', 'finance:view')` |
| 489 | POST | `/complete` | `@permission('receive:edit')` |
| 527 | POST | `/external-send` | `@permission('receive:edit')` |
| 579 | POST | `/external-quote` | `@permission('receive:edit')` |
| 624 | POST | `/customer-quote` | `@permission('receive:edit')` |
| 673 | POST | `/external-confirm` | `@permission('receive:edit')` |
| 719 | POST | `/external-return` | `@permission('receive:edit')` |
| 797 | POST | `/external-retest` | `@permission('receive:edit')` |
| 860 | POST | `/cancel` | `@permission('receive:delete')` |

**附加优化（建议，但非必须）**：技师（technician）只能操作自己接的接件单。这需要在每个 handler 函数体里加：
```python
from app.services.permission_helpers import assert_can_modify_receiveorder

err = assert_can_modify_receiveorder(order, get_jwt(), action='edit')
if err:
    return err
```
（参考 `permission_helpers.py:178-197`）。**简化原则**：本任务只装饰器化，不加 ownership 校验（ownership 校验属于 P2-1 data_scope 显式化）。

## 不要碰
- 不要改 `permission_helpers.py`
- 不要改 `receive.py`（CRUD 已认证）
- 不要改函数体逻辑

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -x -v
```

## 提交
```
feat(receive-actions): 状态机 14 个动作加 RBAC 装饰器

- 全部给 receive:edit（除 cancel 给 receive:delete）
- settle 额外要求 finance:view（业务+财务双重）
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/receive_actions.py
```
