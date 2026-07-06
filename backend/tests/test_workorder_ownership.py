"""技师 ownership 隔离测试。

- 技师 A 只能看到/修改自己 assigned 的工单
- admin 通配符不受限
- 技师 A 试图改 B 的工单 → 403
"""
import json
from datetime import datetime

import pytest

# 与 init_db.py:213-267 一致
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
    """造一个用户，返回 (SysUser, Authorization header dict)。"""
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


def _make_workorder(db, wo_no: str, assigned_user_id: int):
    from models.workorder import WorkOrder
    wo = WorkOrder(
        wo_no=wo_no,
        status=0,
        customer_name='客户',
        assigned_user_id=assigned_user_id,
    )
    db.session.add(wo)
    db.session.commit()
    return wo


def test_tech_A_can_only_see_own_workorders(app, db):
    """技师 A 调 GET /api/workorders 只看到自己 assigned 的工单。"""
    with app.app_context():
        tech_a, headers_a = _make_user(db, 'tech_a', TECH_PERMS)
        tech_b, _ = _make_user(db, 'tech_b', TECH_PERMS)
        wo_a = _make_workorder(db, 'WO-A', assigned_user_id=tech_a.id)
        wo_b = _make_workorder(db, 'WO-B', assigned_user_id=tech_b.id)

        client = app.test_client()
        res = client.get('/api/workorders', headers=headers_a)
        assert res.status_code == 200
        data = res.get_json()
        items = data['data']['list']
        ids = [item['id'] for item in items]
        assert wo_a.id in ids, 'A 应看到自己工单'
        assert wo_b.id not in ids, 'A 不应看到 B 的工单'


def test_tech_A_cannot_view_Bs_workorder_detail(app, db):
    """技师 A 调 GET /api/workorders/<B的工单id> → 403。"""
    with app.app_context():
        tech_a, headers_a = _make_user(db, 'tech_a', TECH_PERMS)
        tech_b, _ = _make_user(db, 'tech_b', TECH_PERMS)
        wo_b = _make_workorder(db, 'WO-B', assigned_user_id=tech_b.id)

        client = app.test_client()
        res = client.get(f'/api/workorders/{wo_b.id}', headers=headers_a)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_A_cannot_update_Bs_workorder(app, db):
    """技师 A 调 PUT /api/workorders/<B的工单id> → 403。"""
    with app.app_context():
        tech_a, headers_a = _make_user(db, 'tech_a', TECH_PERMS)
        tech_b, _ = _make_user(db, 'tech_b', TECH_PERMS)
        wo_b = _make_workorder(db, 'WO-B', assigned_user_id=tech_b.id)

        client = app.test_client()
        res = client.put(
            f'/api/workorders/{wo_b.id}',
            headers=headers_a,
            json={'fault_desc': '试图改 B 的工单'},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_A_cannot_delete_Bs_workorder(app, db):
    """技师 A 调 DELETE /api/workorders/<B的工单id> → 403。"""
    with app.app_context():
        tech_a, headers_a = _make_user(db, 'tech_a', TECH_PERMS)
        tech_b, _ = _make_user(db, 'tech_b', TECH_PERMS)
        wo_b = _make_workorder(db, 'WO-B-2', assigned_user_id=tech_b.id)

        client = app.test_client()
        res = client.delete(f'/api/workorders/{wo_b.id}', headers=headers_a)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_can_update_own_workorder(app, db):
    """技师改自己的工单 → 200。"""
    with app.app_context():
        tech_a, headers_a = _make_user(db, 'tech_a', TECH_PERMS)
        wo = _make_workorder(db, 'WO-MINE', assigned_user_id=tech_a.id)

        client = app.test_client()
        res = client.put(
            f'/api/workorders/{wo.id}',
            headers=headers_a,
            json={'fault_desc': '更新自己的工单'},
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_admin_sees_all_workorders(app, db):
    """admin 通配符 * 应能看到所有工单。"""
    with app.app_context():
        admin, headers_admin = _make_user(db, 'admin', ['*'], role_code='admin')
        tech_a, _ = _make_user(db, 'tech_a', TECH_PERMS)
        tech_b, _ = _make_user(db, 'tech_b', TECH_PERMS)
        wo_a = _make_workorder(db, 'WO-A-2', assigned_user_id=tech_a.id)
        wo_b = _make_workorder(db, 'WO-B-3', assigned_user_id=tech_b.id)

        client = app.test_client()
        res = client.get('/api/workorders', headers=headers_admin)
        assert res.status_code == 200
        data = res.get_json()
        items = data['data']['list']
        ids = [item['id'] for item in items]
        assert wo_a.id in ids
        assert wo_b.id in ids


def test_admin_can_view_any_workorder_detail(app, db):
    """admin 调 GET 任意工单 → 200。"""
    with app.app_context():
        admin, headers_admin = _make_user(db, 'admin', ['*'], role_code='admin')
        tech_a, _ = _make_user(db, 'tech_a', TECH_PERMS)
        wo = _make_workorder(db, 'WO-ADMIN', assigned_user_id=tech_a.id)

        client = app.test_client()
        res = client.get(f'/api/workorders/{wo.id}', headers=headers_admin)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'
