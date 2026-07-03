from datetime import datetime

from extensions import db
from .._base import BigIntPK


class WorkOrder(db.Model):
    """维修工单"""
    __tablename__ = 'work_order'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    wo_no = db.Column(db.String(50), unique=True, nullable=False)  # 工单号
    wo_type = db.Column(db.String(50))  # 工单类型: network/device/delivery/monitor/purchase/survey/install
    wo_sub_type = db.Column(db.String(50))  # 二级分类code
    customer_id = db.Column(BigIntPK)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    customer_address = db.Column(db.String(255))  # 客户地址

    # 设备相关字段（设备维修维护、设备安装）
    device_type = db.Column(db.String(50))  # 设备类型
    device_brand = db.Column(db.String(50))  # 品牌
    device_model = db.Column(db.String(100))  # 型号
    device_sn = db.Column(db.String(100))  # 序列号
    device_imei = db.Column(db.String(50))  # IMEI
    device_password = db.Column(db.String(100))  # 密码
    device_need_door = db.Column(db.Integer, default=0)  # 是否需要上门 0否 1是

    # 网络相关字段（网络维修维护）
    net_type = db.Column(db.String(50))  # 网络类型: 宽带/企业网/家庭网/无线覆盖
    net_operator = db.Column(db.String(50))  # 运营商: 电信/移动/联通/其他
    net_need_device = db.Column(db.Integer, default=0)  # 是否需要提供设备

    # 配送相关字段（设备配送安装、产品代购）
    goods_type = db.Column(db.String(50))  # 货物类型
    goods_quantity = db.Column(db.Integer, default=1)  # 货物数量
    goods_need_install = db.Column(db.Integer, default=0)  # 是否需要安装调试
    goods_floor_type = db.Column(db.String(20))  # 楼层类型: 有电梯/无电梯
    goods_floor = db.Column(db.Integer, default=1)  # 楼层数

    # 监控相关字段（监控维修安装）
    monitor_brand = db.Column(db.String(50))  # 监控品牌: 海康威视/大华/宇视/其他
    camera_count = db.Column(db.Integer, default=0)  # 摄像头数量
    camera_location = db.Column(db.String(255))  # 安装位置
    monitor_need_record = db.Column(db.Integer, default=0)  # 是否需要录像存储
    record_days = db.Column(db.Integer, default=7)  # 录像存储天数

    # 通用字段
    fault_desc = db.Column(db.Text)  # 故障描述/需求描述
    appearance_desc = db.Column(db.Text)  # 外观描述
    accessories = db.Column(db.Text)  # 随机配件
    remark = db.Column(db.Text)

    # 状态相关
    status = db.Column(db.Integer, default=0)  # 状态: 0待处理 1已派单 2处理中 3待配件 4待确认 5已完成 6已取消
    status_name = db.Column(db.String(50))  # 状态名称

    # 费用相关
    labor_cost = db.Column(db.Numeric(15, 2), default=0.00)  # 人工费
    parts_cost = db.Column(db.Numeric(15, 2), default=0.00)  # 配件费
    material_cost = db.Column(db.Numeric(15, 2), default=0.00)  # 材料费
    transport_cost = db.Column(db.Numeric(15, 2), default=0.00)  # 运输费
    total_cost = db.Column(db.Numeric(15, 2), default=0.00)  # 总费用

    # 结算相关
    settlement_status = db.Column(db.Integer, default=0)  # 结算状态 0未结算 1已结算
    settlement_account_id = db.Column(BigIntPK)  # 结算账户
    settlement_time = db.Column(db.DateTime)  # 结算时间

    # 派单相关
    assigned_user_id = db.Column(BigIntPK)  # 指派技师
    assigned_user_name = db.Column(db.String(50))  # 技师姓名
    assigned_time = db.Column(db.DateTime)  # 指派时间

    # 报价关联
    quote_id = db.Column(BigIntPK)  # 关联报价单
    quote_confirmed = db.Column(db.Integer, default=0)  # 报价确认 0未确认 1已确认
    quote_confirm_time = db.Column(db.DateTime)  # 报价确认时间

    # 设备接收单
    receive_order_id = db.Column(BigIntPK)  # 关联接件单
    receive_confirmed = db.Column(db.Integer, default=0)  # 接收确认 0未确认 1已确认
    receive_confirm_time = db.Column(db.DateTime)  # 接收确认时间
    customer_sign = db.Column(db.String(255))  # 客户签字图片

    # 其他
    priority = db.Column(db.Integer, default=0)  # 优先级 0普通 1紧急 2特急
    estimated_time = db.Column(db.DateTime)  # 预计完成时间
    actual_time = db.Column(db.DateTime)  # 实际完成时间
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(BigIntPK)

    # ========== 新增通用字段 ==========
    customer_company = db.Column(db.String(200))  # 客户单位
    customer_office = db.Column(db.String(200))  # 办公室
    receiver_id = db.Column(BigIntPK)  # 接待员工ID
    receiver_name = db.Column(db.String(50))  # 接待员工姓名
    need_bring_back = db.Column(db.Integer, default=0)  # 是否需带回维修(0否1是)
    receive_order_id = db.Column(BigIntPK)  # 关联接件单ID
    related_quote_id = db.Column(BigIntPK)  # 关联报价单ID
    related_purchase_id = db.Column(BigIntPK)  # 关联采购单ID
    related_sales_id = db.Column(BigIntPK)  # 关联销售单ID
    related_finance_id = db.Column(BigIntPK)  # 关联财务记录ID
    auto_dispatch = db.Column(db.Integer, default=0)  # 派单方式(0手动1自动)
    dispatch_rule = db.Column(db.String(100))  # 派单规则
    labor_hours = db.Column(db.Numeric(10, 2))  # 工时
    labor_unit_price = db.Column(db.Numeric(10, 2))  # 人工费单价
    service_fee = db.Column(db.Numeric(10, 2), default=0)  # 代购服务费
    delivery_address = db.Column(db.String(500))  # 配送地址
    install_position = db.Column(db.String(500))  # 安装位置
    arrival_time = db.Column(db.DateTime)  # 到货时间
    install_material = db.Column(db.Text)  # 安装材料
    acceptance_standard = db.Column(db.Text)  # 验收标准
    customer_confirm_items = db.Column(db.Text)  # 客户确认项
    survey_address = db.Column(db.String(500))  # 勘察地址
    site_environment = db.Column(db.Text)  # 现场环境
    device_status_desc = db.Column(db.Text)  # 设备现状
    problem_summary = db.Column(db.Text)  # 问题汇总
    construction_plan = db.Column(db.Text)  # 施工方案
    required_parts = db.Column(db.Text)  # 所需设备配件(JSON)
    estimated_duration = db.Column(db.String(50))  # 预估工期
    estimated_cost = db.Column(db.Numeric(10, 2))  # 预估费用
    customer_device_model = db.Column(db.String(200))  # 客户自有设备型号
    device_source = db.Column(db.String(100))  # 设备来源
    install_requirement = db.Column(db.Text)  # 安装要求
    consumable_usage = db.Column(db.Text)  # 耗材使用
    purchase_product = db.Column(db.String(500))  # 代购产品名称
    purchase_brand = db.Column(db.String(100))  # 代购品牌
    purchase_spec = db.Column(db.String(200))  # 代购规格
    purchase_qty = db.Column(db.Integer)  # 代购数量
    customer_demand = db.Column(db.Text)  # 客户需求
    expected_arrival_date = db.Column(db.Date)  # 预期到货时间
    purchase_price = db.Column(db.Numeric(10, 2))  # 采购价
    finish_report = db.Column(db.Text)  # 完工报告
    finish_photos = db.Column(db.Text)  # 完工照片(JSON)
    test_result = db.Column(db.Integer, default=0)  # 测试结果(0待测/1通过/2未通过)
    test_remark = db.Column(db.Text)  # 测试备注
    return_visit_time = db.Column(db.DateTime)  # 上门送回时间
    return_visit_result = db.Column(db.Text)  # 上门送回结果
    customer_acceptance = db.Column(db.Integer, default=0)  # 客户验收(0待验收/1已验收/2未通过)
    customer_acceptance_time = db.Column(db.DateTime)  # 验收时间
    customer_acceptance_sign = db.Column(db.String(500))  # 验收签字图片
    print_count = db.Column(db.Integer, default=0)  # 打印次数

    # ========== 网络维修专属字段 ==========
    net_topology = db.Column(db.Text)  # 网络拓扑
    fault_location = db.Column(db.String(500))  # 故障点位
    net_ip = db.Column(db.String(50))  # IP地址
    device_port = db.Column(db.String(50))  # 设备端口
    line_type = db.Column(db.String(50))  # 线路类型
    test_items = db.Column(db.Text)  # 检测项目
    net_speed_data = db.Column(db.String(200))  # 网络测速数据
    maintenance_cycle = db.Column(db.String(50))  # 维护周期
    restart_record = db.Column(db.Text)  # 重启记录
    debug_content = db.Column(db.Text)  # 调试内容

    # ========== 设备维修专属字段 ==========
    device_config = db.Column(db.Text)  # 设备配置
    os_version = db.Column(db.String(100))  # 系统版本
    error_code = db.Column(db.String(100))  # 报错代码
    repair_part = db.Column(db.String(200))  # 维修部位
    maintenance_items = db.Column(db.Text)  # 保养项目
    replaced_parts = db.Column(db.Text)  # 更换配件清单(JSON)
    retest_result = db.Column(db.Text)  # 复测结果

    # ========== 监控维修专属字段 ==========
    channel_no = db.Column(db.String(50))  # 通道号
    nvr_model = db.Column(db.String(100))  # NVR型号
    disk_capacity = db.Column(db.String(50))  # 硬盘容量
    recording_status = db.Column(db.String(50))  # 录像状态
    screen_fault = db.Column(db.String(200))  # 画面故障
    infrared_status = db.Column(db.String(50))  # 红外状态
    power_status = db.Column(db.String(50))  # 供电状态
    line_inspection = db.Column(db.Text)  # 线路检修
    point_debug_record = db.Column(db.Text)  # 点位调试记录

    # ========== 监控安装专属字段 ==========
    install_points = db.Column(db.Text)  # 安装点位
    camera_model = db.Column(db.String(100))  # 摄像头型号
    storage_config = db.Column(db.String(200))  # 存储配置
    cable_length = db.Column(db.String(50))  # 布线长度
    consumable_qty = db.Column(db.String(100))  # 耗材数量
    debug_result = db.Column(db.Text)  # 调试结果
    picture_clarity = db.Column(db.String(50))  # 画面清晰度
    recording_settings = db.Column(db.Text)  # 录像设置

    # ========== 新增字段 ==========
    delivery_products = db.Column(db.Text)  # 配送产品清单(JSON)
    repair_camera_count = db.Column(db.Integer, default=0)  # 需维修的监控数量


