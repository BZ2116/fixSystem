"""数据迁移脚本：把状态机修复前的旧状态值迁移到新值。

迁移内容：
- work_order.status=10 → 7 (WO_STATUS_MAP 的"已取消")
- receive_order.status=14 (quote_confirmed=2 客户拒绝) → 17 (新状态"客户拒绝报价")

幂等：可重跑，第二次运行不会改任何东西（WHERE 已不匹配新值）。

调用方式：
- 独立运行：python scripts/migrate_status.py
- 在测试中：from scripts.migrate_status import migrate; migrate(db_path)
- 启动时自动调用：在 init_db.py / app factory 中调用 migrate_default()
"""
import logging
import sqlite3
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _resolve_default_db_path():
    """从 DATABASE_URL 解析 SQLite 文件路径。"""
    import os
    url = os.environ.get('DATABASE_URL', '')
    if url.startswith('sqlite:///'):
        path = url[len('sqlite:///'):]
        if path == ':memory:':
            return None
        p = Path(path)
        if not p.is_absolute():
            # 相对路径，相对于 project root
            _HERE = Path(__file__).resolve().parent
            _PROJECT_ROOT = _HERE.parent.parent
            p = _PROJECT_ROOT / path
        return p
    return None


def migrate(db_path: str) -> dict:
    """对指定 SQLite 文件运行迁移。返回修改行数统计。"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        # 1. work_order.status=10 → 7
        cur.execute('UPDATE work_order SET status=7 WHERE status=10')
        wo_count = cur.rowcount

        # 2. receive_order.status=14 且 quote_confirmed=2 → 17
        # 仅迁移"客户拒绝报价"场景，避免误改外店取回待测试(14)
        cur.execute(
            'UPDATE receive_order SET status=17 '
            'WHERE status=14 AND quote_confirmed=2'
        )
        ro_count = cur.rowcount

        conn.commit()
        logger.info('migrate_status: work_order 10→7 修改 %d 行, receive_order 14→17 修改 %d 行',
                    wo_count, ro_count)
        return {'work_order': wo_count, 'receive_order': ro_count}
    finally:
        conn.close()


def migrate_default() -> dict:
    """迁移默认数据库（从 DATABASE_URL 解析）。"""
    p = _resolve_default_db_path()
    if p is None:
        logger.info('migrate_status: 跳过（内存数据库）')
        return {'work_order': 0, 'receive_order': 0}
    if not p.exists():
        logger.info('migrate_status: 跳过（数据库文件不存在: %s）', p)
        return {'work_order': 0, 'receive_order': 0}
    return migrate(str(p))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    result = migrate_default()
    print(f'[migrate_status] 完成: {result}')
    sys.exit(0)
