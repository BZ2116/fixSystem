from datetime import datetime

from extensions import db
from .._base import BigIntPK


class ReceiveOrder(db.Model):
    """接件单"""
    __tablename__ = 'receive_order'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    receive_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(BigIntPK)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    receive_type = db.Column(db.Integer, default=1)  # 1本店修 2外送修
    external_shop_id = db.Column(BigIntPK)  # 外送供应商ID
    external_shop_name = db.Column(db.String(100))  # 外送供应商名称
    status = db.Column(db.Integer, default=0)  # 状态见 RO_STATUS_MAP
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    paid_amount = db.Column(db.Numeric(15, 2), default=0.00)
    remark = db.Column(db.Text)
    # 接待/维修员工
    receiver_id = db.Column(BigIntPK)  # 接待员工ID
    receiver_name = db.Column(db.String(50))  # 接待员工姓名
    engineer_id = db.Column(BigIntPK)  # 维修工程师ID
    engineer_name = db.Column(db.String(50))  # 维修工程师姓名
    # 检测信息
    detect_result = db.Column(db.Text)  # 检测结果
    detect_fault_reason = db.Column(db.Text)  # 故障原因
    detect_repair_plan = db.Column(db.Text)  # 维修方案
    detect_parts = db.Column(db.Text)  # 预估配件(JSON)
    # 报价信息
    quote_labor_cost = db.Column(db.Numeric(10, 2), default=0.00)  # 报价人工费
    quote_material_cost = db.Column(db.Numeric(10, 2), default=0.00)  # 报价材料费
    quote_other_cost = db.Column(db.Numeric(10, 2), default=0.00)  # 报价其他费用
    quote_total = db.Column(db.Numeric(10, 2), default=0.00)  # 报价总计
    quote_confirmed = db.Column(db.Integer, default=0)  # 客户确认(0待确认/1已确认/2已拒绝)
    quote_confirm_time = db.Column(db.DateTime)  # 确认时间
    # 外店维修信息
    external_quote = db.Column(db.Numeric(10, 2), default=0.00)  # 外店报价
    external_repair_reason = db.Column(db.Text)  # 送修原因
    external_send_date = db.Column(db.Date)  # 送修日期
    external_return_date = db.Column(db.Date)  # 取回日期
    external_round = db.Column(db.Integer, default=1)  # 外店往返次数
    external_history = db.Column(db.Text)  # 外店往返记录(JSON)
    # 完工/测试信息
    finish_report = db.Column(db.Text)  # 完工报告
    finish_photos = db.Column(db.Text)  # 测试照片(JSON)
    test_result = db.Column(db.Integer, default=0)  # 测试结果(0待测试/1通过/2未通过)
    test_remark = db.Column(db.Text)  # 测试备注
    # 通知/完成信息
    notify_time = db.Column(db.DateTime)  # 通知取件时间
    notify_method = db.Column(db.String(20))  # 通知方式
    complete_time = db.Column(db.DateTime)  # 完成时间
    finance_record_id = db.Column(BigIntPK)  # 关联财务记录ID
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(BigIntPK)


class ReceiveOrderDevice(db.Model):
    """接件单设备明细"""
    __tablename__ = 'receive_order_device'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    receive_order_id = db.Column(BigIntPK, nullable=False)
    device_archive_id = db.Column(BigIntPK)
    device_type = db.Column(db.String(50))
    device_brand = db.Column(db.String(50))
    device_model = db.Column(db.String(100))
    device_sn = db.Column(db.String(100))
    device_imei = db.Column(db.String(50))
    fault_desc = db.Column(db.Text)
    appearance_desc = db.Column(db.Text)
    accessories = db.Column(db.Text)
    work_order_id = db.Column(BigIntPK)  # 关联工单ID
    status = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    # 设备详细信息
    device_name = db.Column(db.String(200))  # 设备名称
    cpu = db.Column(db.String(100))  # CPU
    memory = db.Column(db.String(100))  # 内存
    disk = db.Column(db.String(100))  # 硬盘
    os = db.Column(db.String(100))  # 操作系统
    os_version = db.Column(db.String(100))  # 系统版本
    toner_model = db.Column(db.String(100))  # 硒鼓型号(打印机)
    drum_model = db.Column(db.String(100))  # 粉盒型号(打印机)
    ip_address = db.Column(db.String(50))  # IP地址
    port = db.Column(db.Integer)  # 端口
    camera_count = db.Column(db.Integer)  # 摄像头数量(监控设备)
    monitor_brand = db.Column(db.String(100))  # 监控品牌
    firmware_version = db.Column(db.String(100))  # 固件版本(网络设备)
    port_count = db.Column(db.Integer)  # 端口数(网络设备)
    label_printed = db.Column(db.Integer, default=0)  # 标签是否已打印(0否/1是)


