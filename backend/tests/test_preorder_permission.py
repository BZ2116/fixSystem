"""preorder 蓝图 RBAC 测试。

约束：
- preorder 是采购预订，使用 preorder:view / preorder:add / preorder:edit / preorder:delete
  （与销售预订 preorder-sale:* 分开；与采购 purchase:* 也分开）
- 技师无 preorder:* 权限，所有端点 403
- 库管有 purchase:view 但无 preorder:view，应 403
- admin '*' 通配符放行

涉及端点（来自 app/blueprints/preorder.py）：
- GET    /api/pre-orders           preorder:view
- GET    /api/pre-orders/<id>      preorder:view
- POST   /api/pre-orders           preorder:add
- PUT    /api/pre-orders/<id>      preorder:edit
- DELETE /api/pre-orders/<id>      preorder:delete
- POST   /api/pre-orders/<id>/convert  preorder:edit
"""
import json

import pytest

# 与 init_db.py 和现有 RBAC 测试一致：技师没有 preorder:* 权限。
TECH_PERMS = json.loads(
    '["workorder:view","workorder:add","workorder:edit",'
    '"receive:view","receive:add","receive:edit",'
    '"dispatch:view",'
    '"asset:view",'
    '"inventory:view","warehouse:view","inventory-log:view",'
    '"customer:view"]'
)

# 库管有 purchase:view（容易误以为能看 preorder），但 preorder:view 是独立权限码。
WAREHOUSE_PERMS = ['inventory:view', 'inventory-in:view', 'purchase:view']


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
    from models.inventory.flow import PreOrder, PreOrderItem  # noqa
    from models.purchase.order import PurchaseOrder, PurchaseOrderItem  # noqa
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


def _make_preorder(db, pre_no: str = 'PRE-RBAC-001'):
    """创建一条待处理预订单，方便 PUT/DELETE/CONVERT 端点测试用。"""
    from models.inventory.flow import PreOrder
    po = PreOrder(
        pre_no=pre_no,
        pre_type=1,
        customer_name='客户',
        supplier_name='供应商',
        status=0,
    )
    db.session.add(po)
    db.session.commit()
    return po


# ============================================
# 1. 技师无 preorder:* 权限 — 所有端点应 403
# ============================================

def test_tech_cannot_list_preorders(app, db):
    """技师 GET /api/pre-orders → 403（无 preorder:view）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.get('/api/pre-orders', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_get_preorder_detail(app, db):
    """技师 GET /api/pre-orders/<id> → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        po = _make_preorder(db)

        client = app.test_client()
        res = client.get(f'/api/pre-orders/{po.id}', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_create_preorder(app, db):
    """技师 POST /api/pre-orders → 403（无 preorder:add）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        client = app.test_client()
        res = client.post(
            '/api/pre-orders',
            headers=headers,
            json={'customer_name': 'X', 'items': []},
        )
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_update_preorder(app, db):
    """技师 PUT /api/pre-orders/<id> → 403（无 preorder:edit）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        po = _make_preorder(db)

        client = app.test_client()
        res = client.put(
            f'/api/pre-orders/{po.id}',
            headers=headers,
            json={'remark': '技师尝试改'},
        )
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_delete_preorder(app, db):
    """技师 DELETE /api/pre-orders/<id> → 403（无 preorder:delete）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        po = _make_preorder(db)

        client = app.test_client()
        res = client.delete(f'/api/pre-orders/{po.id}', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_tech_cannot_convert_preorder(app, db):
    """技师 POST /api/pre-orders/<id>/convert → 403（无 preorder:edit）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        po = _make_preorder(db)

        client = app.test_client()
        res = client.post(
            f'/api/pre-orders/{po.id}/convert',
            headers=headers,
            json={},
        )
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


# ============================================
# 2. 库管无 preorder:* 权限（即使有 purchase:view）
# ============================================

def test_warehouse_cannot_view_preorder(app, db):
    """库管 GET /api/pre-orders → 403。

    库管有 purchase:view，但 preorder:view 是独立权限码，库管不应有。
    此测试是 D-3 核心防回归点：防止后人把 preorder 折进 purchase 视图。
    """
    with app.app_context():
        wh, headers = _make_user(db, 'wh', WAREHOUSE_PERMS, role_code='warehouse')
        client = app.test_client()
        res = client.get('/api/pre-orders', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_warehouse_cannot_get_preorder_detail(app, db):
    """库管 GET /api/pre-orders/<id> → 403。"""
    with app.app_context():
        wh, headers = _make_user(db, 'wh', WAREHOUSE_PERMS, role_code='warehouse')
        po = _make_preorder(db)

        client = app.test_client()
        res = client.get(f'/api/pre-orders/{po.id}', headers=headers)
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


def test_warehouse_cannot_create_preorder(app, db):
    """库管 POST /api/pre-orders → 403。"""
    with app.app_context():
        wh, headers = _make_user(db, 'wh', WAREHOUSE_PERMS, role_code='warehouse')
        client = app.test_client()
        res = client.post(
            '/api/pre-orders',
            headers=headers,
            json={'customer_name': 'X', 'items': []},
        )
        assert res.status_code == 403, (
            f'期望 403, 实际 {res.status_code}: {res.get_json()}'
        )


# ============================================
# 3. admin '*' 通配符放行 — 任何端点都不会被权限拦截
# ============================================

def test_admin_can_list_preorders(app, db):
    """admin GET /api/pre-orders → 200。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        client = app.test_client()
        res = client.get('/api/pre-orders', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_create_preorder(app, db):
    """admin POST /api/pre-orders → 200（业务成功）。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        client = app.test_client()
        res = client.post(
            '/api/pre-orders',
            headers=headers,
            json={
                'pre_type': 1,
                'customer_name': 'admin 测试',
                'supplier_name': '供应商',
                'items': [],
            },
        )
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )
        assert res.status_code != 403, 'admin 不应被权限拦截'


def test_admin_can_update_preorder(app, db):
    """admin PUT /api/pre-orders/<id> → 200（业务校验通过），不是 403。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        po = _make_preorder(db)

        client = app.test_client()
        res = client.put(
            f'/api/pre-orders/{po.id}',
            headers=headers,
            json={'remark': 'admin 更新'},
        )
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_delete_preorder(app, db):
    """admin DELETE /api/pre-orders/<id> → 200，不是 403。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        po = _make_preorder(db)

        client = app.test_client()
        res = client.delete(f'/api/pre-orders/{po.id}', headers=headers)
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )


def test_admin_can_convert_preorder(app, db):
    """admin POST /api/pre-orders/<id>/convert → 200（业务成功），不是 403。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        po = _make_preorder(db)

        client = app.test_client()
        res = client.post(
            f'/api/pre-orders/{po.id}/convert',
            headers=headers,
            json={},
        )
        assert res.status_code == 200, (
            f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        )
