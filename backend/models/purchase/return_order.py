from datetime import datetime

from extensions import db


class ReturnOrder(db.Model):
    """退货单"""
    __tablename__ = 'return_order'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    return_no = db.Column(db.String(50), unique=True, nullable=False)
    return_type = db.Column(db.Integer, default=1)  # 1采购退货 2销售退货
    related_order_id = db.Column(db.BigInteger)  # 关联单据ID
    related_order_no = db.Column(db.String(50))  # 关联单号
    supplier_id = db.Column(db.BigInteger)  # 供应商ID（采购退货）
    supplier_name = db.Column(db.String(100))
    customer_id = db.Column(db.BigInteger)  # 客户ID（销售退货）
    customer_name = db.Column(db.String(100))
    total_quantity = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    refund_amount = db.Column(db.Numeric(15, 2), default=0)  # 退款金额
    status = db.Column(db.Integer, default=0)  # 0待审核 1已审核 2已入库 3已取消
    reason = db.Column(db.Text)  # 退货原因
    remark = db.Column(db.Text)
    created_by = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ReturnOrderItem(db.Model):
    """退货单明细"""
    __tablename__ = 'return_order_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    return_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    quantity = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Numeric(15, 4), default=0)
    total_price = db.Column(db.Numeric(15, 2), default=0)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)