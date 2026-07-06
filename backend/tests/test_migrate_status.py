"""数据迁移脚本测试。

修复了状态机后，存量数据中的 status=10 (work_order) 和 status=14 (receive_order) 需要迁移到正确值。
- work_order.status=10 (旧的"已取消"） → 7 (WO_STATUS_MAP 的"已取消")
- receive_order.status=14 (旧的"客户拒绝报价"） → 17 (新状态, 与外店取回待测试 14 不冲突)
"""
import os
import sqlite3
import tempfile

import pytest


def _create_legacy_db(path: str) -> sqlite3.Connection:
    """创建一个临时 SQLite，插入 work_order/receive_order 模拟旧数据。"""
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE work_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wo_no TEXT,
            status INTEGER
        );
        CREATE TABLE receive_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receive_no TEXT,
            status INTEGER,
            quote_confirmed INTEGER DEFAULT 0
        );
    """)
    # 旧数据：work_order 10、receive_order 14 (quote_confirmed=2 是客户拒绝)
    conn.execute("INSERT INTO work_order (wo_no, status) VALUES ('WO-OLD-1', 10)")
    conn.execute("INSERT INTO work_order (wo_no, status) VALUES ('WO-OLD-2', 0)")
    conn.execute("INSERT INTO work_order (wo_no, status) VALUES ('WO-OLD-3', 10)")
    conn.execute("INSERT INTO receive_order (receive_no, status, quote_confirmed) VALUES ('RO-OLD-1', 14, 2)")
    conn.execute("INSERT INTO receive_order (receive_no, status, quote_confirmed) VALUES ('RO-OLD-2', 0, 0)")
    conn.execute("INSERT INTO receive_order (receive_no, status, quote_confirmed) VALUES ('RO-OLD-3', 14, 2)")
    conn.commit()
    conn.close()


def test_migrate_status_rewrites_legacy_values():
    """迁移脚本应把 work_order.status=10 改为 7，receive_order.status=14 改为 17。"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        _create_legacy_db(db_path)

        # 改环境变量指向这个临时库
        os.environ['MIGRATE_TEST_DB'] = f'sqlite:///{db_path}'
        # 调用迁移
        from scripts.migrate_status import migrate
        migrate(db_path)

        # 验证结果
        conn = sqlite3.connect(db_path)
        wo_statuses = [r[0] for r in conn.execute('SELECT status FROM work_order ORDER BY id').fetchall()]
        ro_statuses = [r[0] for r in conn.execute('SELECT status FROM receive_order ORDER BY id').fetchall()]
        conn.close()

        # WO-OLD-1: 10 → 7, WO-OLD-2: 0 (不变), WO-OLD-3: 10 → 7
        assert wo_statuses == [7, 0, 7], f'work_order 状态迁移错乱: {wo_statuses}'
        # RO-OLD-1: 14 → 17, RO-OLD-2: 0 (不变), RO-OLD-3: 14 → 17
        assert ro_statuses == [17, 0, 17], f'receive_order 状态迁移错乱: {ro_statuses}'
    finally:
        os.unlink(db_path)


def test_migrate_status_is_idempotent():
    """迁移脚本重跑应不报错，状态保持。"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        _create_legacy_db(db_path)
        # 关闭 _create_legacy_db 里的 conn（它返回的连接没在这里关闭）
        # 通过独立连接再访问
        from scripts.migrate_status import migrate
        migrate(db_path)
        # 再跑一次
        migrate(db_path)

        conn = sqlite3.connect(db_path)
        wo_statuses = [r[0] for r in conn.execute('SELECT status FROM work_order ORDER BY id').fetchall()]
        ro_statuses = [r[0] for r in conn.execute('SELECT status FROM receive_order ORDER BY id').fetchall()]
        conn.close()

        assert wo_statuses == [7, 0, 7]
        assert ro_statuses == [17, 0, 17]
    finally:
        os.unlink(db_path)


def test_migrate_status_handles_empty_db():
    """空表迁移应不报错。"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        conn = sqlite3.connect(db_path)
        conn.executescript("""
            CREATE TABLE work_order (id INTEGER PRIMARY KEY AUTOINCREMENT, wo_no TEXT, status INTEGER);
            CREATE TABLE receive_order (id INTEGER PRIMARY KEY AUTOINCREMENT, receive_no TEXT, status INTEGER, quote_confirmed INTEGER DEFAULT 0);
        """)
        conn.commit()
        conn.close()

        from scripts.migrate_status import migrate
        migrate(db_path)  # 不应抛错
    finally:
        os.unlink(db_path)
