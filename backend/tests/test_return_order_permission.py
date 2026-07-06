"""退货单蓝图 (return_order) RBAC 测试。

约束（基于 scripts/init_db.py:213-267 实际权限矩阵）：
- 技师没有 purchase-return:* / sales-return:* → 全部 403
- 财务没有 purchase-return:* / sales-return:*（只看 purchase:view，不看退货单）
- 库管没有 purchase-return:* / sales-return:*（库管只做库存/采购，不做退货单）
- admin 通配符 '*' → 全通

实现位置：app/blueprints/return_order.py 各端点的 @permission() 装饰器。
"""
import json

import pytest

# 与 init_db.py:213-230 一致
TECH_PERMS = json.loads(
    '["workorder:view","workorder:add","workorder:edit",'
    '"receive:view","receive:add","receive:edit",'
    '"dispatch:view",'
    '"asset:view",'
    '"inventory:view","warehouse:view","inventory-log:view",'
    '"customer:view"]'
)

# 与 init_db.py:231-248 一致（财务：全套 finance + 业务单据查看，无 purchase-return）
FINANCE_PERMS = json.loads(
    '["finance:view","finance-statistics:view",'
    '"finance-receivable:view","finance-receivable:edit",'
    '"finance-payable:view","finance-payable:edit",'
    '"finance-receipt:view","finance-receipt:edit",'
    '"finance-payment:view","finance-payment:edit",'
    '"finance-salary:view","finance-salary:edit",'
    '"finance-expense:view","finance-expense:edit",'
    '"finance-reconciliation:view","finance-reconciliation:edit",'
    '"purchase:view","sales:view","inventory:view","workorder:view",'
    '"customer:view","supplier:view"]'
)

# 与 init_db.py:249-266 一致（库管：库存/商品/采购/仓库，无 purchase-return）
WAREHOUSE_PERMS = json.loads(
    '["inventory:view","inventory-in:view","inventory-in:add","inventory-in:edit",'
    '"inventory-out:view","inventory-out:add","inventory-out:edit",'
    '"inventory-check:view","inventory-check:add","inventory-check:edit",'
    '"warehouse:view","warehouse:add","warehouse:edit",'
    '"inventory-log:view",'
    '"transfer:view","transfer:add","transfer:edit",'
    '"cost-adjust:view","cost-adjust:add","cost-adjust:edit",'
    '"product:view","product:add","product:edit",'
    '"purchase:view","purchase:add","purchase:edit",'
    '"receive:view","workorder:view",'
    '"supplier:view"]'
)


@pytest.fixture
def app():
    from app import create_app
    from extensions import db
    from models.workorder import WorkOrder, WorkOrderPart  # noqa
    from models.receive import ReceiveOrder  # noqa
    from models.dispatch.record import DispatchRecord  # noqa
    from models.system import SysUser, SysRole  # noqa
    from models.quote import QuoteOrder  # noqa
    from models.sales import SalesOrder  # noqa
    from models.finance import FinanceAccount, FinanceRecord, FinanceReceivable  # noqa
    from models.product import ProductInfo  # noqa
    from models.inventory import InventoryOut, InventoryOutItem  # noqa
    from models.purchase.return_order import ReturnOrder, ReturnOrderItem  # noqa
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


def _make_return_order(db, return_no: str = 'R001', status: int = 0):
    """建一条退货单（待审核）以便触发 audit/stock-in/delete 端点。"""
    from models.purchase.return_order import ReturnOrder
    order = ReturnOrder(
        return_no=return_no,
        return_type=1,  # 采购退货
        related_order_id=1,
        related_order_no='PO-001',
        supplier_id=1,
        supplier_name='供应商',
        refund_amount=100,
        status=status,
        reason='退货测试',
        created_by=1,
    )
    db.session.add(order)
    db.session.commit()
    return order


# ============================================
# 1. 技师被全部端点拦截
# ============================================

