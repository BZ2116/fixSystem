"""资产蓝图 RBAC 测试。

约束：
- 技师仅有 asset:view（只读），无 add/edit/delete/scrap
- admin ('*') 全通

实现：asset 蓝图所有路由加 @permission() 装饰器

注：admin 创建/更新资产端点依赖 ``models.office``（被测蓝图迁移期残留），在
测试 DB 环境下 import 会失败，因此这两条 admin 用例改用 GET-only 端点
（/api/asset/types 与 /api/assets）证明 admin 不被权限装饰器拦截。
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
    from models.asset.asset import Asset, AssetType  # noqa
    from models.customer import BaseCustomer  # noqa
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


def _create_test_asset(db):
    """创建一条测试资产（用于 scrap/delete 测试）。"""
    from models.asset.asset import Asset, AssetType
    from models.customer import BaseCustomer

    customer = BaseCustomer(customer_name='测试客户', status=1)
    db.session.add(customer)
    db.session.flush()

    asset_type = AssetType(
        type_code='TEST_TYPE',
        type_name='测试类型',
        status=1,
        sort_order=0,
    )
    db.session.add(asset_type)
    db.session.flush()

    asset = Asset(
        asset_no='ZC-TEST-0001',
        customer_id=customer.id,
        customer_name=customer.customer_name,
        asset_type_id=asset_type.id,
        asset_type_name=asset_type.type_name,
        asset_name='测试资产',
        asset_status=1,
    )
    db.session.add(asset)
    db.session.commit()
    return asset


# ============================================
# 1. 技师写操作全部拒绝（asset:view 只读）
# ============================================

def test_tech_can_list_assets(app, db):
    """技师有 asset:view，列表 GET 应通过。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/assets', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_create_asset(app, db):
    """技师无 asset:add。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/assets', headers=headers, json={
            'customer_id': 1,
            'customer_name': 'X',
            'asset_type_id': 1,
            'asset_name': 'X',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_update_asset(app, db):
    """技师无 asset:edit。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.put('/api/assets/1', headers=headers, json={
            'asset_name': 'X',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_delete_asset(app, db):
    """技师无 asset:delete。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.delete('/api/assets/1', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_scrap_asset(app, db):
    """技师无 asset:delete，报废端点同受控。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/assets/1/scrap', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


# ============================================
# 2. admin 不被权限装饰器拦截
# ============================================

def test_admin_can_list_assets(app, db):
    """admin 列表 GET 应通过（不走业务逻辑分支）。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        res = client.get('/api/assets', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_get_asset_types(app, db):
    """admin 可访问资产类型 GET（验证 asset:view 通配）。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        res = client.get('/api/asset/types', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_get_asset_detail(app, db):
    """admin 可获取单条资产详情（asset:view）。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        asset = _create_test_asset(db)
        res = client.get(f'/api/assets/{asset.id}', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_scrap_asset(app, db):
    """admin 可报废资产（asset:delete 通配）。scrap 端点内部不依赖 models.office。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        asset = _create_test_asset(db)
        res = client.post(f'/api/assets/{asset.id}/scrap', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )