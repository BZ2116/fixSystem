"""销售单模型。

迁移自 source-code/app.py 5635-5680 行附近的 SalesOrder / SalesOrderItem 类。
字段与原 app.py 完全一致，便于上层蓝图使用。
"""
from datetime import datetime

from extensions import db


class SalesOrder(db.Model):
    """销售单"""
    __tablename__ = 'sales_order'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.BigInteger)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))  # 客户电话
    customer_address = db.Column(db.String(255))  # 客户地址
    contact_name = db.Column(db.String(50))  # 联系人
    order_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    total_quantity = db.Column(db.Integer, default=0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0)  # 折扣金额
    freight_amount = db.Column(db.Numeric(15, 2), default=0)  # 运费
    actual_amount = db.Column(db.Numeric(15, 2), default=0)  # 实际应收金额
    paid_amount = db.Column(db.Numeric(15, 2), default=0)  # 已收金额
    payment_method = db.Column(db.String(20))  # 付款方式：现金/转账/支付宝/微信/赊账
    delivery_method = db.Column(db.String(20))  # 交货方式：自提/送货/快递
    salesperson_id = db.Column(db.BigInteger)  # 销售人员ID
    salesperson_name = db.Column(db.String(50))  # 销售人员姓名
    status = db.Column(db.Integer, default=0)  # 0待审核 1已审核 2已出库 3已完成 4已取消
    remark = db.Column(db.Text)
    created_by = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    has_invoice = db.Column(db.Integer, default=0)  # 是否开具发票：0否 1是
    has_receipt = db.Column(db.Integer, default=0)  # 是否开具收据：0否 1是


class SalesOrderItem(db.Model):
    """销售单明细"""
    __tablename__ = 'sales_order_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(100))
    unit = db.Column(db.String(20))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Numeric(15, 4), default=0)
    amount = db.Column(db.Numeric(15, 2), default=0)
    delivered_qty = db.Column(db.Integer, default=0)
    remark = db.Column(db.Text)
