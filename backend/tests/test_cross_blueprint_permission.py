"""技师跨蓝图访问控制测试。

约束：
- 技师无权访问 quote / sales / purchase / finance / inventory (除 view) 等业务蓝图
- admin 不受影响

实现：各蓝图加 @permission() 装饰器
"""
import json

import pytest

TECH_PERMS = json.loads(
    '["workorder:view","workorder:add","workorder:edit",'
    '"receive:view","receive:add","receive:edit",'
    '"dispatch:view",'
    '"asset:view",'
    '"inventory:view","warehouse:view","inventory-log:view",'
    '"customer:view"]'
)


@pytest.fixture
def app():
    from app import create_app
    from extensions import db
    from models.workorder import WorkOrder  # noqa
    from models.receive import ReceiveOrder  # noqa
    from models.dispatch.record import DispatchRecord  # noqa
    from models.system import SysUser, SysRole  # noqa
    from models.quote import QuoteOrder  # noqa
    from models.sales import SalesOrder  # noqa
    from models.finance import FinanceAccount, FinanceRecord, FinanceReceivable  # noqa
    from models.product import ProductInfo  # noqa
    from models.inventory import InventoryOut, InventoryOutItem  # noqa
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
# 1. 技师无权 quote / sales / purchase / finance / inventory 业务列表
# ============================================

def test_tech_cannot_list_quotes(app, db):
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/quotes', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_list_sales_orders(app, db):
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/sales/orders', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_list_purchase_orders(app, db):
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/purchase/orders', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_list_finance_accounts(app, db):
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/finance/accounts', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_list_inventory_in(app, db):
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/inventory/in', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_list_inventory_out(app, db):
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/inventory/out', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 2. admin 不受影响
# ============================================

def test_admin_can_list_quotes(app, db):
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        client = app.test_client()
        res = client.get('/api/quotes', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_admin_can_list_sales_orders(app, db):
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        client = app.test_client()
        res = client.get('/api/sales/orders', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_admin_can_list_finance_accounts(app, db):
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        client = app.test_client()
        res = client.get('/api/finance/accounts', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_admin_can_list_inventory_in(app, db):
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        client = app.test_client()
        res = client.get('/api/inventory/in', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 3. 财务角色可访问 finance 蓝图（验证 finance 角色没被误伤）
# ============================================

def test_finance_can_list_finance_accounts(app, db):
    """finance 角色应有 finance:view，能访问财务蓝图。"""
    with app.app_context():
        finance_perms = ['finance:view', 'finance-receivable:view']
        finance, headers = _make_user(db, 'finance', finance_perms, role_code='finance')
        client = app.test_client()
        res = client.get('/api/finance/accounts', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 4. 库管角色可访问 inventory（验证库管没被误伤）
# ============================================

def test_warehouse_can_list_inventory_in(app, db):
    """warehouse 角色应有 inventory-in:view。"""
    with app.app_context():
        wh_perms = ['inventory-in:view']
        wh, headers = _make_user(db, 'wh', wh_perms, role_code='warehouse')
        client = app.test_client()
        res = client.get('/api/inventory/in', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'
