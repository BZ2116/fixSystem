# Task D-1: customer / supplier / asset / product 蓝图 RBAC 测试

## 目标
给 B-1/B-2/B-3/B-4 新加的装饰器写集成测试。

## 涉及文件
新建 4 个测试文件，全部路径 `source-code/backend/tests/`。

## 预先依赖
B-1 ~ B-4 已完成。

## 改法

### 模式
参考 `source-code/backend/tests/test_cross_blueprint_permission.py` 的模板：
- 用 `@pytest.fixture` 创建 testing app
- `_make_user(db, username, perms, role_code)` 创建测试用户 + token
- 每个蓝图写 8 条测试（技师 4 条 CRUD + admin 4 条 CRUD 通过）

### 要写的测试文件

#### `tests/test_customer_permission.py`
```python
import pytest
TECH_PERMS = [...]  # 复制 init_db.py 里的 technician 权限码
ADMIN_PERMS = ['*']
# 测试：test_tech_cannot_{create,update,delete,export,import,batch_delete}_customer
# 测试：test_admin_can_{create,update,delete}_customer
```
8 条左右，每个 HTTP method 一条。

#### `tests/test_supplier_permission.py`
同上模式，URL 换 `/api/suppliers`。

#### `tests/test_asset_permission.py`
同上模式，URL 换 `/api/assets`，额外测 `/api/assets/<id>/scrap`。

#### `tests/test_product_permission.py`
同上模式，URL 换 `/api/products`，额外测 batch 类接口。

### 关键模板

```python
def test_tech_cannot_create_customer(app, db):
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/customers', headers=headers, json={
            'customer_name': '测试客户',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )
```

每个文件里的 `_make_user` 函数体可直接复制 `test_cross_blueprint_permission.py` 第 56-78 行。

## 不要碰
- 不要修改 `test_cross_blueprint_permission.py` 已有的测试
- 不要修改被测的蓝图代码（那是 B-1 ~ B-4 的任务）

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/test_customer_permission.py \
                          tests/test_supplier_permission.py \
                          tests/test_asset_permission.py \
                          tests/test_product_permission.py -v
```
应 100% 通过。

## 提交
```
test(rbac): customer/supplier/asset/product 蓝图 RBAC 测试

- 4 个测试文件仿照 test_cross_blueprint_permission 模式
- 每个 CRUD 方法 1 条 case（技师拒、admin 通过）
```

## 回滚
```bash
rm source-code/backend/tests/test_customer_permission.py \
   source-code/backend/tests/test_supplier_permission.py \
   source-code/backend/tests/test_asset_permission.py \
   source-code/backend/tests/test_product_permission.py
```
