"""校验 init.sql 与 SQLAlchemy 模型一致。

比较 init.sql 中的 (table, column) 集合与 db.metadata.tables 中的 (table, column) 集合。

运行方式（在 backend/ 目录下）：
    DATABASE_URL="sqlite:///test_check.db" JWT_SECRET_KEY=test python scripts/check_schema.py

退出码：
    0 - 完全匹配
    1 - 表级不匹配（缺失或多余）
    2 - 列级不匹配
    3 - init.sql 解析失败
"""
import os
import sqlite3
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
_INIT_SQL = _BACKEND / 'database' / 'init.sql'
_PROJECT_ROOT = _BACKEND.parent

# 应用层管理的表（无对应 SQLAlchemy 模型，但 init.sql 中存在）
ALLOWED_EXTRA_TABLES = {'jwt_blacklist'}


def get_init_sql_columns():
    """从 init.sql 提取 (table, column) 集合。"""
    conn = sqlite3.connect(':memory:')
    try:
        conn.executescript(_INIT_SQL.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'init.sql 解析失败: {e}')
        raise SystemExit(3)
    cols = set()
    for (table,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall():
        for (cid, name, ctype, notnull, dflt, pk) in conn.execute(
            f'PRAGMA table_info({table})'
        ).fetchall():
            cols.add((table, name))
    return cols


def get_model_columns():
    """从 SQLAlchemy 模型提取 (table, column) 集合。

    不创建 Flask app、不调用 create_app（避免触发 seed/blueprint 副作用）。
    直接把 db.metadata 关联到一个临时 sqlite URL，然后 import 所有模型子模块。
    """
    sys.path.insert(0, str(_BACKEND))
    sys.path.insert(0, str(_PROJECT_ROOT))

    # 在 import 之前先写好环境变量
    os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
    os.environ.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')

    from extensions import db  # noqa: E402

    # 用一个临时 sqlite db 让 metadata bind
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///:memory:'

    from sqlalchemy import create_engine  # noqa: E402
    engine = create_engine(db_url, future=True)
    db.metadata.bind = engine

    # 触发所有模型子模块导入，把表注册到 db.metadata
    import models  # noqa: F401  (models 包入口)
    from models import (  # noqa: F401
        asset, customer, dispatch, finance, inventory,
        printer, product, purchase, quote, receive,
        sales, supplier, system, workorder,
    )

    cols = set()
    for table in db.metadata.tables.values():
        for col in table.columns:
            cols.add((table.name, col.name))
    return cols


def main():
    init_cols = get_init_sql_columns()
    model_cols = get_model_columns()

    init_tables = {t for t, _ in init_cols}
    model_tables = {t for t, _ in model_cols}

    missing_tables = model_tables - init_tables
    extra_tables = init_tables - model_tables

    print(f'init.sql tables: {len(init_tables)}')
    print(f'model tables:   {len(model_tables)}')
    if missing_tables:
        print(f'missing in init.sql ({len(missing_tables)}): {sorted(missing_tables)}')
    if extra_tables:
        print(f'extra in init.sql ({len(extra_tables)}):  {sorted(extra_tables)}')

    missing_cols = model_cols - init_cols
    extra_cols = init_cols - model_cols
    if missing_cols:
        print(f'missing columns ({len(missing_cols)}):')
        for tc in sorted(missing_cols):
            print(f'  {tc[0]}.{tc[1]}')
    if extra_cols:
        print(f'extra columns ({len(extra_cols)}):')
        for tc in sorted(extra_cols):
            print(f'  {tc[0]}.{tc[1]}')

    unexpected_extra_tables = extra_tables - ALLOWED_EXTRA_TABLES
    unexpected_extra_cols = extra_cols  # 列级多出的也允许（应用层管理表）

    if missing_tables or unexpected_extra_tables:
        raise SystemExit(1)
    if missing_cols:
        raise SystemExit(2)
    print(f'OK: table and column sets match (allowed extras: {sorted(ALLOWED_EXTRA_TABLES)}).')


if __name__ == '__main__':
    main()