class WorkOrderPart(db.Model):
    """工单配件明细"""
    __tablename__ = 'work_order_part'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    wo_id = db.Column(BigIntPK, nullable=False)
    product_id = db.Column(BigIntPK)
    product_name = db.Column(db.String(200))
    product_code = db.Column(db.String(50))
    specification = db.Column(db.String(200))  # 规格
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit_price = db.Column(db.Numeric(15, 4), default=0.0000)
    total_price = db.Column(db.Numeric(15, 2), default=0.00)
    cost_price = db.Column(db.Numeric(15, 4), default=0.0000)
    is_own = db.Column(db.Integer, default=1)  # 是否本店配件 1是 0客户自带
    status = db.Column(db.Integer, default=0)  # 0待用 1已用 2已退
    used_quantity = db.Column(db.Numeric(15, 3), default=0)  # 已使用数量
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


class WorkOrderQuoteItem(db.Model):
    """工单报价配件明细"""
    __tablename__ = 'work_order_quote_item'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    work_order_id = db.Column(BigIntPK, nullable=False, index=True)
    product_name = db.Column(db.String(200), nullable=False)
    spec = db.Column(db.String(200))
    unit = db.Column(db.String(50))
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit_price = db.Column(db.Numeric(15, 4), default=0.0000)
    subtotal = db.Column(db.Numeric(15, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.now)


class WorkOrderLog(db.Model):
    """工单操作日志"""
    __tablename__ = 'work_order_log'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    wo_id = db.Column(BigIntPK, nullable=False)
    action = db.Column(db.String(50))
    old_status = db.Column(db.Integer)
    new_status = db.Column(db.Integer)
    content = db.Column(db.Text)
    operator_id = db.Column(BigIntPK)
    operator_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)


class WorkOrderExtend(db.Model):
    """工单扩展信息（关联表存储接单方式、处理方式等）"""
    __tablename__ = 'work_order_extend'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    wo_id = db.Column(BigIntPK, nullable=False, index=True)  # 工单ID
    order_source = db.Column(db.String(20))  # 接单方式: wechat/phone/other
    service_type = db.Column(db.String(20))  # 处理方式: onsite/remote
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class WoCustomerPart(db.Model):
    """工单客户需求配件（只做信息记录，不直接扣库存）"""
    __tablename__ = 'wo_customer_part'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    wo_id = db.Column(BigIntPK, nullable=False, index=True)
    product_id = db.Column(BigIntPK)
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(200))
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, default=0)
    remark = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)