def test_tech_cannot_list_returns(app, db):
    """技师 GET /api/return-orders → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)

        client = app.test_client()
        res = client.get('/api/return-orders', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_view_return_detail(app, db):
    """技师 GET /api/return-orders/<id> → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        ro = _make_return_order(db, 'R-Tech-V')

        client = app.test_client()
        res = client.get(f'/api/return-orders/{ro.id}', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_create_return(app, db):
    """技师 POST /api/return-orders → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)

        client = app.test_client()
        res = client.post(
            '/api/return-orders',
            headers=headers,
            json={
                'return_type': 1,
                'related_order_id': 1,
                'related_order_no': 'PO-001',
                'supplier_id': 1,
                'supplier_name': '供应商',
                'refund_amount': 100,
                'items': [],
            },
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_audit_return(app, db):
    """技师 POST /api/return-orders/<id>/audit → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        ro = _make_return_order(db, 'R-Tech-A')

        client = app.test_client()
        res = client.post(f'/api/return-orders/{ro.id}/audit', headers=headers, json={})
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_stock_in_return(app, db):
    """技师 POST /api/return-orders/<id>/stock-in → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        ro = _make_return_order(db, 'R-Tech-S', status=1)

        client = app.test_client()
        res = client.post(f'/api/return-orders/{ro.id}/stock-in', headers=headers, json={})
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_tech_cannot_delete_return(app, db):
    """技师 DELETE /api/return-orders/<id> → 403。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        ro = _make_return_order(db, 'R-Tech-D')

        client = app.test_client()
        res = client.delete(f'/api/return-orders/{ro.id}', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 2. 财务也读不到退货单（init_db.py 财务权限里没有 purchase-return:view）
# ============================================

def test_finance_cannot_list_returns(app, db):
    """财务 GET /api/return-orders → 403（与产品定位一致：财务不做退货单）。"""
    with app.app_context():
        finance, headers = _make_user(db, 'finance', FINANCE_PERMS, role_code='finance')

        client = app.test_client()
        res = client.get('/api/return-orders', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_finance_cannot_view_return_detail(app, db):
    """财务 GET /api/return-orders/<id> → 403。"""
    with app.app_context():
        finance, headers = _make_user(db, 'finance', FINANCE_PERMS, role_code='finance')
        ro = _make_return_order(db, 'R-Fin-V')

        client = app.test_client()
        res = client.get(f'/api/return-orders/{ro.id}', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_finance_cannot_create_return(app, db):
    """财务 POST /api/return-orders → 403。"""
    with app.app_context():
        finance, headers = _make_user(db, 'finance', FINANCE_PERMS, role_code='finance')

        client = app.test_client()
        res = client.post(
            '/api/return-orders',
            headers=headers,
            json={
                'return_type': 1,
                'related_order_id': 1,
                'related_order_no': 'PO-001',
                'supplier_id': 1,
                'supplier_name': '供应商',
                'refund_amount': 100,
                'items': [],
            },
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 3. 库管角色 — init_db.py 中库管只有 purchase:view，无 purchase-return:* 权限
# ============================================

def test_warehouse_cannot_list_returns(app, db):
    """库管 GET /api/return-orders → 403（库管权限中无 purchase-return:view）。"""
    with app.app_context():
        warehouse, headers = _make_user(db, 'wh', WAREHOUSE_PERMS, role_code='warehouse')

        client = app.test_client()
        res = client.get('/api/return-orders', headers=headers)
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_warehouse_cannot_create_return(app, db):
    """库管 POST /api/return-orders → 403（库管权限中无 purchase-return:add）。"""
    with app.app_context():
        warehouse, headers = _make_user(db, 'wh', WAREHOUSE_PERMS, role_code='warehouse')

        client = app.test_client()
        res = client.post(
            '/api/return-orders',
            headers=headers,
            json={
                'return_type': 1,
                'related_order_id': 1,
                'related_order_no': 'PO-001',
                'supplier_id': 1,
                'supplier_name': '供应商',
                'refund_amount': 100,
                'items': [],
            },
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 4. admin 不受限制（除了某些端点需业务校验存在单据）
# ============================================

def test_admin_can_list_returns(app, db):
    """admin GET /api/return-orders → 200。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')

        client = app.test_client()
        res = client.get('/api/return-orders', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_admin_can_view_return_detail(app, db):
    """admin GET /api/return-orders/<id> → 200。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        ro = _make_return_order(db, 'R-ADM-V')

        client = app.test_client()
        res = client.get(f'/api/return-orders/{ro.id}', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_admin_can_create_return(app, db):
    """admin POST /api/return-orders → 200（创建成功）。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')

        client = app.test_client()
        res = client.post(
            '/api/return-orders',
            headers=headers,
            json={
                'return_type': 1,
                'related_order_id': 1,
                'related_order_no': 'PO-001',
                'supplier_id': 1,
                'supplier_name': '供应商',
                'refund_amount': 100,
                'reason': 'admin 退货',
                'items': [],
            },
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        assert res.get_json().get('code') == 200


def test_admin_can_delete_return(app, db):
    """admin DELETE /api/return-orders/<id> → 200。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        ro = _make_return_order(db, 'R-ADM-D')

        client = app.test_client()
        res = client.delete(f'/api/return-orders/{ro.id}', headers=headers)
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        assert res.get_json().get('code') == 200