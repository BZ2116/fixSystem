# Task B-1: customer.py RBAC 加固

## 目标
关掉 customer 蓝图"任何登录用户能改/删"的漏洞。

## 涉及文件
- `source-code/backend/app/blueprints/customer.py`（8 个路由）

## 预先依赖
A 组（特别是 A-3）已完成。

## 改法
在每条路由前加 `@permission('xxx')`。权限码从 `app/scripts/init_db.py` 的 `PERMISSIONS` 列表第 148-151 行确认。

```python
from app.security import permission  # 加在 imports 区域
```

| 行号 | 方法 | 路径 | 加装饰器 |
|------|------|------|---------|
| 33 | GET | `/api/customers` | `@permission('customer:view')` |
| 89 | GET | `/api/customers/<int:cid>` | `@permission('customer:view')` |
| 103 | POST | `/api/customers` | `@permission('customer:add')` |
| 142 | PUT | `/api/customers/<int:cid>` | `@permission('customer:edit')` |
| 167 | DELETE | `/api/customers/<int:cid>` | `@permission('customer:delete')` |
| 181 | GET | `/api/customers/export` | `@permission('customer:view')` |
| 220 | POST | `/api/customers/import` | `@permission('customer:add')` |
| 316 | POST | `/api/customers/batch-delete` | `@permission('customer:delete')` |

加完后每条 `@jwt_required()` 下方紧跟 `@permission(...)`：

```python
@bp.route('', methods=['GET'])
@jwt_required()
@permission('customer:view')
def list_customers():
    ...
```

## 不要碰
- 不要改 `permission_helpers.py`、`auth.py`
- 不要改其他蓝图
- 不要动 `customer.py` 里 `@bp.route`/`@jwt_required` 之间以外的逻辑代码

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/test_cross_blueprint_permission.py -x -v
.venv/Scripts/python.exe -m pytest tests/ -x -v
```
浏览器：以 `finance_test` 登录 → POST `/api/customers` 应 403；以 `admin` 登录 → 应 200。

## 提交
```
feat(customer): 后端 RBAC 加固

- 8 个路由加 @permission 装饰器
- 权限码：customer:view / :add / :edit / :delete 按操作类别
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/customer.py
```
