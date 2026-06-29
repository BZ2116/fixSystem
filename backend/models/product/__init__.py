"""商品子包：商品信息、分类、单位、多单位关联。"""
from .info import (
    ProductCategory,
    ProductInfo,
    ProductUnit,
    ProductUnitRel,
)

__all__ = [
    'ProductCategory',
    'ProductInfo',
    'ProductUnit',
    'ProductUnitRel',
]