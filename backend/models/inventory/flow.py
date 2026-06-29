from datetime import datetime

from extensions import db


class InventoryIn(db.Model):
    """入库单"""
    __tablename__ = 'inventory_in'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    in_no = db.Column(db.String(50), unique=True, nullable=False)
    in_type = db.Column(db.Integer, default=1)  # 1采购入库 2退货入库 3调拨入库 4组装入库 5其他入库
    supplier_id = db.Column(db.BigInteger)
    supplier_name = db.Column(db.String(100))
    warehouse_id = db.Column(db.BigInteger, default=1)
    warehouse_name = db.Column(db.String(50))
    total_quantity = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    status = db.Column(db.Integer, default=0)  # 0待审核 1已审核 2已入库
    auditor_id = db.Column(db.BigInteger)
    auditor_name = db.Column(db.String(50))
    audit_time = db.Column(db.DateTime)
    remark = db.Column(db.Text)
    related_order_id = db.Column(db.BigInteger)  # 关联单据ID
    related_order_no = db.Column(db.String(50))  # 关联单据号
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.BigInteger)


class InventoryInItem(db.Model):
    """入库单明细"""
    __tablename__ = 'inventory_in_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    in_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(100))
    unit_name = db.Column(db.String(20))
    quantity = db.Column(db.Numeric(10, 2), default=0)
    unit_price = db.Column(db.Numeric(15, 4), default=0.0000)
    total_price = db.Column(db.Numeric(15, 2), default=0.00)
    cost_price = db.Column(db.Numeric(15, 4), default=0.0000)
    batch_no = db.Column(db.String(50))
    serial_no = db.Column(db.String(100))
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


class InventoryOut(db.Model):
    """出库单"""
    __tablename__ = 'inventory_out'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    out_no = db.Column(db.String(50), unique=True, nullable=False)
    out_type = db.Column(db.Integer, default=1)  # 1销售出库 2维修领料 3调拨出库 4拆卸出库 5其他出库
    customer_id = db.Column(db.BigInteger)
    customer_name = db.Column(db.String(100))
    warehouse_id = db.Column(db.BigInteger, default=1)
    warehouse_name = db.Column(db.String(50))
    total_quantity = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    status = db.Column(db.Integer, default=0)  # 0待审核 1已审核 2已出库
    auditor_id = db.Column(db.BigInteger)
    auditor_name = db.Column(db.String(50))
    audit_time = db.Column(db.DateTime)
    remark = db.Column(db.Text)
    related_order_id = db.Column(db.BigInteger)
    related_order_no = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.BigInteger)


class InventoryOutItem(db.Model):
    """出库单明细"""
    __tablename__ = 'inventory_out_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    out_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(100))
    unit_name = db.Column(db.String(20))
    quantity = db.Column(db.Numeric(10, 2), default=0)
    unit_price = db.Column(db.Numeric(15, 4), default=0.0000)
    total_price = db.Column(db.Numeric(15, 2), default=0.00)
    cost_price = db.Column(db.Numeric(15, 4), default=0.0000)
    batch_no = db.Column(db.String(50))
    serial_no = db.Column(db.String(100))
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


class InventoryCheck(db.Model):
    """盘点单"""
    __tablename__ = 'inventory_check'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    check_no = db.Column(db.String(50), unique=True, nullable=False)
    warehouse_id = db.Column(db.BigInteger, default=1)
    warehouse_name = db.Column(db.String(50))
    shelf_id = db.Column(db.BigInteger)  # 货架ID
    shelf_name = db.Column(db.String(100))  # 货架名称
    check_date = db.Column(db.Date)
    status = db.Column(db.Integer, default=0)  # 0待盘点 1盘点中 2已完成
    total_quantity = db.Column(db.Integer, default=0)
    diff_quantity = db.Column(db.Integer, default=0)
    diff_amount = db.Column(db.Numeric(15, 2), default=0.00)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.BigInteger)


