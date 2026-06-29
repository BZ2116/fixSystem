from datetime import datetime

from extensions import db


class Warehouse(db.Model):
    """仓库"""
    __tablename__ = 'warehouse'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    warehouse_code = db.Column(db.String(30), unique=True)  # 仓库编码
    warehouse_name = db.Column(db.String(50), nullable=False)  # 仓库名称
    address = db.Column(db.String(255))  # 仓库地址
    contact_person = db.Column(db.String(50))  # 联系人
    contact_phone = db.Column(db.String(20))  # 联系电话
    remark = db.Column(db.Text)  # 备注
    status = db.Column(db.Integer, default=1)  # 启用状态：1启用 0禁用
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Shelf(db.Model):
    """货架"""
    __tablename__ = 'shelf'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    shelf_name = db.Column(db.String(100), nullable=False)
    shelf_code = db.Column(db.String(50), unique=True)
    warehouse_id = db.Column(db.BigInteger, nullable=False)
    warehouse_name = db.Column(db.String(100))
    location = db.Column(db.String(200))  # 货架位置描述
    sort_order = db.Column(db.Integer, default=0)  # 排序
    remark = db.Column(db.Text)
    status = db.Column(db.Integer, default=1)  # 1启用 0停用
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)