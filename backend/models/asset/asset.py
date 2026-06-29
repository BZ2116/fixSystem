from datetime import datetime

from extensions import db


class Asset(db.Model):
    """资产台账"""
    __tablename__ = 'asset'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    asset_no = db.Column(db.String(50), unique=True)  # 资产编号

    # 归属信息（客户优先维度）
    customer_id = db.Column(db.BigInteger, nullable=False)  # 归属客户ID
    customer_name = db.Column(db.String(100), nullable=False)  # 归属客户名称
    office_id = db.Column(db.BigInteger)  # 所属办公室ID
    office_name = db.Column(db.String(50))  # 所属办公室名称
    location = db.Column(db.String(100))  # 存放位置

    # 基础信息
    asset_type_id = db.Column(db.BigInteger, nullable=False)  # 资产类型ID
    asset_type_name = db.Column(db.String(50))  # 资产类型名称
    asset_name = db.Column(db.String(100), nullable=False)  # 资产名称
    device_no = db.Column(db.String(50))  # 设备编号
    sn_code = db.Column(db.String(100))  # SN序列号

    # 时间信息
    register_date = db.Column(db.Date)  # 登记日期
    purchase_date = db.Column(db.Date)  # 采购日期
    warranty_expire_date = db.Column(db.Date)  # 质保到期日

    # 状态信息
    warranty_status = db.Column(db.Integer, default=1)  # 0过保 1在保
    asset_status = db.Column(db.Integer, default=1)  # 1正常使用 2维修中 3闲置 4报废 5停用

    # 责任人信息
    responsible_person = db.Column(db.String(50))  # 使用责任人
    contact_phone = db.Column(db.String(20))  # 联系电话

    # 通用技术字段（所有类型都显示）
    ip_address = db.Column(db.String(50))  # IP地址
    login_password = db.Column(db.String(100))  # 设备登录密码
    remark = db.Column(db.Text)  # 备注信息

    # 专属字段（JSON存储）
    asset_data = db.Column(db.JSON)  # 设备类型专属字段

    # 关联信息
    sales_order_id = db.Column(db.BigInteger)  # 关联销售单ID
    sales_order_no = db.Column(db.String(50))  # 关联销售单号

    # 审计字段
    created_by = db.Column(db.BigInteger)
    created_by_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)