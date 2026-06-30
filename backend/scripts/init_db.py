"""
SQLite 数据库初始化脚本。
- 读取 backend/database/init.sql 并执行
- 插入种子数据（默认管理员 + 默认角色）

用法：
    python -m scripts.init_db
    或
    cd backend && python scripts/init_db.py
"""
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

import bcrypt

# 允许直接 `python scripts/init_db.py` 运行时找到 app / extensions / models
_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
_PROJECT_ROOT = _BACKEND.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(_PROJECT_ROOT))

# 强制 .env（如有）
try:
    from dotenv import load_dotenv
    env_path = _PROJECT_ROOT / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


def _project_root() -> Path:
    return _PROJECT_ROOT


def _db_path() -> Path:
    return _project_root() / 'data' / 'repair_system.db'


def _resolve_sqlite_uri() -> Path:
    """从 DATABASE_URL 或默认路径解析 SQLite 文件路径。"""
    url = os.environ.get('DATABASE_URL', '')
    if url.startswith('sqlite:///'):
        path = url[len('sqlite:///'):]
        if path == ':memory:':
            return None
        p = Path(path)
        if not p.is_absolute():
            p = _project_root() / path
        return p
    # 默认
    return _db_path()


def init_database():
    """执行 init.sql + 写入种子数据。"""
    db_file = _resolve_sqlite_uri()
    if db_file is None:
        raise RuntimeError('DATABASE_URL 指向内存数据库，不应执行 init_db 脚本')

    db_file.parent.mkdir(parents=True, exist_ok=True)
    sql_file = _BACKEND / 'database' / 'init.sql'
    if not sql_file.exists():
        raise FileNotFoundError(f'找不到 init.sql: {sql_file}')

    print(f'[init_db] 目标数据库: {db_file}')
    if db_file.exists():
        print(f'[init_db] 警告：{db_file} 已存在，将被覆盖')
        db_file.unlink()
    # 清理 WAL/SHM 残留
    for suffix in ('-wal', '-shm'):
        sidecar = db_file.with_name(db_file.name + suffix)
        if sidecar.exists():
            sidecar.unlink()

    conn = sqlite3.connect(str(db_file))
    try:
        conn.executescript(sql_file.read_text(encoding='utf-8'))
        _seed(conn)
        conn.commit()
        print('[init_db] 数据库初始化完成 [OK]')
    finally:
        conn.close()


def _seed(conn: sqlite3.Connection):
    """插入默认管理员和角色。"""
    now = datetime.now().isoformat(sep=' ')
    default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', '123456')
    password_hash = bcrypt.hashpw(
        default_password.encode('utf-8'), bcrypt.gensalt()
    ).decode('utf-8')

    # 默认角色（permissions 是 JSON 字符串）
    # 实际字段：role_name / role_code（不是 name / code）
    roles = [
        ('系统管理员', 'admin', '["*"]', '全部权限'),
        ('维修技师', 'technician', '["workorder.*","inventory.read"]', '工单与库存查看'),
        ('财务', 'finance', '["finance.*","report.read"]', '财务模块'),
        ('库管', 'warehouse', '["inventory.*","purchase.read","sales.read"]', '库存与采购'),
    ]
    for role_name, role_code, perms, desc in roles:
        conn.execute(
            'INSERT INTO sys_role (role_name, role_code, permissions, description, status, created_at, updated_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (role_name, role_code, perms, desc, 1, now, now),
        )

    # 默认管理员用户（关联到 admin 角色）
    # 实际字段：password（不是 password_hash）
    admin_role = conn.execute(
        "SELECT id FROM sys_role WHERE role_code = 'admin'"
    ).fetchone()
    role_id = admin_role[0] if admin_role else None

    conn.execute(
        'INSERT INTO sys_user (username, password, real_name, status, role_id, created_at, updated_at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        ('admin', password_hash, '系统管理员', 1, role_id, now, now),
    )
    print(f'[init_db] 已创建默认管理员: admin / {default_password}')


if __name__ == '__main__':
    init_database()