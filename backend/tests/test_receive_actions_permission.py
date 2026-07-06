"""接件单状态机动作蓝图 (receive_actions) RBAC 测试。

约束（基于 scripts/init_db.py:213-267 实际权限矩阵）：
- 技师有 receive:edit → 可以 detect/quote/confirm/allocate/finish/test/notify/complete
  /external-send/external-quote/customer-quote/external-confirm/external-return
  /external-retest；但没有 receive:delete → cancel 应 403
- 库管只有 receive:view，没有 receive:edit/delete → 全部 403
- 财务只有 finance:view，没有 receive:edit/delete → 全部 403
- admin 通配符 '*' → 全通

实现位置：app/blueprints/receive_actions.py 各端点的 @permission() 装饰器。
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

# 与 init_db.py:231-248 一致
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

# 与 init_db.py:249-266 一致
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
    from models.receive import ReceiveOrder, ReceiveOrderDevice, ReceiveOrderLog  # noqa
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


def _make_receive_order(db, receive_no: str = 'RO-001', status: int = 0):
    from models.receive import ReceiveOrder
    order = ReceiveOrder(
        receive_no=receive_no,
        customer_name='客户',
        customer_phone='13800000000',
        status=status,
        created_by=1,
    )
    db.session.add(order)
    db.session.commit()
    return order


# ============================================
# 1. 技师有 receive:edit：detect / quote / finish 端点 200（状态合法时）
# ============================================

def test_tech_can_detect(app, db):
    """技师 POST /api/receiveorders/<id>/detect → 200（status=0 时）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        ro = _make_receive_order(db, 'RO-Tech-Det', status=0)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/detect',
            headers=headers,
            json={
                'can_repair': True,
                'detect_result': '可维修',
                'detect_fault_reason': '主板故障',
                'detect_repair_plan': '更换主板',
            },
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_tech_can_finish(app, db):
    """技师 POST /api/receiveorders/<id>/finish → 200（status=5 时）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        ro = _make_receive_order(db, 'RO-Tech-Fin', status=5)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/finish',
            headers=headers,
            json={'finish_report': '已修复'},
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


def test_tech_can_notify(app, db):
    """技师 POST /api/receiveorders/<id>/notify → 200（status=7 时）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        ro = _make_receive_order(db, 'RO-Tech-Not', status=7)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/notify',
            headers=headers,
            json={'notify_method': '电话'},
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 2. 技师没有 receive:delete：cancel 应 403
# ============================================

def test_tech_cannot_cancel(app, db):
    """技师 POST /api/receiveorders/<id>/cancel → 403（无 receive:delete）。"""
    with app.app_context():
        tech, headers = _make_user(db, 'tech', TECH_PERMS)
        ro = _make_receive_order(db, 'RO-Tech-Can', status=0)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/cancel',
            headers=headers,
            json={'cancel_reason': '技师取消'},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 3. 库管不能检测 / 取消（无 receive:edit / receive:delete）
# ============================================

def test_warehouse_cannot_detect(app, db):
    """库管 POST /api/receiveorders/<id>/detect → 403。"""
    with app.app_context():
        warehouse, headers = _make_user(db, 'wh', WAREHOUSE_PERMS, role_code='warehouse')
        ro = _make_receive_order(db, 'RO-WH-Det', status=0)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/detect',
            headers=headers,
            json={'can_repair': True},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_warehouse_cannot_cancel(app, db):
    """库管 POST /api/receiveorders/<id>/cancel → 403。"""
    with app.app_context():
        warehouse, headers = _make_user(db, 'wh', WAREHOUSE_PERMS, role_code='warehouse')
        ro = _make_receive_order(db, 'RO-WH-Can', status=0)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/cancel',
            headers=headers,
            json={'cancel_reason': '库管取消'},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_warehouse_cannot_quote(app, db):
    """库管 POST /api/receiveorders/<id>/quote → 403。"""
    with app.app_context():
        warehouse, headers = _make_user(db, 'wh', WAREHOUSE_PERMS, role_code='warehouse')
        ro = _make_receive_order(db, 'RO-WH-Q', status=2)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/quote',
            headers=headers,
            json={'items': []},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 4. 财务也不能 detect / cancel
# ============================================

def test_finance_cannot_detect(app, db):
    """财务 POST /api/receiveorders/<id>/detect → 403（无 receive:edit）。"""
    with app.app_context():
        finance, headers = _make_user(db, 'finance', FINANCE_PERMS, role_code='finance')
        ro = _make_receive_order(db, 'RO-Fin-Det', status=0)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/detect',
            headers=headers,
            json={'can_repair': True},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


def test_finance_cannot_cancel(app, db):
    """财务 POST /api/receiveorders/<id>/cancel → 403。"""
    with app.app_context():
        finance, headers = _make_user(db, 'finance', FINANCE_PERMS, role_code='finance')
        ro = _make_receive_order(db, 'RO-Fin-Can', status=0)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/cancel',
            headers=headers,
            json={'cancel_reason': '财务取消'},
        )
        assert res.status_code == 403, f'期望 403, 实际 {res.status_code}: {res.get_json()}'


# ============================================
# 5. admin 不受权限拦截（业务校验 200 或 400，但绝非 403）
# ============================================

def test_admin_can_detect(app, db):
    """admin POST /api/receiveorders/<id>/detect → 200（业务校验通过）。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        ro = _make_receive_order(db, 'RO-ADM-Det', status=0)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/detect',
            headers=headers,
            json={'can_repair': True},
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'
        assert res.status_code != 403


def test_admin_can_cancel(app, db):
    """admin POST /api/receiveorders/<id>/cancel → 200 或 400（业务校验），不是 403。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        ro = _make_receive_order(db, 'RO-ADM-Can', status=0)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/cancel',
            headers=headers,
            json={'cancel_reason': 'admin 取消'},
        )
        assert res.status_code in (200, 400), (
            f'期望 200 或 400 (业务校验), 实际 {res.status_code}: {res.get_json()}'
        )
        assert res.status_code != 403, 'admin 不应被权限拦截'


def test_admin_not_blocked_by_permission_on_quote(app, db):
    """admin POST /api/receiveorders/<id>/quote → 200 或 400（业务校验），不是 403。"""
    with app.app_context():
        admin, headers = _make_user(db, 'admin', ['*'], role_code='admin')
        ro = _make_receive_order(db, 'RO-ADM-Q', status=2)

        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{ro.id}/quote',
            headers=headers,
            json={'items': []},
        )
        # 业务校验失败 400 即可（items 空）；绝不能 403
        assert res.status_code in (200, 400), (
            f'期望 200/400, 实际 {res.status_code}: {res.get_json()}'
        )
        assert res.status_code != 403