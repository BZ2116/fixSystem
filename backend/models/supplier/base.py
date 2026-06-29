from datetime import datetime

from extensions import db


class BaseSupplier(db.Model):
    """供应商信息"""
    __tablename__ = 'base_supplier'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    supplier_code = db.Column(db.String(50), unique=True)
    supplier_name = db.Column(db.String(100), nullable=False)
    pinyin_code = db.Column(db.String(100))
    contact_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(255))
    tax_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    bank_account = db.Column(db.String(50))
    is_repair_partner = db.Column(db.Integer, default=0)  # 是否维修合作方
    repair_types = db.Column(db.JSON)  # 可维修类型
    remark = db.Column(db.Text)
    total_purchase_amount = db.Column(db.Numeric(15, 2), default=0.00)
    total_purchase_count = db.Column(db.Integer, default=0)
    total_repair_amount = db.Column(db.Numeric(15, 2), default=0.00)
    total_repair_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)