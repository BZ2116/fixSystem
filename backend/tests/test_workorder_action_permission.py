"""技师工作流 action 端点权限测试。

约束：
- 技师无权 settle / to-quote / to-sales / allocate-parts / change_status（即使工单 assigned 给技师本人）
- 技师 GET /api/dispatch/staff-list 响应里无 phone 字段
- admin 不受影响（'*' 通配符）

实现位置：app/services/permission_helpers.py
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


@pytest.fixture
def app():
    from app import create_app
    from extensions import db
    # 必须在 create_all 前 import 所有 model，否则 SQLAlchemy 不知道表结构
    from models.workorder import WorkOrder, WorkOrderPart  # noqa
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


def _make_workorder(db, wo_no: str, assigned_user_id: int, status: int = 0):
    from models.workorder import WorkOrder
    wo = WorkOrder(
        wo_no=wo_no,
        status=status,
        customer_name='客户',
        assigned_user_id=assigned_user_id,
    )
    db.session.add(wo)
    db.session.commit()
    return wo


# ============================================
# 1. 技师不能对 assigned 给自己的工单做高危操作
# ============================================

def test_tech_cannot_settle_own_workorder(app, db):
    """技师 POST /api/workorders/<own id>/settle → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-S', tech.id, status=3)  # 待结算

        client = app.test_client()
        res = client.post(f'/api/workorders/{wo.id}/settle', headers=headers, json={})
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_to_quote_own_workorder(app, db):
    """技师 POST /api/workorders/<own id>/to-quote → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-Q', tech.id, status=2)

        client = app.test_client()
        res = client.post(f'/api/workorders/{wo.id}/to-quote', headers=headers, json={})
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_to_sales_own_workorder(app, db):
    """技师 POST /api/workorders/<own id>/to-sales → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-X', tech.id, status=3)

        client = app.test_client()
        res = client.post(f'/api/workorders/{wo.id}/to-sales', headers=headers, json={})
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_allocate_parts_own_workorder(app, db):
    """技师 POST /api/workorders/<own id>/allocate-parts → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-A', tech.id, status=2)

        client = app.test_client()
        res = client.post(
            f'/api/workorders/{wo.id}/allocate-parts', headers=headers, json={}
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_change_status_own_workorder(app, db):
    """技师 POST /api/workorders/<own id>/status → 403（应使用 accept/finish 专用端点）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-CS', tech.id, status=1)

        client = app.test_client()
        res = client.post(
            f'/api/workorders/{wo.id}/status', headers=headers, json={'status': 2}
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 2. 技师应能改自己工单的"普通字段"（通过 PUT /api/workorders/<id>）
#    注：accept/finish/cancel 走专用端点
# ============================================

def test_tech_can_finish_own_workorder(app, db):
    """技师 POST /api/workorders/<own id>/finish → 200（使用 workorder:edit）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-F', tech.id, status=2)

        client = app.test_client()
        res = client.post(
            f'/api/workorders/{wo.id}/finish', headers=headers, json={}
        )
        # 200 表示成功；其他状态码表示完成逻辑需要更多字段
        assert res.status_code in (200, 400), (
            f'期望 200 或 400 (业务校验), 实际 {res.status_code}: {res.get_json()}'
        )
        assert res.status_code != 403, 'finish 端点不应被权限拦截'


def test_tech_can_accept_own_workorder(app, db):
    """技师 POST /api/workorders/<own id>/accept → 200。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-AC', tech.id, status=1)

        client = app.test_client()
        res = client.post(
            f'/api/workorders/{wo.id}/accept', headers=headers, json={}
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 3. dispatch staff-list 隐私：技师无 phone 字段
# ============================================

def test_tech_staff_list_no_phone(app, db):
    """技师 GET /api/dispatch/staff-list → 响应里无 phone 字段。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        # 造另一个 user
        from models.system import SysUser
        from werkzeug.security import generate_password_hash
        other = SysUser(
            username='other', password=generate_password_hash('x'),
            real_name='其他', phone='13800000000',
        )
        db.session.add(other)
        db.session.commit()

        client = app.test_client()
        res = client.get('/api/dispatch/staff-list', headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        items = data['data']
        assert len(items) > 0, '应至少有 1 个员工'
        for item in items:
            assert 'phone' not in item, f'技师响应不应含 phone: {item}'


def test_admin_staff_list_has_phone(app, db):
    """admin GET /api/dispatch/staff-list → 响应里有 phone 字段。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        from models.system import SysUser
        from werkzeug.security import generate_password_hash
        other = SysUser(
            username='other', password=generate_password_hash('x'),
            real_name='其他', phone='13800000000',
        )
        db.session.add(other)
        db.session.commit()

        client = app.test_client()
        res = client.get('/api/dispatch/staff-list', headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        items = data['data']
        assert len(items) > 0
        for item in items:
            assert 'phone' in item, f'admin 响应应含 phone: {item}'


# ============================================
# 4. admin 不被拦截（即使工单状态非法，业务校验 400，不是 403）
# ============================================

def test_admin_not_blocked_by_permission_on_settle(app, db):
    """admin POST /api/workorders/<id>/settle → 200 或 400（业务校验），不是 403。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        wo = _make_workorder(db, 'WO-ADM-S', admin.id, status=0)  # 状态非法

        client = app.test_client()
        res = client.post(f'/api/workorders/{wo.id}/settle', headers=headers, json={})
        # 业务校验失败 400 即可（状态不是待结算）；绝不能 403
        assert res.status_code in (200, 400), (
            f'期望 200/400, 实际 {res.status_code}: {res.get_json()}'
        )
        assert res.status_code != 403, 'admin 不应被权限拦截'
