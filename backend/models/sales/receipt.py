"""销售收据模型。

迁移自 source-code/app.py 5712-5734 行附近的 SalesReceipt 类。
字段与原 app.py 完全一致，便于上层蓝图使用。
"""
from datetime import datetime

from extensions import db
from .._base import BigIntPK


class SalesReceipt(db.Model):
    """销售收据"""
    __tablename__ = 'sales_receipt'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    order_id = db.Column(BigIntPK, nullable=False)  # 关联销售单ID
    order_no = db.Column(db.String(50))  # 关联销售单号
    receipt_no = db.Column(db.String(50))  # 收据编号（自动生成）
    receipt_date = db.Column(db.Date)  # 收款日期
    # 客户信息
    customer_name = db.Column(db.String(100))  # 客户名称
    customer_phone = db.Column(db.String(20))  # 联系方式
    # 金额信息
    total_amount = db.Column(db.Numeric(15, 2), default=0)  # 应收金额
    paid_amount = db.Column(db.Numeric(15, 2), default=0)  # 实收金额
    payment_method = db.Column(db.String(20))  # 收款方式
    # 商品明细（JSON格式）
    items = db.Column(db.Text)  # 收据商品明细JSON
    remark = db.Column(db.Text)  # 备注/收款说明
    payee = db.Column(db.String(50))  # 收款人
    status = db.Column(db.Integer, default=1)  # 状态：1有效 0作废
    created_by = db.Column(BigIntPK)  # 开具人ID
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
