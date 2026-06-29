"""采购单模型。

迁移自 source-code/app.py 5598-5631 行附近的 PurchaseOrder / PurchaseOrderItem 类。
字段与原 app.py 完全一致，便于上层蓝图使用。
"""
from datetime import datetime

from extensions import db


class PurchaseOrder(db.Model):
    """采购单"""
    __tablename__ = 'purchase_order'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.BigInteger)
    supplier_name = db.Column(db.String(100))
    order_date = db.Column(db.Date)
    delivery_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    total_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=0)  # 0待审核 1已审核 2已完成 3已取消
    has_invoice = db.Column(db.Integer, default=0)  # 0未收发票 1已收发票
    remark = db.Column(db.Text)
    created_by = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class PurchaseOrderItem(db.Model):
    """采购单明细"""
    __tablename__ = 'purchase_order_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(100))
    unit = db.Column(db.String(20))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Numeric(15, 4), default=0)
    amount = db.Column(db.Numeric(15, 2), default=0)
    received_qty = db.Column(db.Integer, default=0)
    remark = db.Column(db.Text)