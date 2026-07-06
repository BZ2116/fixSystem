"""派单蓝图 (dispatch) RBAC 测试。

约束：
- 技师有 dispatch:view（可看 pending/records/logs/staff-list），但没有 dispatch:edit
  （manual/redirect/accept/reject/arrive/finish 都需 dispatch:edit）
- admin 通配符 '*' 不受任何端点限制

实现位置：app/blueprints/dispatch.py 中各端点的 @permission() 装饰器。
"""
import json

import pytest

# 与 init_db.py:213-230 一致：技师权限不含 dispatch:edit
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
    from models.dispatch.record import DispatchRecord, DispatchLog, StaffStatus  # noqa
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


def _make_workorder(db, wo_no: str, assigned_user_id=None, status: int = 0):
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


def _make_dispatch_record(db, wo_id: int, staff_id: int, staff_name: str):
    """创建一条派单记录，用于 redirect/accept/reject/finish 等操作。"""
    from models.dispatch.record import DispatchRecord
    rec = DispatchRecord(
        wo_id=wo_id,
        dispatch_type='manual',
        dispatcher_id=staff_id,
        dispatcher_name='派单人',
        staff_id=staff_id,
        staff_name=staff_name,
        staff_phone='13800000000',
        accept_status=0,
    )
    db.session.add(rec)
    db.session.commit()
    return rec


# ============================================
# 1. 技师被 dispatch:edit 端点拦截（manual / redirect）
# ============================================

def test_tech_cannot_create_dispatch(app, db):
    """技师 POST /api/dispatch/manual → 403（无 dispatch:edit）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        target, _ = _make_user(db, 'target', TECH_PERMS)
        wo = _make_workorder(db, 'WO-D', assigned_user_id=tech.id, status=0)

        client = app.test_client()
        res = client.post(
            '/api/dispatch/manual',
            headers=headers,
            json={'wo_id': wo.id, 'staff_id': target.id, 'remark': '技师试图派单'},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_redirect(app, db):
    """技师 POST /api/dispatch/<id>/redirect → 403（无 dispatch:edit）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        old_staff, _ = _make_user(db, 'old_staff', TECH_PERMS)
        new_staff, _ = _make_user(db, 'new_staff', TECH_PERMS)
        wo = _make_workorder(db, 'WO-D2', assigned_user_id=old_staff.id, status=1)
        rec = _make_dispatch_record(db, wo.id, old_staff.id, '旧技师')

        client = app.test_client()
        res = client.post(
            f'/api/dispatch/{rec.id}/redirect',
            headers=headers,
            json={'staff_id': new_staff.id, 'remark': '技师改派'},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_accept_dispatch(app, db):
    """技师 POST /api/dispatch/<id>/accept → 403（即使工单 assigned 给技师本人）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-D3', assigned_user_id=tech.id, status=1)
        rec = _make_dispatch_record(db, wo.id, tech.id, '技师自己')

        client = app.test_client()
        res = client.post(f'/api/dispatch/{rec.id}/accept', headers=headers, json={})
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_reject_dispatch(app, db):
    """技师 POST /api/dispatch/<id>/reject → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-D4', assigned_user_id=tech.id, status=1)
        rec = _make_dispatch_record(db, wo.id, tech.id, '技师自己')

        client = app.test_client()
        res = client.post(
            f'/api/dispatch/{rec.id}/reject',
            headers=headers,
            json={'reason': '技师拒单'},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_arrive_dispatch(app, db):
    """技师 POST /api/dispatch/<id>/arrive → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-D5', assigned_user_id=tech.id, status=3)
        rec = _make_dispatch_record(db, wo.id, tech.id, '技师自己')

        client = app.test_client()
        res = client.post(f'/api/dispatch/{rec.id}/arrive', headers=headers, json={})
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_finish_dispatch(app, db):
    """技师 POST /api/dispatch/<id>/finish → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-D6', assigned_user_id=tech.id, status=3)
        rec = _make_dispatch_record(db, wo.id, tech.id, '技师自己')

        client = app.test_client()
        res = client.post(f'/api/dispatch/{rec.id}/finish', headers=headers, json={})
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 2. 技师能查看派单（dispatch:view）
# ============================================

def test_tech_can_view_pending_dispatch(app, db):
    """技师 GET /api/dispatch/pending → 200（dispatch:view）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)

        client = app.test_client()
        res = client.get('/api/dispatch/pending', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_tech_can_view_records(app, db):
    """技师 GET /api/dispatch/records → 200。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)

        client = app.test_client()
        res = client.get('/api/dispatch/records', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_tech_can_view_staff_list(app, db):
    """技师 GET /api/dispatch/staff-list → 200。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)

        client = app.test_client()
        res = client.get('/api/dispatch/staff-list', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_tech_can_view_stats(app, db):
    """技师 GET /api/dispatch/stats → 200。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)

        client = app.test_client()
        res = client.get('/api/dispatch/stats', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 3. admin 不受限制
# ============================================

def test_admin_can_view_pending(app, db):
    """admin GET /api/dispatch/pending → 200。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')

        client = app.test_client()
        res = client.get('/api/dispatch/pending', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_admin_can_create_dispatch(app, db):
    """admin POST /api/dispatch/manual → 200（业务成功），不会被权限拦截。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        tech, _ = _make_user(db, 'tech', TECH_PERMS)
        wo = _make_workorder(db, 'WO-DA', assigned_user_id=None, status=0)

        client = app.test_client()
        res = client.post(
            '/api/dispatch/manual',
            headers=headers,
            json={'wo_id': wo.id, 'staff_id': tech.id, 'remark': 'admin 派单'},
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        assert res.get_json().get('code') == 200


def test_admin_can_redirect(app, db):
    """admin POST /api/dispatch/<id>/redirect → 200。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        old_staff, _ = _make_user(db, 'old_a', TECH_PERMS)
        new_staff, _ = _make_user(db, 'new_a', TECH_PERMS)
        wo = _make_workorder(db, 'WO-DA2', assigned_user_id=old_staff.id, status=1)
        rec = _make_dispatch_record(db, wo.id, old_staff.id, '旧技师')

        client = app.test_client()
        res = client.post(
            f'/api/dispatch/{rec.id}/redirect',
            headers=headers,
            json={'staff_id': new_staff.id, 'remark': 'admin 改派'},
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        assert res.get_json().get('code') == 200