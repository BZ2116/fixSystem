"""销售发票模型。

迁移自 source-code/app.py 5681-5710 行附近的 SalesInvoice 类。
字段与原 app.py 完全一致，便于上层蓝图使用。
"""
from datetime import datetime

from extensions import db


class SalesInvoice(db.Model):
    """销售发票"""
    __tablename__ = 'sales_invoice'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, nullable=False)  # 关联销售单ID
    order_no = db.Column(db.String(50))  # 关联销售单号
    invoice_type = db.Column(db.String(30))  # 发票类型：普通发票/增值税专用发票/电子发票
    invoice_status = db.Column(db.String(20), default='未开票')  # 开票状态：未开票/已开票/作废
    invoice_no = db.Column(db.String(50))  # 发票编号
    invoice_date = db.Column(db.Date)  # 开票日期
    # 客户开票信息
    buyer_name = db.Column(db.String(200))  # 客户开票抬头（公司名称/个人）
    buyer_tax_no = db.Column(db.String(50))  # 统一社会信用代码/税号
    buyer_address = db.Column(db.String(255))  # 开票地址
    buyer_phone = db.Column(db.String(50))  # 联系电话
    buyer_bank = db.Column(db.String(100))  # 开户行
    buyer_bank_account = db.Column(db.String(50))  # 银行账号
    # 开票项目明细（JSON格式存储）
    items = db.Column(db.Text)  # 发票明细JSON：[{name,spec,qty,price,amount,tax_rate,tax,total}]
    total_amount = db.Column(db.Numeric(15, 2), default=0)  # 金额合计（不含税）
    total_tax = db.Column(db.Numeric(15, 2), default=0)  # 税额合计
    total_with_tax = db.Column(db.Numeric(15, 2), default=0)  # 价税合计
    tax_rate = db.Column(db.Numeric(5, 2), default=0)  # 默认税率%
    remark = db.Column(db.Text)  # 开票备注
    attachment = db.Column(db.String(500))  # 发票附件路径
    created_by = db.Column(db.BigInteger)  # 开票人ID
    created_by_name = db.Column(db.String(50))  # 开票人姓名
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
