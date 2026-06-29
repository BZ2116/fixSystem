"""SQLAlchemy 模型 → dict 序列化工具。"""
from datetime import datetime, date
from decimal import Decimal


def to_dict(model, fields=None, exclude=None):
    """通用序列化。

    Args:
        model: SQLAlchemy 模型实例
        fields: 白名单字段列表（None 表示全部）
        exclude: 黑名单字段列表
    """
    if model is None:
        return None
    exclude = set(exclude or [])
    result = {}
    for col in model.__table__.columns:
        if col.name in exclude:
            continue
        if fields and col.name not in fields:
            continue
        value = getattr(model, col.name)
        result[col.name] = _serialize_value(value)
    return result


def _serialize_value(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, Decimal):
        # 用 str 保留精度；float 会丢精度，财务字段不能接受
        return str(value)
    return value