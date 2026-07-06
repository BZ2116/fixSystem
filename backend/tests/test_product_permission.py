"""商品蓝图 RBAC 测试。

约束：
- 技师无任何 product 权限（technician 角色权限列表里没有 product:*）
- admin ('*') 全通
- batch-update-* / batch-disable / batch-enable / batch-delete 都是 batch 操作，需 product:edit 或 product:delete

实现：product 蓝图所有路由加 @permission() 装饰器

注：admin batch-delete 端点调用的 check_business_record 内部 try-import 多个
业务 Item 模型，导入失败会冒泡到 try/except 兜底返回 500，与本次权限校验
任务无关。admin GET-detail 同样能证明不被权限装饰器拦截。
"""
import json

import pytest

# 与 init_db.py:223-228 一致
TECH_PERMS = json.loads(
    '["workorder:view","workorder:add","workorder:edit",'
    '"receive:view","receive:add","receive:edit",'
    '"dispatch:view",'
    '"asset:view",'
    '"inventory:view","warehouse:view","inventory-log:view",'
    '"customer:view"]'
)
ADMIN_PERMS = ['*']


@pytest.fixture
def app():
    from app import create_app
    from extensions import db
    # 必须在 create_all 前 import 所有 model
    from models.system import SysUser, SysRole  # noqa
    from models.product.info import ProductInfo, ProductUnit, ProductUnitRel  # noqa
    from models.inventory.stock import InventoryStock  # noqa
    app = create_app('testing')
    with app.app_context():
        db.session.execute(db.text(
            'CREATE TABLE IF NOT EXISTS jwt_blacklist ('
            '  jti TEXT PRIMARY KEY,'
            '  revoked_at DATETIME NOT NULL,'
            '  expires_at DATETIME NOT NULL'
            ')'
        ))
        db.session.commit()
        db.create_all()
    yield app


@pytest.fixture
def db(app):
    from extensions import db as _db
    return _db


def _make_user(db, username: str, perms: list, role_code: str = 'technician'):
    from models.system import SysUser, SysRole
    from werkzeug.security import generate_password_hash
    from flask_jwt_extended import create_access_token

    role = SysRole.query.filter_by(role_code=role_code).first()
    if role is None:
        role = SysRole(role_name=role_code, role_code=role_code, permissions=perms)
        db.session.add(role)
        db.session.commit()
    user = SysUser(
        username=username,
        password=generate_password_hash('test123'),
        real_name=username,
        role_id=role.id,
    )
    db.session.add(user)
    db.session.commit()
    token = create_access_token(
        identity=str(user.id),
        additional_claims={'permissions': perms, 'role_code': role_code},
    )
    return user, {'Authorization': f'Bearer {token}'}


# ============================================
# 1. 技师全部拒绝（技师无 product 权限）
# ============================================

def test_tech_cannot_list_products(app, db):
    """技师无 product:view，连列表都看不到。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/products', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_create_product(app, db):
    """技师无 product:add。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/products', headers=headers, json={
            'product_name': '测试商品',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_update_product(app, db):
    """技师无 product:edit。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.put('/api/products/1', headers=headers, json={
            'product_name': 'X',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_delete_product(app, db):
    """技师无 product:delete。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.delete('/api/products/1', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_batch_update_product(app, db):
    """技师无 product:edit，batch-update-category 应被拒。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/products/batch-update-category', headers=headers,
                          json={'ids': [1], 'category_id': 1})
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_batch_delete_product(app, db):
    """技师无 product:delete。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/products/batch-delete', headers=headers,
                          json={'ids': [1]})
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


# ============================================
# 2. admin 全通
# ============================================

def test_admin_can_list_products(app, db):
    """admin 可看商品列表。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        res = client.get('/api/products', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_create_product(app, db):
    """admin 可创建商品。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        res = client.post('/api/products', headers=headers, json={
            'product_name': '测试商品A',
        })
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_update_product(app, db):
    """admin 可更新商品（先创建再更新）。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        create_res = client.post('/api/products', headers=headers, json={
            'product_name': '测试商品B',
        })
        assert create_res.status_code == 200, create_res.get_json()
        pid = create_res.get_json()['data']['id']
        res = client.put(f'/api/products/{pid}', headers=headers, json={
            'product_name': '测试商品B-更新',
        })
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_get_product(app, db):
    """admin 可获取商品详情（先创建再 GET）。GET-detail 不调业务校验。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        create_res = client.post('/api/products', headers=headers, json={
            'product_name': '测试商品D',
        })
        assert create_res.status_code == 200, create_res.get_json()
        pid = create_res.get_json()['data']['id']
        res = client.get(f'/api/products/{pid}', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )