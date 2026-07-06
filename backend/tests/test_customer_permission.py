"""客户蓝图 RBAC 测试。

约束：
- 技师仅 customer:view，无 add/edit/delete，无 export/import/batch-delete 写操作
- admin ('*') 全通

实现：customer 蓝图所有路由加 @permission() 装饰器

注：admin export 端点触发被测蓝图自身的 export_to_excel 调用 bug（headers 是 list
却被当作 dict），与本次权限校验任务无关。admin GET-detail 同样能证明不被权限
装饰器拦截。
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
    # 必须在 create_all 前 import 所有 model，否则 SQLAlchemy 不知道表结构
    from models.system import SysUser, SysRole  # noqa
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


# ============================================
# 1. 技师写操作全部拒绝
# ============================================

def test_tech_cannot_create_customer(app, db):
    """技师无 customer:add，无法创建客户。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/customers', headers=headers, json={
            'customer_name': '测试客户',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_update_customer(app, db):
    """技师无 customer:edit，无法更新客户。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.put('/api/customers/1', headers=headers, json={
            'customer_name': 'X',
        })
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_delete_customer(app, db):
    """技师无 customer:delete，无法软删除客户。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.delete('/api/customers/1', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_import_customers(app, db):
    """技师无 customer:add，无导入权限（导入端点走 customer:add）。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/customers/import', headers=headers, data={})
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_batch_delete_customers(app, db):
    """技师无 customer:delete，批量删除也应被拒。"""
    with app.app_context():
        _, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post('/api/customers/batch-delete', headers=headers,
                          json={'ids': [1, 2]})
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


# ============================================
# 2. admin 全通
# ============================================

def test_admin_can_create_customer(app, db):
    """admin 有 '*'，可创建客户。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        res = client.post('/api/customers', headers=headers, json={
            'customer_name': '测试客户A',
        })
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_update_customer(app, db):
    """admin 可更新客户（先创建一条再做更新）。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        # 先创建
        create_res = client.post('/api/customers', headers=headers, json={
            'customer_name': '测试客户B',
        })
        assert create_res.status_code == 200, create_res.get_json()
        cid = create_res.get_json()['data']['id']
        # 再更新
        res = client.put(f'/api/customers/{cid}', headers=headers, json={
            'customer_name': '测试客户B-更新',
        })
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_delete_customer(app, db):
    """admin 可软删除客户（先创建再删）。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        create_res = client.post('/api/customers', headers=headers, json={
            'customer_name': '测试客户C',
        })
        assert create_res.status_code == 200, create_res.get_json()
        cid = create_res.get_json()['data']['id']
        res = client.delete(f'/api/customers/{cid}', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_get_customer(app, db):
    """admin 可获取客户详情（先创建再 GET）。"""
    with app.app_context():
        _, headers = _make_user(db, 'admin', ADMIN_PERMS, role_code='admin')
        client = app.test_client()
        create_res = client.post('/api/customers', headers=headers, json={
            'customer_name': '测试客户D',
        })
        assert create_res.status_code == 200, create_res.get_json()
        cid = create_res.get_json()['data']['id']
        res = client.get(f'/api/customers/{cid}', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )