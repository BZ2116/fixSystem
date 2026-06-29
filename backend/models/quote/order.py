from datetime import datetime

from extensions import db


class QuoteOrder(db.Model):
    """报价单"""
    __tablename__ = 'quote_order'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    quote_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.BigInteger)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    contact_name = db.Column(db.String(50))
    address = db.Column(db.String(255))
    quote_date = db.Column(db.Date, default=datetime.now().date)
    valid_until = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    remark = db.Column(db.Text)
    status = db.Column(db.Integer, default=0)  # 0待确认 1已确认 2已失效 3已转工单 4已转接件 5已转销售
    related_type = db.Column(db.String(50))
    related_id = db.Column(db.BigInteger)
    created_by = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class QuoteOrderItem(db.Model):
    """报价单明细"""
    __tablename__ = 'quote_order_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    quote_id = db.Column(db.BigInteger, nullable=False)
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(100))
    brand = db.Column(db.String(50))
    unit = db.Column(db.String(20))
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit_price = db.Column(db.Numeric(15, 2), default=0.00)
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
