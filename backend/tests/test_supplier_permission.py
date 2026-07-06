"""供应商蓝图 RBAC 测试。

约束：
- 技师无任何 supplier 权限
- admin ('*') 全通

实现：supplier 蓝图所有路由加 @permission() 装饰器
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
    from models.supplier import BaseSupplier  # noqa
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
# 1. 技师全部拒绝（技师无 supplier 权限）
# ============================================

def test_tech_cannot_list_suppliers(app, db):
    """技师无 supplier:view，连列表都看不到。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/suppliers', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_create_supplier(app, db):
    """技师无 supplier:add，无法创建。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/suppliers', headers=headers, json={
            'supplier_name': '测试供应商',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_update_supplier(app, db):
    """技师无 supplier:edit。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.put('/api/suppliers/1', headers=headers, json={
            'supplier_name': 'X',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_delete_supplier(app, db):
    """技师无 supplier:delete。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.delete('/api/suppliers/1', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_batch_delete_suppliers(app, db):
    """技师无 supplier:delete，批量删除应被拒。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/suppliers/batch-delete', headers=headers,
                          json={'ids': [1, 2]})
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


# ============================================
# 2. admin 全通
# ============================================

def test_admin_can_list_suppliers(app, db):
    """admin 可看列表。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        res = client.get('/api/suppliers', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_create_supplier(app, db):
    """admin 可创建供应商。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        res = client.post('/api/suppliers', headers=headers, json={
            'supplier_name': '测试供应商A',
        })
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_update_supplier(app, db):
    """admin 可更新供应商（先创建再更新）。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        create_res = client.post('/api/suppliers', headers=headers, json={
            'supplier_name': '测试供应商B',
        })
        assert create_res.status_code == 200, create_res.get_json()
        sid = create_res.get_json()['data']['id']
        res = client.put(f'/api/suppliers/{sid}', headers=headers, json={
            'supplier_name': '测试供应商B-更新',
        })
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_delete_supplier(app, db):
    """admin 可软删除供应商。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        create_res = client.post('/api/suppliers', headers=headers, json={
            'supplier_name': '测试供应商C',
        })
        assert create_res.status_code == 200, create_res.get_json()
        sid = create_res.get_json()['data']['id']
        res = client.delete(f'/api/suppliers/{sid}', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )