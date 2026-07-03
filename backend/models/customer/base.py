from datetime import datetime

from extensions import db
from models._base import BigIntPK


class BaseCustomer(db.Model):
    """客户信息"""
    __tablename__ = 'base_customer'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    customer_code = db.Column(db.String(50), unique=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_type = db.Column(db.Integer, default=1)  # 1:个人 2:企业
    pinyin_code = db.Column(db.String(100))
    contact_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    phone2 = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(255))
    discount_rate = db.Column(db.Numeric(5, 2), default=100.00)
    credit_limit = db.Column(db.Numeric(15, 2), default=0.00)
    tax_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    bank_account = db.Column(db.String(50))
    remark = db.Column(db.Text)
    total_sales_amount = db.Column(db.Numeric(15, 2), default=0.00)
    total_sales_count = db.Column(db.Integer, default=0)
    last_sales_date = db.Column(db.Date)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)