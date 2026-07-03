from datetime import datetime

from extensions import db
from .._base import BigIntPK


class PrintTemplate(db.Model):
    """打印模板"""
    __tablename__ = 'print_template'
    __table_args__ = {'extend_existing': True}
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    template_name = db.Column(db.String(100), nullable=False)
    template_type = db.Column(db.String(50))  # work_order, receive, dispatch, quote, sale, purchase, return_purchase, return_sale, inventory_in, inventory_out, inventory_check, transfer, receivable, payable, receipt, payment, salary
    description = db.Column(db.String(200))
    header_content = db.Column(db.Text)  # 页眉HTML
    body_content = db.Column(db.Text)    # 主体HTML模板（支持变量占位符）
    footer_content = db.Column(db.Text)  # 页脚HTML
    style_content = db.Column(db.Text)   # CSS样式
    paper_size = db.Column(db.String(20), default='A4')
    paper_width = db.Column(db.Integer, default=210)   # 纸张宽度mm
    paper_height = db.Column(db.Integer, default=297)  # 纸张高度mm
    is_default = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)