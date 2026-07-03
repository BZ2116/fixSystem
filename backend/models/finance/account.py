from datetime import datetime

from extensions import db
from .._base import BigIntPK


class FinanceAccount(db.Model):
    """财务账户"""
    __tablename__ = 'finance_account'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    account_name = db.Column(db.String(50), nullable=False)
    account_type = db.Column(db.Integer, default=1)  # 1现金 2银行 3支付宝 4微信
    account_no = db.Column(db.String(50))
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    status = db.Column(db.Integer, default=1)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class FinanceRecord(db.Model):
    """财务流水"""
    __tablename__ = 'finance_record'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    account_id = db.Column(BigIntPK)
    account_name = db.Column(db.String(50))
    record_type = db.Column(db.Integer, default=1)  # 1收入 2支出
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    balance_before = db.Column(db.Numeric(15, 2), default=0.00)
    balance_after = db.Column(db.Numeric(15, 2), default=0.00)
    related_type = db.Column(db.String(50))  # 关联类型: work_order, sale, purchase等
    related_id = db.Column(BigIntPK)
    related_no = db.Column(db.String(50))
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    created_by = db.Column(BigIntPK)


class FinanceReceivable(db.Model):
    """应收账款"""
    __tablename__ = 'finance_receivable'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    receivable_no = db.Column(db.String(50), unique=True)  # 应收编号
    related_type = db.Column(db.String(30))  # 关联类型：sale/return_sale
    related_id = db.Column(BigIntPK)  # 关联单据ID
    related_no = db.Column(db.String(50))  # 关联单据号
    customer_id = db.Column(BigIntPK)  # 客户ID
    customer_name = db.Column(db.String(100))  # 客户名称
    total_amount = db.Column(db.Numeric(15, 2), default=0)  # 应收总额
    received_amount = db.Column(db.Numeric(15, 2), default=0)  # 已收金额
    remaining_amount = db.Column(db.Numeric(15, 2), default=0)  # 待收金额
    status = db.Column(db.Integer, default=0)  # 状态：0待收款/1部分收款/2已结清/3已取消
    invoice_id = db.Column(BigIntPK)  # 关联发票ID
    due_date = db.Column(db.Date)  # 到期日
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class FinancePayable(db.Model):
    """应付账款"""
    __tablename__ = 'finance_payable'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    payable_no = db.Column(db.String(50), unique=True)  # 应付编号
    related_type = db.Column(db.String(30))  # 关联类型：purchase/return_purchase
    related_id = db.Column(BigIntPK)  # 关联单据ID
    related_no = db.Column(db.String(50))  # 关联单据号
    supplier_id = db.Column(BigIntPK)  # 供应商ID
    supplier_name = db.Column(db.String(100))  # 供应商名称
    total_amount = db.Column(db.Numeric(15, 2), default=0)  # 应付总额
    paid_amount = db.Column(db.Numeric(15, 2), default=0)  # 已付金额
    remaining_amount = db.Column(db.Numeric(15, 2), default=0)  # 待付金额
    status = db.Column(db.Integer, default=0)  # 状态：0待付款/1部分付款/2已结清/3已取消
    invoice_id = db.Column(BigIntPK)  # 关联发票ID
    due_date = db.Column(db.Date)  # 到期日
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class FinanceInvoice(db.Model):
    """发票管理"""
    __tablename__ = 'finance_invoice'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    invoice_no = db.Column(db.String(50), unique=True)
    invoice_type = db.Column(db.Integer, default=1)  # 1普通发票 2增值税发票
    customer_id = db.Column(BigIntPK)
    customer_name = db.Column(db.String(100))
    amount = db.Column(db.Numeric(15, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(15, 2), default=0.00)
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    status = db.Column(db.Integer, default=0)  # 0待开票 1已开票
    related_type = db.Column(db.String(50))
    related_id = db.Column(BigIntPK)
    related_no = db.Column(db.String(50))
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(BigIntPK)


class PurchaseInvoice(db.Model):
    """采购发票"""
    __tablename__ = 'purchase_invoice'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    invoice_no = db.Column(db.String(50), unique=True)  # 发票号码
    invoice_code = db.Column(db.String(50))  # 发票代码
    invoice_type = db.Column(db.Integer, default=1)  # 1普通发票 2增值税专用发票
    purchase_order_id = db.Column(BigIntPK)  # 关联采购单ID
    purchase_order_no = db.Column(db.String(50))  # 关联采购单号
    supplier_id = db.Column(BigIntPK)
    supplier_name = db.Column(db.String(100))
    amount = db.Column(db.Numeric(15, 2), default=0.00)  # 不含税金额
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00)  # 税率(%)
    tax_amount = db.Column(db.Numeric(15, 2), default=0.00)  # 税额
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)  # 价税合计
    invoice_date = db.Column(db.Date)  # 开票日期
    status = db.Column(db.Integer, default=0)  # 0待认证 1已认证 2已抵扣 3已作废
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(BigIntPK)


class Salary(db.Model):
    """工资发放"""
    __tablename__ = 'salary'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    salary_no = db.Column(db.String(50), unique=True)  # 工资单号
    user_id = db.Column(BigIntPK, nullable=False)  # 员工ID
    user_name = db.Column(db.String(50), nullable=False)  # 员工姓名
    department = db.Column(db.String(50))  # 部门
    position = db.Column(db.String(50))  # 岗位
    salary_month = db.Column(db.String(7), nullable=False)  # 工资月份，格式：2026-05
    base_salary = db.Column(db.Numeric(15, 2), default=0.00)  # 基本工资
    performance_salary = db.Column(db.Numeric(15, 2), default=0.00)  # 绩效工资
    commission = db.Column(db.Numeric(15, 2), default=0.00)  # 提成
    subsidy = db.Column(db.Numeric(15, 2), default=0.00)  # 补贴
    deduction = db.Column(db.Numeric(15, 2), default=0.00)  # 扣款
    should_pay = db.Column(db.Numeric(15, 2), default=0.00)  # 应发金额
    tax = db.Column(db.Numeric(15, 2), default=0.00)  # 个税
    actual_pay = db.Column(db.Numeric(15, 2), default=0.00)  # 实发金额
    account_id = db.Column(BigIntPK)  # 发放账户ID
    account_name = db.Column(db.String(50))  # 发放账户名称
    status = db.Column(db.Integer, default=0)  # 0待发放 1已发放 2已取消
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(BigIntPK)
    paid_at = db.Column(db.DateTime)  # 实际发放时间


class Expense(db.Model):
    """费用管理"""
    __tablename__ = 'expense'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    expense_no = db.Column(db.String(50), unique=True)  # 费用单号
    expense_name = db.Column(db.String(100), nullable=False)  # 费用名称
    expense_type = db.Column(db.Integer, default=1)  # 1日常费用 2其他收入 3运营支出 4管理费用
    amount = db.Column(db.Numeric(15, 2), default=0.00)  # 金额
    record_type = db.Column(db.Integer, default=2)  # 1收入 2支出
    account_id = db.Column(BigIntPK)  # 账户ID
    account_name = db.Column(db.String(50))  # 账户名称
    partner_type = db.Column(db.String(20))  # 往来类型：customer/supplier/other
    partner_id = db.Column(BigIntPK)  # 往来单位ID
    partner_name = db.Column(db.String(100))  # 往来单位名称
    expense_date = db.Column(db.Date)  # 费用日期
    status = db.Column(db.Integer, default=0)  # 0待处理 1已确认 2已取消
    attachment = db.Column(db.String(255))  # 附件路径
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)