from datetime import datetime

from extensions import db


class InventoryStock(db.Model):
    """库存明细"""
    __tablename__ = 'inventory_stock'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(db.BigInteger, nullable=False)
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    warehouse_id = db.Column(db.BigInteger, default=1)
    warehouse_name = db.Column(db.String(50), default='主仓库')
    shelf_id = db.Column(db.BigInteger)  # 货架ID
    shelf_name = db.Column(db.String(100))  # 货架名称
    quantity = db.Column(db.Numeric(10, 2), default=0)  # 库存数量
    frozen_quantity = db.Column(db.Numeric(10, 2), default=0)  # 冻结数量
    available_quantity = db.Column(db.Numeric(10, 2), default=0)  # 可用数量
    cost_price = db.Column(db.Numeric(15, 4), default=0.0000)
    batch_no = db.Column(db.String(50))
    serial_no = db.Column(db.String(100))
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class InventoryLog(db.Model):
    """库存变动明细"""
    __tablename__ = 'inventory_log'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(db.BigInteger)  # 商品ID
    product_code = db.Column(db.String(50))  # 商品编码
    product_name = db.Column(db.String(200))  # 商品名称
    warehouse_id = db.Column(db.BigInteger)  # 仓库ID
    warehouse_name = db.Column(db.String(50))  # 仓库名称
    change_type = db.Column(db.String(20))  # 变动类型：in入库/out出库/adjust调整/transfer调拨
    order_type = db.Column(db.String(30))  # 单据类型：采购入库/销售出库/维修领料/退货入库/调拨/盘点调整/成本调价
    order_id = db.Column(db.BigInteger)  # 关联单据ID
    order_no = db.Column(db.String(50))  # 关联单据号
    quantity_change = db.Column(db.Numeric(10, 2), default=0)  # 变动数量（正数增加，负数减少）
    before_quantity = db.Column(db.Numeric(10, 2), default=0)  # 变动前数量
    after_quantity = db.Column(db.Numeric(10, 2), default=0)  # 变动后数量
    cost_price = db.Column(db.Numeric(15, 4), default=0)  # 成本价
    amount = db.Column(db.Numeric(15, 2), default=0)  # 变动金额
    related_party = db.Column(db.String(100))  # 往来单位（客户/供应商）
    operator_id = db.Column(db.BigInteger)  # 操作人ID
    operator_name = db.Column(db.String(50))  # 操作人
    remark = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.now)


class CostAdjust(db.Model):
    """成本调价单"""
    __tablename__ = 'cost_adjust'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    adjust_no = db.Column(db.String(50), unique=True)  # 调价单号
    warehouse_id = db.Column(db.BigInteger)  # 仓库ID
    warehouse_name = db.Column(db.String(50))  # 仓库名称
    product_id = db.Column(db.BigInteger)  # 商品ID
    product_code = db.Column(db.String(50))  # 商品编码
    product_name = db.Column(db.String(200))  # 商品名称
    old_cost_price = db.Column(db.Numeric(15, 4), default=0)  # 原成本价
    new_cost_price = db.Column(db.Numeric(15, 4), default=0)  # 新成本价
    adjust_quantity = db.Column(db.Numeric(10, 2), default=0)  # 调整数量
    adjust_amount = db.Column(db.Numeric(15, 2), default=0)  # 调整金额（新成本-原成本）*数量
    status = db.Column(db.Integer, default=0)  # 状态：0待审核/1已审核/2已取消
    remark = db.Column(db.Text)  # 备注
    created_by = db.Column(db.BigInteger)  # 创建人ID
    created_by_name = db.Column(db.String(50))  # 创建人
    audited_by = db.Column(db.BigInteger)  # 审核人ID
    audited_by_name = db.Column(db.String(50))  # 审核人
    audited_at = db.Column(db.DateTime)  # 审核时间
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)