class InventoryCheckItem(db.Model):
    """盘点单明细"""
    __tablename__ = 'inventory_check_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    check_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(100))
    unit_name = db.Column(db.String(20))
    system_quantity = db.Column(db.Numeric(10, 2), default=0)  # 系统库存
    actual_quantity = db.Column(db.Numeric(10, 2), default=0)  # 实际库存
    diff_quantity = db.Column(db.Numeric(10, 2), default=0)  # 差异
    cost_price = db.Column(db.Numeric(15, 4), default=0.0000)
    diff_amount = db.Column(db.Numeric(15, 2), default=0.00)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


class TransferOrder(db.Model):
    """调拨单"""
    __tablename__ = 'transfer_order'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    transfer_no = db.Column(db.String(50), unique=True, nullable=False)
    from_warehouse_id = db.Column(db.BigInteger)
    from_warehouse_name = db.Column(db.String(50))
    to_warehouse_id = db.Column(db.BigInteger)
    to_warehouse_name = db.Column(db.String(50))
    total_quantity = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.Integer, default=0)  # 0待审核 1已审核 2已完成
    transfer_type = db.Column(db.Integer, default=1)  # 调拨类型：1同价调拨 2变价调拨
    from_cost_price = db.Column(db.Numeric(15, 4), default=0)  # 调出成本价
    to_cost_price = db.Column(db.Numeric(15, 4), default=0)  # 调入成本价（变价调拨时使用）
    operator_id = db.Column(db.BigInteger)  # 经手人ID
    operator_name = db.Column(db.String(50))  # 经手人
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.BigInteger)


class TransferOrderItem(db.Model):
    """调拨单明细"""
    __tablename__ = 'transfer_order_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    transfer_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(100))
    unit_name = db.Column(db.String(20))
    quantity = db.Column(db.Numeric(10, 2), default=0)
    from_cost_price = db.Column(db.Numeric(15, 4), default=0)  # 调出成本价
    to_cost_price = db.Column(db.Numeric(15, 4), default=0)  # 调入成本价
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


class AssembleOrder(db.Model):
    """组装单"""
    __tablename__ = 'assemble_order'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    assemble_no = db.Column(db.String(50), unique=True, nullable=False)
    product_id = db.Column(db.BigInteger)  # 组装成品ID
    product_name = db.Column(db.String(200))
    quantity = db.Column(db.Numeric(10, 2), default=1)
    warehouse_id = db.Column(db.BigInteger, default=1)
    warehouse_name = db.Column(db.String(50))
    status = db.Column(db.Integer, default=0)  # 0待审核 1已审核 2已完成
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.BigInteger)


class AssembleOrderItem(db.Model):
    """组装单明细（子件）"""
    __tablename__ = 'assemble_order_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    assemble_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    specification = db.Column(db.String(100))
    unit_name = db.Column(db.String(20))
    quantity = db.Column(db.Numeric(10, 2), default=0)
    cost_price = db.Column(db.Numeric(15, 4), default=0.0000)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


class PreOrder(db.Model):
    """预订单"""
    __tablename__ = 'pre_order'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    pre_no = db.Column(db.String(50), unique=True, nullable=False)
    pre_type = db.Column(db.Integer, default=1)  # 1采购预定 2销售预定
    customer_id = db.Column(db.BigInteger)
    customer_name = db.Column(db.String(100))
    supplier_id = db.Column(db.BigInteger)
    supplier_name = db.Column(db.String(100))
    total_quantity = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    status = db.Column(db.Integer, default=0)  # 0待处理 1已转单 2已取消
    related_order_id = db.Column(db.BigInteger)  # 转换后的单据ID
    related_order_no = db.Column(db.String(50))
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.BigInteger)


class PreOrderItem(db.Model):
    """预订单明细"""
    __tablename__ = 'pre_order_item'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    pre_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.BigInteger)
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    quantity = db.Column(db.Numeric(10, 2), default=0)
    unit_price = db.Column(db.Numeric(15, 4), default=0.0000)
    total_price = db.Column(db.Numeric(15, 2), default=0.00)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)