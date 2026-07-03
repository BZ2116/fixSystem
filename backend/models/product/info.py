from datetime import datetime

from extensions import db
from .._base import BigIntPK


class ProductInfo(db.Model):
    """商品信息"""
    __tablename__ = 'product_info'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    product_code = db.Column(db.String(50), unique=True, nullable=False)
    barcode = db.Column(db.String(50), unique=True)
    product_name = db.Column(db.String(200), nullable=False)
    pinyin_code = db.Column(db.String(200))
    category_id = db.Column(BigIntPK)
    category_name = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    specification = db.Column(db.String(100))
    unit_id = db.Column(BigIntPK)
    unit_name = db.Column(db.String(20))
    sub_unit_id = db.Column(BigIntPK)  # 辅助单位
    sub_unit_rate = db.Column(db.Numeric(10, 4))  # 换算率
    purchase_price = db.Column(db.Numeric(15, 4), default=0.0000)
    sale_price = db.Column(db.Numeric(15, 4), default=0.0000)
    member_price = db.Column(db.Numeric(15, 4), default=0.0000)
    wholesale_price = db.Column(db.Numeric(15, 4), default=0.0000)  # 批发价
    customer_price = db.Column(db.Numeric(15, 4), default=0.0000)  # 客户价
    cost_price = db.Column(db.Numeric(15, 4), default=0.0000)
    min_stock = db.Column(db.Integer, default=0)
    max_stock = db.Column(db.Integer, default=0)
    current_stock = db.Column(db.Integer, default=0)
    weight = db.Column(db.Numeric(10, 3))
    volume = db.Column(db.Numeric(10, 3))
    shelf_life = db.Column(db.Integer)
    is_serial = db.Column(db.Integer, default=0)  # 是否序列号管理
    is_batch = db.Column(db.Integer, default=0)  # 是否批次管理
    is_assembly = db.Column(db.Integer, default=0)  # 是否组装件
    is_gift = db.Column(db.Integer, default=0)  # 是否赠品
    no_cost = db.Column(db.Integer, default=0)  # 是否不计成本
    no_stock = db.Column(db.Integer, default=0)  # 是否不计库存
    status = db.Column(db.Integer, default=1)
    remark = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    shelf_id = db.Column(BigIntPK)  # 默认货架
    shelf_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ProductCategory(db.Model):
    """商品分类"""
    __tablename__ = 'product_category'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(BigIntPK, default=0)
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)


class ProductUnit(db.Model):
    """商品单位"""
    __tablename__ = 'product_unit'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    unit_name = db.Column(db.String(50), nullable=False)  # 单位名称
    unit_code = db.Column(db.String(20), unique=True)  # 单位编码
    conversion_rate = db.Column(db.Numeric(10, 4), default=1.0000)  # 换算率
    is_base = db.Column(db.Integer, default=0)  # 是否基本单位 1是 0否
    sort_order = db.Column(db.Integer, default=0)  # 排序
    status = db.Column(db.Integer, default=1)  # 状态 1启用 0禁用
    created_at = db.Column(db.DateTime, default=datetime.now)


class ProductUnitRel(db.Model):
    """商品多单位关联表"""
    __tablename__ = 'product_unit_rel'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    product_id = db.Column(BigIntPK, nullable=False)  # 商品ID
    unit_id = db.Column(BigIntPK, nullable=False)  # 单位ID
    conversion_rate = db.Column(db.Numeric(10, 4), default=1.0000)  # 换算率
    is_default = db.Column(db.Integer, default=0)  # 是否默认单位 1是 0否
    created_at = db.Column(db.DateTime, default=datetime.now)