class ReceiveOrderPart(db.Model):
    """接件单维修配件/领料明细"""
    __tablename__ = 'receive_order_part'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    receive_order_id = db.Column(BigIntPK, nullable=False)  # 关联接件单ID
    product_id = db.Column(BigIntPK)  # 商品ID
    product_name = db.Column(db.String(200))  # 商品名称
    product_code = db.Column(db.String(50))  # 商品编码
    specification = db.Column(db.String(100))  # 规格
    unit_name = db.Column(db.String(20))  # 单位
    quantity = db.Column(db.Numeric(10, 2), default=0)  # 数量
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)  # 单价
    total_price = db.Column(db.Numeric(10, 2), default=0.00)  # 总价
    cost_price = db.Column(db.Numeric(10, 2), default=0.00)  # 成本价
    source = db.Column(db.Integer, default=1)  # 来源(1库存/2采购)
    inventory_out_item_id = db.Column(BigIntPK)  # 关联出库明细ID
    purchase_order_item_id = db.Column(BigIntPK)  # 关联采购明细ID
    status = db.Column(db.Integer, default=0)  # 状态(0待领/1已领/2已采购)
    remark = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.now)


class DeviceArchive(db.Model):
    """设备档案"""
    __tablename__ = 'device_archive'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    device_code = db.Column(db.String(50), unique=True)
    customer_id = db.Column(BigIntPK)
    device_type = db.Column(db.String(50))
    device_name = db.Column(db.String(200))
    device_brand = db.Column(db.String(50))
    device_model = db.Column(db.String(100))
    device_sn = db.Column(db.String(100))
    device_imei = db.Column(db.String(50))
    device_password = db.Column(db.String(200))
    ip_address = db.Column(db.String(50))
    port = db.Column(db.Integer)
    quantity = db.Column(db.Integer, default=1)
    cpu = db.Column(db.String(100))
    memory = db.Column(db.String(100))
    disk = db.Column(db.String(100))
    os = db.Column(db.String(100))
    os_version = db.Column(db.String(100))
    accessories = db.Column(db.String(500))
    account = db.Column(db.String(200))
    password = db.Column(db.String(200))
    password_remark = db.Column(db.String(500))
    # 打印机耗材字段
    consumable_model = db.Column(db.String(200))  # 耗材型号
    toner_model = db.Column(db.String(100))       # 硒鼓型号
    drum_model = db.Column(db.String(100))        # 粉盒型号
    purchase_date = db.Column(db.Date)
    warranty_expire = db.Column(db.Date)
    remark = db.Column(db.Text)
    repair_count = db.Column(db.Integer, default=0)
    last_repair_date = db.Column(db.Date)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ReceiveOrderLog(db.Model):
    """接件单操作日志。"""
    __tablename__ = 'receive_order_log'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    receive_order_id = db.Column(BigIntPK, nullable=False, index=True)
    action = db.Column(db.String(50))
    old_status = db.Column(db.Integer)
    new_status = db.Column(db.Integer)
    content = db.Column(db.Text)
    operator_id = db.Column(BigIntPK)
    operator_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)