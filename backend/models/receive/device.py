from datetime import datetime

from extensions import db
from .._base import BigIntPK


class DeviceReceiveOrder(db.Model):
    """设备接收单"""
    __tablename__ = 'device_receive_order'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    receive_no = db.Column(db.String(50), unique=True, nullable=False)  # 接收单号
    wo_id = db.Column(BigIntPK)  # 关联工单ID
    customer_id = db.Column(BigIntPK)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))

    # 设备信息
    device_type = db.Column(db.String(50))  # 设备类型
    device_brand = db.Column(db.String(50))  # 品牌
    device_model = db.Column(db.String(100))  # 型号
    device_sn = db.Column(db.String(100))  # 序列号
    device_imei = db.Column(db.String(50))  # IMEI

    # 接收信息
    appearance_desc = db.Column(db.Text)  # 外观描述
    accessories = db.Column(db.Text)  # 配件清单（JSON格式）
    device_password = db.Column(db.String(100))  # 设备密码
    fault_desc = db.Column(db.Text)  # 故障描述
    remark = db.Column(db.Text)  # 备注

    # 确认信息
    receiver_id = db.Column(BigIntPK)  # 接收人ID
    receiver_name = db.Column(db.String(50))  # 接收人姓名
    receive_time = db.Column(db.DateTime, default=datetime.now)  # 接收时间

    customer_sign = db.Column(db.String(255))  # 客户签字图片
    sign_time = db.Column(db.DateTime)  # 签字时间

    status = db.Column(db.Integer, default=0)  # 状态: 0待确认 1已确认 2已取走
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class DeviceAccessory(db.Model):
    """配件明细表"""
    __tablename__ = 'device_accessory'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    receive_order_id = db.Column(BigIntPK, nullable=False)  # 关联接件单ID
    accessory_name = db.Column(db.String(100), nullable=False)  # 配件名称
    quantity = db.Column(db.Integer, default=1)  # 数量
    status = db.Column(db.String(20), default='完好')  # 状态: 完好/损坏/缺失
    remark = db.Column(db.String(255))  # 备注
    created_at = db.Column(db.DateTime, default=datetime.now)


class DevicePhoto(db.Model):
    """接件照片表"""
    __tablename__ = 'device_photo'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    receive_order_id = db.Column(BigIntPK, nullable=False)  # 关联接件单ID
    photo_type = db.Column(db.String(20), default='整体照')  # 照片类型: 整体照/外观照/屏幕照/标签特写
    photo_url = db.Column(db.String(500), nullable=False)  # 照片URL
    remark = db.Column(db.String(255))  # 备注
    created_at = db.Column(db.DateTime, default=datetime.now)