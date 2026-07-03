"""
SQLAlchemy 通用 mixin。

2026-06-30: 替代 MySQL 的 `ON UPDATE CURRENT_TIMESTAMP`（spec §4）。
SQLAlchemy 的 onupdate 钩子在 app 层运行，SQLite 兼容。
"""
from datetime import datetime

from extensions import db

# BigInteger 主键：SQLite 用 Integer 走 ROWID 自增，MySQL/PostgreSQL 用 BigInteger。
BigIntPK = db.BigInteger().with_variant(db.Integer, "sqlite")


class TimestampMixin:
    """created_at / updated_at 自动管理。"""
    created_at = db.Column(
        db.DateTime, default=datetime.now, nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )