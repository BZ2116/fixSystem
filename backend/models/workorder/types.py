from datetime import datetime

from extensions import db


class WoType(db.Model):
    """工单类型"""
    __tablename__ = 'wo_type'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    type_name = db.Column(db.String(50), nullable=False)
    type_code = db.Column(db.String(50), unique=True, nullable=False)
    default_labor_cost = db.Column(db.Numeric(15, 2), default=0.00)
    estimated_days = db.Column(db.Integer, default=1)
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)


class WoSubType(db.Model):
    """工单二级分类"""
    __tablename__ = 'wo_sub_type'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    parent_type = db.Column(db.String(50), nullable=False)  # 父类型code: repair/maintenance/inspection/installation
    sub_type_code = db.Column(db.String(50), unique=True, nullable=False)  # 二级分类code
    sub_type_name = db.Column(db.String(50), nullable=False)  # 二级分类名称
    device_category = db.Column(db.String(50))  # 设备类别: monitor/network/printer/computer/other
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)


class WoDynamicField(db.Model):
    """工单动态字段"""
    __tablename__ = 'wo_dynamic_field'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    wo_id = db.Column(db.BigInteger, nullable=False, index=True)  # 工单ID
    field_key = db.Column(db.String(100), nullable=False)  # 字段标识: ip_address/manage_account/manage_password/login_account/login_password
    field_value = db.Column(db.Text)  # 字段值
    field_label = db.Column(db.String(100))  # 字段显示名
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Project(db.Model):
    """维修项目"""
    __tablename__ = 'project'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    project_name = db.Column(db.String(100), nullable=False)
    project_code = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(50))  # 维修类别
    default_price = db.Column(db.Numeric(15, 2), default=0.00)
    estimated_hours = db.Column(db.Numeric(5, 1), default=1.0)
    remark = db.Column(db.Text)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)