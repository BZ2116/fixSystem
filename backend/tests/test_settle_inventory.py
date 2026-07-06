"""settle 库存修复测试。

约束：
- 工单领料后 InventoryStock.frozen_quantity 应增加
- settle 后 frozen_quantity 应减少（释放未用部分）
- settle 不应改变 Product.stock（避免双重入账）
- used_qty 超过 part.quantity 时应截断到 part.quantity（不抛错）

实现：app/services/workorder_service.py 中 settle_workorder 的库存释放逻辑
"""
import pytest


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
    from models.inventory import InventoryOut, InventoryOutItem, InventoryStock  # noqa
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


def _make_product_with_stock(db, qty: float = 10.0, frozen: float = 0.0):
    """造一个 Product + InventoryStock，返回 (product, stock)."""
    from models.product import ProductInfo
    from models.inventory import InventoryStock

    product = ProductInfo(
        product_code=f'P-{qty}',
        product_name='测试商品',
        sale_price=100,
        cost_price=50,
        current_stock=int(qty),
    )
    db.session.add(product)
    db.session.commit()

    stock = InventoryStock(
        product_id=product.id,
        warehouse_id=1,
        quantity=qty,
        frozen_quantity=frozen,
        available_quantity=qty - frozen,
    )
    db.session.add(stock)
    db.session.commit()
    return product, stock


def _make_user(db):
    from models.system import SysUser
    from werkzeug.security import generate_password_hash
    user = SysUser(
        username='tester', password=generate_password_hash('x'), real_name='tester',
    )
    db.session.add(user)
    db.session.commit()
    return user


# ============================================
# 1. 领料后 frozen_quantity 应增加
# ============================================

def test_allocate_increases_frozen_quantity(app, db):
    """工单领料后 InventoryStock.frozen_quantity 增加。"""
    with app.app_context():
        from models.workorder import WorkOrder
        from app.services.workorder_service import allocate_parts

        product, stock = _make_product_with_stock(db, qty=10.0, frozen=0.0)
        user = _make_user(db)
        wo = WorkOrder(wo_no='WO-A', status=2, customer_name='c', assigned_user_id=user.id)
        db.session.add(wo)
        db.session.commit()

        allocate_parts(
            wo,
            [{'product_id': product.id, 'quantity': 3}],
            user.id, 'tester',
        )
        db.session.commit()

        # 重新查询 stock
        from models.inventory import InventoryStock
        stock_after = InventoryStock.query.filter_by(product_id=product.id).first()
        assert stock_after.frozen_quantity == 3, (
            f'期望 frozen=3, 实际 {stock_after.frozen_quantity}'
        )


# ============================================
# 2. settle 后 frozen_quantity 应减少，Product.stock 不变
# ============================================

def test_settle_releases_frozen_for_unused_parts(app, db):
    """settle 未用配件应释放 frozen_quantity，Product.stock 不变。"""
    with app.app_context():
        from models.workorder import WorkOrder, WorkOrderPart
        from models.inventory import InventoryStock
        from app.services.workorder_service import allocate_parts, settle_workorder

        product, stock = _make_product_with_stock(db, qty=10.0, frozen=0.0)
        user = _make_user(db)
        wo = WorkOrder(wo_no='WO-S1', status=2, customer_name='c', assigned_user_id=user.id)
        db.session.add(wo)
        db.session.commit()

        # 领料 3 个
        allocate_parts(wo, [{'product_id': product.id, 'quantity': 3}], user.id, 'tester')
        db.session.commit()

        # 移到待结算状态
        wo.status = 4
        db.session.commit()

        # 取出 WorkOrderPart
        part = WorkOrderPart.query.filter_by(wo_id=wo.id).first()
        assert part is not None
        assert part.quantity == 3

        # 结算：用 1 个（剩 2 个未用）
        settle_workorder(
            wo,
            {f'used_qty_{part.id}': 1, 'settle_type': 'cash'},
            user.id, 'tester',
        )
        db.session.commit()

        # 重新查询
        stock_after = InventoryStock.query.filter_by(product_id=product.id).first()
        product_after = product

        # frozen_quantity: 3 - 2 (unused) = 1
        assert float(stock_after.frozen_quantity or 0) == 1, (
            f'期望 frozen=1, 实际 {stock_after.frozen_quantity}'
        )
        # Product.current_stock 不变（防止双重入账）
        assert int(product_after.current_stock or 0) == 10, (
            f'期望 Product.current_stock=10, 实际 {product_after.current_stock}'
        )


# ============================================
# 3. used_qty 超过 part.quantity 时应截断
# ============================================

def test_settle_caps_used_qty_to_part_quantity(app, db):
    """used_qty 超过 part.quantity 时截断到 part.quantity，不抛错。"""
    with app.app_context():
        from models.workorder import WorkOrder, WorkOrderPart
        from app.services.workorder_service import allocate_parts, settle_workorder

        product, _ = _make_product_with_stock(db, qty=10.0, frozen=0.0)
        user = _make_user(db)
        wo = WorkOrder(wo_no='WO-S2', status=2, customer_name='c', assigned_user_id=user.id)
        db.session.add(wo)
        db.session.commit()

        # 领料 3 个
        allocate_parts(wo, [{'product_id': product.id, 'quantity': 3}], user.id, 'tester')
        db.session.commit()
        wo.status = 4
        db.session.commit()

        part = WorkOrderPart.query.filter_by(wo_id=wo.id).first()
        # 故意让 used_qty=10（超过 part.quantity=3）
        # 不应抛 ValueError
        settle_workorder(
            wo,
            {f'used_qty_{part.id}': 10, 'settle_type': 'cash'},
            user.id, 'tester',
        )
        db.session.commit()

        # used_quantity 应被截断到 3
        assert float(part.used_quantity or 0) == 3, (
            f'期望 used_quantity=3 (被截断), 实际 {part.used_quantity}'
        )
