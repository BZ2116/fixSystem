# Repair System Portable SQLite Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有维修商贸系统从 MySQL+Redis+docker 架构迁移到 SQLite + 本地 Python 脚本 + 便携 zip 打包，使整个项目解压后可在任何 Windows 机器一键启动。

**Architecture:**
- 数据层：单文件 SQLite（WAL 模式）存放业务数据 + JWT 黑名单；上传文件存 `data/uploads/`
- 运行层：开发模式 Flask + Vite 双进程，生产模式 gunicorn + 预构建静态文件
- 部署层：跨平台 start/stop 脚本 + PID 文件管理；用 `scripts/build_portable.bat` 产出 `.zip`
- 删除：MySQL、Redis、Docker、PyInstaller

**Tech Stack:**
- 后端：Python 3.11 + Flask 2.3.3 + Flask-SQLAlchemy 3.0.5 + Flask-JWT-Extended 4.5.2
- 前端：Vue 3.2.47 + Vite 4.4.9 + Element Plus（不变）
- 数据：SQLite（stdlib `sqlite3`）+ 本地文件系统
- 进程：原生 `subprocess` + PID 文件（不用 docker，不用 PyInstaller）

**Reference Spec:** `docs/superpowers/specs/2026-06-30-repair-system-portable-tech-stack-design.md`

---

## File Structure Changes

**新增目录**：
- `backend/scripts/` — `init_db.py`、`start_dev.py`、`build_portable.bat`
- `data/` — 运行时数据根（uploads / logs / .pids）
- `docs/archive/docker-configs/` — 旧 docker 文件暂存
- `docs/archive/database_complete_v3.sql` — MySQL 原版仅作参考

**修改文件**：
- `backend/extensions.py`（移除 redis）
- `backend/app/config.py`（SQLite URI + 移除 MySQL 专属配置）
- `backend/app/security.py`（JWT 黑名单改 SQLite）
- `backend/app/__init__.py`（移除 init_redis 调用）
- `backend/requirements.txt`（移除 PyMySQL / redis）
- `backend/tests/conftest.py`（保留 in-memory SQLite）
- `README.md`（重写部署章节）
- `.gitignore`（加入 `data/`、`backend/.venv/`、`frontend/node_modules/`）
- 根目录新增 `.env.example`、`VERSION.txt`、4 个 `start*.bat/sh`、2 个 `stop*.bat/sh`

**删除文件**：
- 根 `app.py`（shim）
- 旧 `docker-compose.yml`（先搬后删）

**保留不变**：
- 27 个 blueprint 文件
- models 子目录的 SQLAlchemy 模型（仅加 TimestampMixin）
- 全部前端代码

---

## Phase 1: 准备与归档

### Task 1: 创建归档目录并移动 docker 文件

**Files:**
- Create: `docs/archive/docker-configs/.gitkeep`
- Move: `docker-compose.yml` → `docs/archive/docker-configs/docker-compose.yml`
- Move: `backend/Dockerfile` → `docs/archive/docker-configs/backend.Dockerfile`
- Move: `frontend/Dockerfile` → `docs/archive/docker-configs/frontend.Dockerfile`
- Move: `frontend/nginx.conf` → `docs/archive/docker-configs/frontend.nginx.conf`

- [ ] **Step 1: 创建归档目录**

```bash
mkdir -p docs/archive/docker-configs
```

- [ ] **Step 2: 移动 5 个 docker 相关文件**

Windows (PowerShell):
```powershell
Move-Item docker-compose.yml docs/archive/docker-configs/
Move-Item backend/Dockerfile docs/archive/docker-configs/backend.Dockerfile
Move-Item frontend/Dockerfile docs/archive/docker-configs/frontend.Dockerfile
Move-Item frontend/nginx.conf docs/archive/docker-configs/frontend.nginx.conf
```

- [ ] **Step 3: 验证移动结果**

```bash
ls docs/archive/docker-configs/
```

Expected output:
```
backend.Dockerfile
docker-compose.yml
frontend.Dockerfile
frontend.nginx.conf
```

- [ ] **Step 4: 提交**

```bash
git add docs/archive/docker-configs/
git rm docker-compose.yml backend/Dockerfile frontend/Dockerfile frontend/nginx.conf
git commit -m "chore: archive docker files (will delete after 2 weeks)"
```

---

### Task 2: 归档 MySQL 原版 schema

**Files:**
- Move: `database_complete_v3.sql` → `docs/archive/database_complete_v3.sql`

- [ ] **Step 1: 移动 MySQL schema**

```bash
git mv database_complete_v3.sql docs/archive/database_complete_v3.sql
```

- [ ] **Step 2: 验证**

```bash
ls docs/archive/
```

Expected: 包含 `database_complete_v3.sql` 和 `docker-configs/` 子目录

- [ ] **Step 3: 提交**

```bash
git commit -m "chore: archive MySQL schema as reference only"
```

---

### Task 3: 创建运行时目录骨架

**Files:**
- Create: `data/.gitkeep`
- Create: `data/uploads/.gitkeep`
- Create: `data/logs/.gitkeep`
- Create: `data/.pids/.gitkeep`
- Create: `backend/scripts/__init__.py`

- [ ] **Step 1: 创建 data/ 子目录**

Windows (PowerShell):
```powershell
New-Item -ItemType Directory -Force -Path data\uploads,data\logs,data\.pids
"" | Set-Content -Path data\uploads\.gitkeep
"" | Set-Content -Path data\logs\.gitkeep
"" | Set-Content -Path data\.pids\.gitkeep
"" | Set-Content -Path data\.gitkeep
```

- [ ] **Step 2: 创建 backend/scripts 目录**

```bash
mkdir -p backend/scripts
touch backend/scripts/__init__.py
```

- [ ] **Step 3: 验证结构**

```bash
ls data/
```

Expected: 包含 `.gitkeep`、`.pids/`、`logs/`、`uploads/`

- [ ] **Step 4: 提交**

```bash
git add data/ backend/scripts/__init__.py
git commit -m "chore: create data/ runtime directories and scripts/ skeleton"
```

---

## Phase 2: 数据库 Schema

### Task 4: 创建 SQLite 初始化脚本

**Files:**
- Create: `backend/database/init.sql`

> 注意：本任务只创建 schema（CREATE TABLE）部分，不包含种子数据。种子数据由 `init_db.py` 单独处理（Task 6）。

- [ ] **Step 1: 创建空文件**

```bash
touch backend/database/init.sql
```

- [ ] **Step 2: 写入 SQLite schema（按业务域分块）**

打开 `backend/database/init.sql`，写入以下内容（按当前 `docs/archive/database_complete_v3.sql` 的业务域结构，对应翻译为 SQLite 语法）：

```sql
-- ============================================
-- Repair System SQLite Schema
-- Generated from MySQL version; SQLite-compatible.
-- All tables: InnoDB → SQLite, AUTO_INCREMENT → INTEGER PRIMARY KEY,
--   ON UPDATE CURRENT_TIMESTAMP → handled in app layer,
--   JSON columns → TEXT (SQLAlchemy db.JSON 兼容),
--   ENUM → TEXT with CHECK constraints (none in current schema).
-- ============================================

PRAGMA foreign_keys = ON;

-- ----- system -----
CREATE TABLE sys_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    real_name TEXT,
    phone TEXT,
    email TEXT,
    avatar TEXT,
    role_id INTEGER,
    status INTEGER NOT NULL DEFAULT 1,
    last_login_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE sys_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    permissions TEXT,  -- JSON array
    description TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE operation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    module TEXT,
    action TEXT,
    target_id INTEGER,
    target_type TEXT,
    detail TEXT,
    ip TEXT,
    created_at DATETIME NOT NULL
);

CREATE TABLE data_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    before_data TEXT,
    after_data TEXT,
    created_at DATETIME NOT NULL
);

CREATE TABLE print_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- ----- product / inventory -----
CREATE TABLE product_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE product_unit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category_id INTEGER,
    unit_id INTEGER,
    barcode TEXT,
    spec TEXT,
    cost_price DECIMAL(10,2) DEFAULT 0,
    sale_price DECIMAL(10,2) DEFAULT 0,
    stock INTEGER DEFAULT 0,
    stock_warning INTEGER DEFAULT 0,
    description TEXT,
    image TEXT,
    status INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    warehouse TEXT,
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_cost DECIMAL(10,2) DEFAULT 0,
    updated_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE stock_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    change_qty INTEGER NOT NULL,
    before_qty INTEGER,
    after_qty INTEGER,
    ref_type TEXT,
    ref_id INTEGER,
    operator_id INTEGER,
    remark TEXT,
    created_at DATETIME NOT NULL
);

CREATE TABLE stocktake (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    operator_id INTEGER,
    total_diff INTEGER DEFAULT 0,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE stocktake_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stocktake_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    book_qty INTEGER NOT NULL,
    actual_qty INTEGER NOT NULL,
    diff INTEGER NOT NULL,
    created_at DATETIME NOT NULL
);

-- ----- customer / supplier -----
CREATE TABLE customer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT NOT NULL,
    contact TEXT,
    phone TEXT,
    address TEXT,
    discount_rate DECIMAL(5,2) DEFAULT 100.00,
    balance DECIMAL(12,2) DEFAULT 0,
    level TEXT,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT NOT NULL,
    contact TEXT,
    phone TEXT,
    address TEXT,
    balance DECIMAL(12,2) DEFAULT 0,
    is_outsource INTEGER DEFAULT 0,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- ----- workorder -----
CREATE TABLE workorder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,        -- install/repair/maintain/network_install/network_repair/network_maintain
    customer_id INTEGER,
    customer_name TEXT,
    contact TEXT,
    phone TEXT,
    address TEXT,
    device TEXT,
    fault_desc TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending/assigned/processing/completed/cancelled
    technician_id INTEGER,
    outsource_supplier_id INTEGER,
    expected_at DATETIME,
    completed_at DATETIME,
    total_amount DECIMAL(12,2) DEFAULT 0,
    cost_amount DECIMAL(12,2) DEFAULT 0,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE workorder_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workorder_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    operator_id INTEGER,
    operator_name TEXT,
    detail TEXT,
    created_at DATETIME NOT NULL
);

CREATE TABLE workorder_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workorder_id INTEGER NOT NULL,
    product_id INTEGER,
    name TEXT,
    qty DECIMAL(10,2) DEFAULT 0,
    price DECIMAL(10,2) DEFAULT 0,
    cost DECIMAL(10,2) DEFAULT 0,
    created_at DATETIME NOT NULL
);

-- ----- purchase / receive / sales -----
CREATE TABLE purchase_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    supplier_id INTEGER,
    warehouse TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    total_amount DECIMAL(12,2) DEFAULT 0,
    paid_amount DECIMAL(12,2) DEFAULT 0,
    operator_id INTEGER,
    remark TEXT,
    purchase_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE purchase_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    product_id INTEGER,
    qty DECIMAL(10,2) DEFAULT 0,
    price DECIMAL(10,2) DEFAULT 0,
    amount DECIMAL(12,2) DEFAULT 0,
    created_at DATETIME NOT NULL
);

CREATE TABLE receive_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,        -- purchase_return/sales_return/receive
    related_id INTEGER,
    supplier_id INTEGER,
    customer_id INTEGER,
    warehouse TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    total_amount DECIMAL(12,2) DEFAULT 0,
    operator_id INTEGER,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE receive_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receive_id INTEGER NOT NULL,
    product_id INTEGER,
    qty DECIMAL(10,2) DEFAULT 0,
    price DECIMAL(10,2) DEFAULT 0,
    amount DECIMAL(12,2) DEFAULT 0,
    created_at DATETIME NOT NULL
);

CREATE TABLE sales_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,        -- sale/retail
    customer_id INTEGER,
    warehouse TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    total_amount DECIMAL(12,2) DEFAULT 0,
    paid_amount DECIMAL(12,2) DEFAULT 0,
    operator_id INTEGER,
    remark TEXT,
    sale_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE sales_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_id INTEGER NOT NULL,
    product_id INTEGER,
    qty DECIMAL(10,2) DEFAULT 0,
    price DECIMAL(10,2) DEFAULT 0,
    amount DECIMAL(12,2) DEFAULT 0,
    created_at DATETIME NOT NULL
);

CREATE TABLE preorder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    product_id INTEGER,
    qty DECIMAL(10,2) DEFAULT 0,
    deposit DECIMAL(12,2) DEFAULT 0,
    expected_at DATETIME,
    status TEXT NOT NULL DEFAULT 'pending',
    operator_id INTEGER,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE return_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    related_id INTEGER,
    supplier_id INTEGER,
    customer_id INTEGER,
    total_amount DECIMAL(12,2) DEFAULT 0,
    operator_id INTEGER,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- ----- quote / dispatch -----
CREATE TABLE quote (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    total_amount DECIMAL(12,2) DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    operator_id INTEGER,
    valid_until DATETIME,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE quote_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    product_id INTEGER,
    qty DECIMAL(10,2) DEFAULT 0,
    price DECIMAL(10,2) DEFAULT 0,
    amount DECIMAL(12,2) DEFAULT 0,
    created_at DATETIME NOT NULL
);

CREATE TABLE dispatch_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    workorder_id INTEGER,
    technician_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    dispatched_at DATETIME,
    completed_at DATETIME,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- ----- finance -----
CREATE TABLE account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    balance DECIMAL(12,2) DEFAULT 0,
    bank TEXT,
    account_no TEXT,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,        -- receive/pay
    account_id INTEGER,
    customer_id INTEGER,
    supplier_id INTEGER,
    related_type TEXT,
    related_id INTEGER,
    amount DECIMAL(12,2) DEFAULT 0,
    operator_id INTEGER,
    remark TEXT,
    paid_at DATETIME,
    created_at DATETIME NOT NULL
);

CREATE TABLE invoice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT UNIQUE,
    type TEXT NOT NULL,
    customer_id INTEGER,
    supplier_id INTEGER,
    related_type TEXT,
    related_id INTEGER,
    amount DECIMAL(12,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    operator_id INTEGER,
    issued_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    account_id INTEGER,
    amount DECIMAL(12,2) DEFAULT 0,
    operator_id INTEGER,
    remark TEXT,
    expense_at DATETIME,
    created_at DATETIME NOT NULL
);

CREATE TABLE salary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    month TEXT,
    base_amount DECIMAL(12,2) DEFAULT 0,
    bonus DECIMAL(12,2) DEFAULT 0,
    deduction DECIMAL(12,2) DEFAULT 0,
    net_amount DECIMAL(12,2) DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    operator_id INTEGER,
    paid_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE reconciliation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    supplier_id INTEGER,
    type TEXT NOT NULL,
    period_start DATETIME,
    period_end DATETIME,
    opening_balance DECIMAL(12,2) DEFAULT 0,
    closing_balance DECIMAL(12,2) DEFAULT 0,
    diff DECIMAL(12,2) DEFAULT 0,
    operator_id INTEGER,
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- ----- asset / device -----
CREATE TABLE asset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    customer_id INTEGER,
    purchase_at DATETIME,
    warranty_until DATETIME,
    location TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    remark TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE device (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER,
    customer_id INTEGER,
    serial_no TEXT,
    model TEXT,
    install_at DATETIME,
    warranty_until DATETIME,
    status TEXT NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- ----- office -----
CREATE TABLE office (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,
    config TEXT,  -- JSON
    status INTEGER DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- ----- statistics view helper (SQLite 不支持 view 参数化，跳过) -----

-- ----- JWT blacklist (新增) -----
CREATE TABLE jwt_blacklist (
    jti TEXT PRIMARY KEY,
    revoked_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL
);
CREATE INDEX idx_jwt_blacklist_expires_at ON jwt_blacklist(expires_at);

-- ----- indexes -----
CREATE INDEX idx_workorder_status ON workorder(status);
CREATE INDEX idx_workorder_customer_id ON workorder(customer_id);
CREATE INDEX idx_workorder_technician_id ON workorder(technician_id);
CREATE INDEX idx_workorder_created_at ON workorder(created_at);
CREATE INDEX idx_sales_order_status ON sales_order(status);
CREATE INDEX idx_sales_order_customer_id ON sales_order(customer_id);
CREATE INDEX idx_sales_order_created_at ON sales_order(created_at);
CREATE INDEX idx_purchase_order_status ON purchase_order(status);
CREATE INDEX idx_purchase_order_supplier_id ON purchase_order(supplier_id);
CREATE INDEX idx_purchase_order_created_at ON purchase_order(created_at);
CREATE INDEX idx_product_category_id ON product(category_id);
CREATE INDEX idx_stock_product_id ON stock(product_id);
CREATE INDEX idx_stock_log_product_id ON stock_log(product_id);
CREATE INDEX idx_stock_log_created_at ON stock_log(created_at);
CREATE INDEX idx_operation_log_user_id ON operation_log(user_id);
CREATE INDEX idx_operation_log_created_at ON operation_log(created_at);
CREATE INDEX idx_payment_customer_id ON payment(customer_id);
CREATE INDEX idx_payment_supplier_id ON payment(supplier_id);
CREATE INDEX idx_payment_paid_at ON payment(paid_at);
CREATE INDEX idx_data_audit_log_table_record ON data_audit_log(table_name, record_id);
```

> **⚠️ Schema 完整性说明**：上面是按 `docs/archive/database_complete_v3.sql` 的结构拆解的精简版。如果某个 blueprint 在实际运行时报 `OperationalError: no such table`，回到这个文件补表（仍然遵循 SQLite 语法：AUTOINCREMENT、TEXT、DATETIME、DECIMAL）。

- [ ] **Step 3: 验证 SQLite 语法**

启动临时 SQLite：
```bash
sqlite3 :memory: < backend/database/init.sql
```

Expected: 无错误输出

如果 `sqlite3` 不在 PATH，跳过此步；下一步的 init_db.py 会做完整验证。

- [ ] **Step 4: 提交**

```bash
git add backend/database/init.sql
git commit -m "feat(db): add SQLite init schema with jwt_blacklist table"
```

---

### Task 5: 创建 init_db.py 脚本

**Files:**
- Create: `backend/scripts/init_db.py`

- [ ] **Step 1: 写入脚本**

`backend/scripts/init_db.py`：
```python
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


def _resolve_sqlite_uri() -> str:
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
        print('[init_db] 数据库初始化完成 ✓')
    finally:
        conn.close()


def _seed(conn: sqlite3.Connection):
    """插入默认管理员和角色。"""
    now = datetime.now().isoformat(sep=' ')
    default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', '123456')
    password_hash = bcrypt.hashpw(
        default_password.encode('utf-8'), bcrypt.gensalt()
    ).decode('utf-8')

    # 默认角色
    roles = [
        ('系统管理员', 'admin', '["*"]', '全部权限'),
        ('维修技师', 'technician', '["workorder.*","inventory.read"]', '工单与库存查看'),
        ('财务', 'finance', '["finance.*","report.read"]', '财务模块'),
        ('库管', 'warehouse', '["inventory.*","purchase.read","sales.read"]', '库存与采购'),
    ]
    for name, code, perms, desc in roles:
        conn.execute(
            'INSERT INTO sys_role (name, code, permissions, description, created_at, updated_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (name, code, perms, desc, now, now),
        )

    # 默认管理员用户（关联到 admin 角色）
    admin_role = conn.execute(
        "SELECT id FROM sys_role WHERE code = 'admin'"
    ).fetchone()
    role_id = admin_role[0] if admin_role else None

    conn.execute(
        'INSERT INTO sys_user (username, password_hash, real_name, status, role_id, created_at, updated_at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        ('admin', password_hash, '系统管理员', 1, role_id, now, now),
    )
    print(f'[init_db] 已创建默认管理员: admin / {default_password}')


if __name__ == '__main__':
    init_database()
```

- [ ] **Step 2: 安装 bcrypt（如果还没装）**

```bash
cd backend
pip install bcrypt==4.1.2
```

- [ ] **Step 3: 运行脚本验证**

```bash
cd backend
python scripts/init_db.py
```

Expected output:
```
[init_db] 目标数据库: .../data/repair_system.db
[init_db] 数据库初始化完成 ✓
[init_db] 已创建默认管理员: admin / 123456
```

- [ ] **Step 4: 验证数据库文件存在**

```bash
ls -la data/repair_system.db*
```

Expected: `repair_system.db` 文件存在（可能伴随 `-wal` / `-shm`）

- [ ] **Step 5: 验证表结构**

```bash
sqlite3 data/repair_system.db ".tables"
```

Expected: 列出 `sys_user sys_role jwt_blacklist workorder sales_order product customer ...` 等表

- [ ] **Step 6: 验证种子数据**

```bash
sqlite3 data/repair_system.db "SELECT username, real_name, status FROM sys_user"
sqlite3 data/repair_system.db "SELECT name, code FROM sys_role"
```

Expected:
- sys_user 输出 1 行：admin / 系统管理员 / 1
- sys_role 输出 4 行

- [ ] **Step 7: 提交**

```bash
git add backend/scripts/init_db.py
git commit -m "feat(db): add init_db.py script with seed data"
```

---

## Phase 3: 后端代码改造

### Task 6: 修改 extensions.py — 移除 Redis

**Files:**
- Modify: `backend/extensions.py`

- [ ] **Step 1: 重写整个文件**

`backend/extensions.py`（完整替换）：
```python
"""
扩展实例，单例。在 create_app 中通过 init_app 绑定。

放在 backend/ 根目录（不是 backend/app/）是为了避免与项目根的 app.py
发生命名冲突。同时让 models 子包可以用 `from extensions import db` 直接导入。

2026-06-30: 移除 Redis（已迁移到 SQLite jwt_blacklist 表）。
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_talisman import Talisman

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()
talisman = Talisman()


def init_redis(url: str):  # pragma: no cover
    """保留函数签名以兼容历史 import，但不再创建客户端。

    真实撤销状态保存在 SQLite jwt_blacklist 表。
    """
    import logging
    logging.getLogger(__name__).warning(
        'init_redis() 被调用但已弃用；JWT 黑名单使用 SQLite jwt_blacklist 表。'
    )
    return None
```

- [ ] **Step 2: 验证无残留 redis 引用**

```bash
cd backend
grep -r "redis_client" app/ scripts/ models/ 2>/dev/null | grep -v __pycache__
```

Expected: 仅在 `app/security.py`（下一步要改）和 `__pycache__` 中出现。当前阶段先看到 security.py 还有引用是正常的。

- [ ] **Step 3: 提交**

```bash
git add backend/extensions.py
git commit -m "refactor(extensions): remove redis client (blacklist now in SQLite)"
```

---

### Task 7: 修改 config.py — SQLite 默认 + 移除 MySQL 专属

**Files:**
- Modify: `backend/app/config.py`

- [ ] **Step 1: 用 Edit 替换 Config 类的关键行**

在 `backend/app/config.py` 中：

替换这一段（行 36-48）：
```python
    # 数据库
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    # pymysql 专属参数（sqlite 测试不需要）
    if SQLALCHEMY_DATABASE_URI.startswith('mysql'):
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
            'charset': 'utf8mb4',
            'init_command': "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
        }
```

替换为：
```python
    # 数据库（默认指向 data/repair_system.db；DATABASE_URL 可覆盖）
    _DEFAULT_DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data',
        'repair_system.db',
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{_DEFAULT_DB_PATH}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def _engine_options():
        """按方言返回 engine options。"""
        if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
            return {
                'connect_args': {
                    'timeout': 5,           # busy_timeout (seconds)
                    'check_same_thread': False,
                },
                'pool_pre_ping': True,
            }
        return {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        }
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options()
```

替换这一段（行 49-51）：
```python
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
```

替换为：
```python
    # Redis 已移除（JWT 黑名单改用 SQLite jwt_blacklist 表）
    # 保留 REDIS_URL 配置项以兼容旧 .env；不读取
```

- [ ] **Step 2: 验证修改**

```bash
cd backend
grep -n "SQLALCHEMY_DATABASE_URI\|REDIS_URL\|connect_args" app/config.py
```

Expected: 看到 `SQLALCHEMY_DATABASE_URI = os.environ.get(...)` 和 `connect_args` 在 SQLite 分支，无 `mysql` 字样。

- [ ] **Step 3: 验证配置可加载**

```bash
cd backend
DATABASE_URL="sqlite:///test.db" python -c "from app.config import Config; print(Config.SQLALCHEMY_DATABASE_URI); print(Config.SQLALCHEMY_ENGINE_OPTIONS)"
```

Expected: 打印 sqlite URI 和 connect_args 包含 timeout: 5

清理：
```bash
rm -f test.db
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/config.py
git commit -m "refactor(config): SQLite default URI, remove MySQL-specific options"
```

---

### Task 8: 修改 security.py — JWT 黑名单改 SQLite

**Files:**
- Modify: `backend/app/security.py`

- [ ] **Step 1: 替换头部 import 和 redis 相关代码**

替换 `backend/app/security.py` 顶部 import 段（行 1-11）：
```python
"""
安全相关：JWT 配置、token 黑名单、文件上传白名单。

2026-06-30: JWT 黑名单从 Redis 迁移到 SQLite jwt_blacklist 表。
"""
import os
from datetime import datetime
from uuid import uuid4
from flask import jsonify, g, request

# extensions 在 backend/ 根目录（不在 backend/app/ 下）
from extensions import jwt, db

REVOKED_JTI_KEY = 'jwt:revoked:{}'  # 保留兼容旧 import；新逻辑使用 SQL 表
```

- [ ] **Step 2: 替换 `configure_jwt` 中的 `check_revoked`**

在 `backend/app/security.py` 中：

替换（行 17-25）：
```python
    @jwt_instance.token_in_blocklist_loader
    def check_revoked(_jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        if redis_client is None:
            return False
        try:
            return bool(redis_client.exists(REVOKED_JTI_KEY.format(jti)))
        except Exception:
            return False
```

替换为：
```python
    @jwt_instance.token_in_blocklist_loader
    def check_revoked(_jwt_header, jwt_payload):
        """从 SQLite jwt_blacklist 表查询。"""
        jti = jwt_payload.get('jti')
        if not jti:
            return False
        try:
            row = db.session.execute(
                db.text(
                    'SELECT 1 FROM jwt_blacklist '
                    'WHERE jti = :jti AND expires_at > :now'
                ),
                {'jti': jti, 'now': datetime.now()},
            ).first()
            return row is not None
        except Exception:
            return False
```

- [ ] **Step 3: 替换 `revoke_token`**

替换（行 44-51）：
```python
def revoke_token(jwt_payload: dict):
    """把 jti 加入 redis 黑名单，过期时间与 token TTL 一致。"""
    jti = jwt_payload['jti']
    exp = jwt_payload.get('exp')
    if redis_client is None:
        return
    ttl = max(60, int(exp - __import__('time').time())) if exp else 7 * 24 * 3600
    redis_client.setex(REVOKED_JTI_KEY.format(jti), ttl, '1')
```

替换为：
```python
def revoke_token(jwt_payload: dict):
    """把 jti 写入 SQLite jwt_blacklist；过期由 token exp 决定。"""
    jti = jwt_payload.get('jti')
    exp = jwt_payload.get('exp')
    if not jti:
        return
    expires_at = (
        datetime.fromtimestamp(exp) if exp
        else datetime.now()
    )
    try:
        db.session.execute(
            db.text(
                'INSERT OR IGNORE INTO jwt_blacklist (jti, expires_at) '
                'VALUES (:jti, :exp)'
            ),
            {'jti': jti, 'exp': expires_at},
        )
        db.session.commit()
    except Exception:
        db.session.rollback()


def cleanup_expired_blacklist():
    """清理已过期的黑名单条目（启动时 + 每日调用）。"""
    try:
        db.session.execute(
            db.text('DELETE FROM jwt_blacklist WHERE expires_at < :now'),
            {'now': datetime.now()},
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
```

- [ ] **Step 4: 验证文件无残留 redis**

```bash
cd backend
grep -n "redis_client" app/security.py
```

Expected: 无输出（之前的 redis_client 引用已被全部替换）

- [ ] **Step 5: 提交**

```bash
git add backend/app/security.py
git commit -m "refactor(security): JWT blacklist moved from Redis to SQLite"
```

---

### Task 9: 创建 utils/db_retry.py

**Files:**
- Create: `backend/app/utils/db_retry.py`

- [ ] **Step 1: 写入装饰器**

`backend/app/utils/db_retry.py`：
```python
"""
SQLite 写入重试装饰器：捕获 'database is locked'，自动重试。

适用场景：workorder 创建、库存变更、财务写入（spec §8）。
"""
import time
import functools
import logging

from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


def retry_on_lock(max_retries: int = 3, delay: float = 0.5):
    """装饰器：捕获 SQLite 'database is locked' 错误并重试。

    Args:
        max_retries: 最大重试次数（含首次）
        delay: 重试间隔（秒）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    msg = str(e).lower()
                    if 'locked' not in msg or i == max_retries - 1:
                        raise
                    last_err = e
                    logger.warning(
                        'SQLite locked on %s, retry %d/%d',
                        func.__name__, i + 1, max_retries,
                    )
                    time.sleep(delay)
            if last_err:
                raise last_err
        return wrapper
    return decorator
```

- [ ] **Step 2: 验证导入**

```bash
cd backend
python -c "from app.utils.db_retry import retry_on_lock; print(retry_on_lock)"
```

Expected: 打印函数对象（无 ImportError）

- [ ] **Step 3: 提交**

```bash
git add backend/app/utils/db_retry.py
git commit -m "feat(utils): add retry_on_lock decorator for SQLite writes"
```

---

### Task 10: 创建 models/_base.py — TimestampMixin

**Files:**
- Create: `backend/models/_base.py`

- [ ] **Step 1: 写入 mixin**

`backend/models/_base.py`：
```python
"""
SQLAlchemy 通用 mixin。

2026-06-30: 替代 MySQL 的 `ON UPDATE CURRENT_TIMESTAMP`（spec §4）。
SQLAlchemy 的 onupdate 钩子在 app 层运行，SQLite 兼容。
"""
from datetime import datetime

from extensions import db


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
```

- [ ] **Step 2: 验证导入**

```bash
cd backend
python -c "from models._base import TimestampMixin; print(TimestampMixin)"
```

Expected: 打印类对象

- [ ] **Step 3: 提交**

```bash
git add backend/models/_base.py
git commit -m "feat(models): add TimestampMixin to replace MySQL ON UPDATE CURRENT_TIMESTAMP"
```

---

### Task 11: 修改 app/__init__.py — 移除 init_redis 调用

**Files:**
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: 用 Edit 删除 init_redis 行**

在 `backend/app/__init__.py` 中：

替换（行 48-50）：
```python
    # Redis 初始化（token 黑名单等依赖）
    from extensions import init_redis
    init_redis(app.config['REDIS_URL'])
```

替换为：
```python
    # JWT 黑名单使用 SQLite jwt_blacklist 表（无需 Redis）
```

- [ ] **Step 2: 同时清理 startup 中的过期黑名单**

在 `backend/app/__init__.py` 中：

替换：
```python
    # 初始化种子（仅空库时）
    with app.app_context():
        from .seed import run_seeds_if_empty
        run_seeds_if_empty()
```

替换为：
```python
    # 启动时清理过期 JWT 黑名单
    with app.app_context():
        from .security import cleanup_expired_blacklist
        cleanup_expired_blacklist()

    # 初始化种子（仅空库时）
    with app.app_context():
        from .seed import run_seeds_if_empty
        run_seeds_if_empty()
```

- [ ] **Step 3: 验证应用工厂可加载**

```bash
cd backend
JWT_SECRET_KEY=test DATABASE_URL="sqlite:///test.db" python -c "from app import create_app; app = create_app('testing'); print('app created OK')"
```

Expected: `app created OK`

清理：
```bash
rm -f test.db
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/__init__.py
git commit -m "refactor(app): remove init_redis, add blacklist cleanup on startup"
```

---

### Task 12: 修改 requirements.txt — 移除 PyMySQL 和 redis

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 移除两行**

打开 `backend/requirements.txt`，删除以下两行：
```
PyMySQL==1.1.0
redis==5.0.1
```

- [ ] **Step 2: 验证最终内容**

```bash
cat backend/requirements.txt
```

Expected: 14 行（少了 PyMySQL 和 redis），其余不变。

- [ ] **Step 3: 提交**

```bash
git add backend/requirements.txt
git commit -m "chore(deps): remove PyMySQL and redis from requirements"
```

---

## Phase 4: 启动 / 打包脚本

### Task 13: 创建 start_dev.py（跨平台进程管理）

**Files:**
- Create: `backend/scripts/start_dev.py`

- [ ] **Step 1: 写入脚本**

`backend/scripts/start_dev.py`：
```python
"""
开发模式进程管理器：同时启动 Flask（5000）和 Vite（5173）。
通过 PID 文件管理两个进程；任一进程崩溃则全部退出。

用法：
    python scripts/start_dev.py
"""
import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
_PROJECT_ROOT = _BACKEND.parent
_FRONTEND = _PROJECT_ROOT / 'frontend'

PID_DIR = _PROJECT_ROOT / 'data' / '.pids'
LOG_DIR = _PROJECT_ROOT / 'data' / 'logs'
FLASK_PID = PID_DIR / 'flask.pid'
VITE_PID = PID_DIR / 'vite.pid'
FLASK_LOG = LOG_DIR / 'flask.log'
VITE_LOG = LOG_DIR / 'vite.log'


def _ensure_dirs():
    PID_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == 'nt':
            # Windows: 用 tasklist 验证
            out = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True, text=True,
            ).stdout
            return str(pid) in out
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def _read_pid(path: Path) -> int:
    try:
        return int(path.read_text().strip())
    except Exception:
        return 0


def _spawn(cmd, cwd, log_path, env):
    """启动子进程，stdout/stderr 重定向到日志，返回 Popen。"""
    log_f = open(log_path, 'a', encoding='utf-8')
    log_f.write(f'\n===== start at {datetime.now().isoformat()} =====\n')
    log_f.flush()
    proc = subprocess.Popen(
        cmd, cwd=str(cwd), env=env,
        stdout=log_f, stderr=subprocess.STDOUT,
    )
    return proc


def main():
    _ensure_dirs()

    # 检查现有进程
    for name, pid_file in [('flask', FLASK_PID), ('vite', VITE_PID)]:
        old = _read_pid(pid_file)
        if old and _is_alive(old):
            print(f'[start_dev] {name} (pid={old}) 已在运行，先停止')
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(old)],
                               capture_output=True)
            else:
                os.kill(old, signal.SIGTERM)
            time.sleep(1)
        if pid_file.exists():
            pid_file.unlink()

    # 构造环境
    env = os.environ.copy()
    env.setdefault('FLASK_ENV', 'development')
    # 继承 DATABASE_URL（如果 .env 已加载）

    flask_cmd = [sys.executable, str(_BACKEND / 'run.py')]
    vite_cmd = ['npm', 'run', 'dev']
    if os.name == 'nt':
        # npm 在 Windows 上是 npm.cmd
        vite_cmd[0] = 'npm.cmd'

    print('[start_dev] 启动 Flask :5000 ...')
    flask_proc = _spawn(flask_cmd, _BACKEND, FLASK_LOG, env)
    FLASK_PID.write_text(str(flask_proc.pid))

    print('[start_dev] 启动 Vite :5173 ...')
    vite_proc = _spawn(vite_cmd, _FRONTEND, VITE_LOG, env)
    VITE_PID.write_text(str(vite_proc.pid))

    print('[start_dev] Flask 日志:', FLASK_LOG)
    print('[start_dev] Vite  日志:', VITE_LOG)
    print('[start_dev] 浏览器打开 http://localhost:5173  (Ctrl+C 退出)')

    def cleanup(*_):
        print('\n[start_dev] 正在停止子进程 ...')
        for proc, name in [(flask_proc, 'flask'), (vite_proc, 'vite')]:
            try:
                if os.name == 'nt':
                    subprocess.run(
                        ['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                        capture_output=True,
                    )
                else:
                    proc.terminate()
                    proc.wait(timeout=3)
            except Exception:
                pass
        for p in (FLASK_PID, VITE_PID):
            try:
                p.unlink()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, cleanup)

    # 主循环：任一进程死亡就退出
    try:
        while True:
            time.sleep(2)
            if flask_proc.poll() is not None:
                print('[start_dev] Flask 进程退出，停止所有服务')
                cleanup()
            if vite_proc.poll() is not None:
                print('[start_dev] Vite 进程退出，停止所有服务')
                cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 验证语法**

```bash
cd backend
python -c "import ast; ast.parse(open('scripts/start_dev.py').read()); print('syntax OK')"
```

Expected: `syntax OK`

- [ ] **Step 3: 提交**

```bash
git add backend/scripts/start_dev.py
git commit -m "feat(scripts): add start_dev.py with PID-based process management"
```

---

### Task 14: 创建 start.bat / start.sh（开发模式入口）

**Files:**
- Create: `start.bat`
- Create: `start.sh`

- [ ] **Step 1: 写入 start.bat**

`start.bat`：
```batch
@echo off
REM ============================================================
REM Repair System - 开发模式启动脚本 (Windows)
REM ============================================================
setlocal

echo [start] 检查 Python ...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未检测到 Python，请先安装 Python 3.11+: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 第一次启动：复制 .env.example
if not exist .env (
    echo [start] 复制 .env.example 为 .env
    copy .env.example .env >nul
)

REM 第一次启动：创建虚拟环境
if not exist backend\.venv (
    echo [start] 创建 Python 虚拟环境 backend\.venv
    cd backend
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)

REM 第一次启动：初始化数据库
if not exist data\repair_system.db (
    echo [start] 初始化 SQLite 数据库
    cd backend
    call .venv\Scripts\activate.bat
    python scripts\init_db.py
    cd ..
)

REM 第一次启动：安装前端依赖
if not exist frontend\node_modules (
    echo [start] 安装前端依赖（首次较慢）
    cd frontend
    call npm install
    cd ..
)

REM 启动开发服务
echo [start] 启动 Flask + Vite ...
cd backend
call .venv\Scripts\activate.bat
python scripts\start_dev.py
cd ..

endlocal
```

- [ ] **Step 2: 写入 start.sh**

`start.sh`：
```bash
#!/usr/bin/env bash
# ============================================================
# Repair System - 开发模式启动脚本 (Linux/macOS)
# ============================================================
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[start] 检查 Python ..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] 未检测到 python3，请先安装 Python 3.11+"
    exit 1
fi

# 第一次启动：复制 .env.example
if [ ! -f .env ]; then
    echo "[start] 复制 .env.example 为 .env"
    cp .env.example .env
fi

# 第一次启动：创建虚拟环境
if [ ! -d backend/.venv ]; then
    echo "[start] 创建 Python 虚拟环境 backend/.venv"
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# 第一次启动：初始化数据库
if [ ! -f data/repair_system.db ]; then
    echo "[start] 初始化 SQLite 数据库"
    cd backend
    source .venv/bin/activate
    python scripts/init_db.py
    cd ..
fi

# 第一次启动：安装前端依赖
if [ ! -d frontend/node_modules ]; then
    echo "[start] 安装前端依赖（首次较慢）"
    cd frontend
    npm install
    cd ..
fi

# 启动开发服务
echo "[start] 启动 Flask + Vite ..."
cd backend
source .venv/bin/activate
python scripts/start_dev.py
```

- [ ] **Step 3: 设置 start.sh 可执行**

```bash
git update-index --chmod=+x start.sh
```

- [ ] **Step 4: 提交**

```bash
git add start.bat start.sh
git commit -m "feat(scripts): add start.bat/start.sh for dev mode entry"
```

---

### Task 15: 创建 stop.bat / stop.sh

**Files:**
- Create: `stop.bat`
- Create: `stop.sh`

- [ ] **Step 1: 写入 stop.bat**

`stop.bat`：
```batch
@echo off
REM ============================================================
REM Repair System - 停止开发服务 (Windows)
REM ============================================================
setlocal

set PID_DIR=data\.pids

if not exist %PID_DIR%\flask.pid (
    echo [stop] 没有运行的 Flask 进程
    goto :check_vite
)
set /p FLASK_PID=<%PID_DIR%\flask.pid
echo [stop] 停止 Flask (pid=%FLASK_PID%)
taskkill /F /T /PID %FLASK_PID% >nul 2>&1
del %PID_DIR%\flask.pid

:check_vite
if not exist %PID_DIR%\vite.pid (
    echo [stop] 没有运行的 Vite 进程
    goto :done
)
set /p VITE_PID=<%PID_DIR%\vite.pid
echo [stop] 停止 Vite (pid=%VITE_PID%)
taskkill /F /T /PID %VITE_PID% >nul 2>&1
del %PID_DIR%\vite.pid

:done
echo [stop] 完成
endlocal
```

- [ ] **Step 2: 写入 stop.sh**

`stop.sh`：
```bash
#!/usr/bin/env bash
# ============================================================
# Repair System - 停止开发服务 (Linux/macOS)
# ============================================================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PID_DIR="data/.pids"

kill_pid() {
    local name="$1"
    local pid_file="$PID_DIR/$1.pid"
    if [ ! -f "$pid_file" ]; then
        echo "[stop] 没有运行的 $name 进程"
        return
    fi
    local pid=$(cat "$pid_file")
    echo "[stop] 停止 $name (pid=$pid)"
    kill -TERM "$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    rm -f "$pid_file"
}

kill_pid flask
kill_pid vite
echo "[stop] 完成"
```

- [ ] **Step 3: 设置 stop.sh 可执行**

```bash
git update-index --chmod=+x stop.sh
```

- [ ] **Step 4: 提交**

```bash
git add stop.bat stop.sh
git commit -m "feat(scripts): add stop.bat/stop.sh to terminate dev services"
```

---

### Task 16: 创建 start_prod.bat / start_prod.sh

**Files:**
- Create: `start_prod.bat`
- Create: `start_prod.sh`

- [ ] **Step 1: 写入 start_prod.bat**

`start_prod.bat`：
```batch
@echo off
REM ============================================================
REM Repair System - 生产模式启动 (Windows): gunicorn 不直接用，
REM 直接用 waitress（更跨平台）。先检测 waitress。
REM ============================================================
setlocal

if not exist .env (
    echo [start_prod] 复制 .env.example 为 .env
    copy .env.example .env >nul
)
if not exist backend\.venv (
    echo [start_prod] 创建虚拟环境
    cd backend
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)
if not exist data\repair_system.db (
    echo [start_prod] 初始化数据库
    cd backend
    call .venv\Scripts\activate.bat
    python scripts\init_db.py
    cd ..
)

if not exist frontend\dist\index.html (
    echo [start_prod] 构建前端
    cd frontend
    call npm install
    call npm run build
    cd ..
)

echo [start_prod] 启动 Flask（生产模式）...
cd backend
call .venv\Scripts\activate.bat
set FLASK_ENV=production
python run.py

endlocal
```

- [ ] **Step 2: 写入 start_prod.sh**

`start_prod.sh`：
```bash
#!/usr/bin/env bash
# ============================================================
# Repair System - 生产模式启动 (Linux/macOS): gunicorn
# ============================================================
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then cp .env.example .env; fi
if [ ! -d backend/.venv ]; then
    cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cd ..
fi
if [ ! -f data/repair_system.db ]; then
    cd backend && source .venv/bin/activate && python scripts/init_db.py && cd ..
fi
if [ ! -f frontend/dist/index.html ]; then
    cd frontend && npm install && npm run build && cd ..
fi

echo "[start_prod] 启动 gunicorn ..."
cd backend
source .venv/bin/activate
FLASK_ENV=production exec gunicorn -w 2 -b 0.0.0.0:5000 run:app
```

- [ ] **Step 3: 设置 start_prod.sh 可执行**

```bash
git update-index --chmod=+x start_prod.sh
```

- [ ] **Step 4: 提交**

```bash
git add start_prod.bat start_prod.sh
git commit -m "feat(scripts): add production-mode start scripts"
```

---

### Task 17: 创建 build_portable.bat

**Files:**
- Create: `build_portable.bat`

> 放在项目根。此脚本**不进 zip**，仅在开发机器运行。

- [ ] **Step 1: 写入脚本**

`build_portable.bat`：
```batch
@echo off
REM ============================================================
REM Repair System - 便携包构建脚本（仅开发机器运行，不进 zip）
REM 用法: build_portable.bat 2026.06.30
REM ============================================================
set VERSION=%1
if "%VERSION%"=="" (
    echo [ERROR] 用法: build_portable.bat ^<version^>
    echo 示例:   build_portable.bat 2026.06.30
    exit /b 1
)

echo [build] 清理临时文件 ...
for /d /r backend %%d in (__pycache__) do @rd /s /q "%%d" 2>nul
for /d /r frontend %%d in (node_modules) do @rd /s /q "%%d" 2>nul
for /d /r frontend %%d in (dist) do @rd /s /q "%%d" 2>nul
if exist backend\.venv rd /s /q backend\.venv

echo [build] 构建前端生产包 ...
cd frontend
call npm install
call npm run build
cd ..

echo [build] 写入 VERSION.txt ...
echo %VERSION%> VERSION.txt

echo [build] 打包 zip ...
powershell -Command "Compress-Archive -Path backend,frontend,data,docs,start.bat,start.sh,start_prod.bat,start_prod.sh,stop.bat,stop.sh,.env.example,.gitignore,README.md,VERSION.txt -DestinationPath repair-system-portable-v%VERSION%.zip -Force"

echo [build] 完成: repair-system-portable-v%VERSION%.zip
```

- [ ] **Step 2: 提交**

```bash
git add build_portable.bat
git commit -m "feat(scripts): add build_portable.bat for portable zip packaging"
```

---

## Phase 5: 配置与文档

### Task 18: 创建根 .env.example

**Files:**
- Create: `.env.example`

- [ ] **Step 1: 写入文件**

`.env.example`：
```ini
# Repair System - 默认开发配置（拷贝为 .env 后可修改）
# ============================================================

# Flask 运行环境：development / production / testing
FLASK_ENV=development

# JWT 密钥（生产环境必须修改为长随机字符串）
JWT_SECRET_KEY=RepairSystemSecretKey2024

# SQLite 数据库路径（默认指向 data/repair_system.db；可用绝对路径覆盖）
DATABASE_URL=sqlite:///data/repair_system.db

# 上传文件目录（绝对路径）
UPLOAD_FOLDER=data/uploads

# 上传文件大小上限（MB）
MAX_CONTENT_LENGTH_MB=16

# CORS 允许的来源（逗号分隔；开发用 localhost:5173）
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Cookie 安全（生产 HTTPS 设为 true）
SESSION_COOKIE_SECURE=false

# Talisman 安全头（生产设为 true）
TALISMAN_ENABLED=false

# Setup 端点开关（首次部署后可设为 false）
SETUP_ENABLED=true

# 默认管理员密码（init_db 时使用）
DEFAULT_ADMIN_PASSWORD=123456
```

- [ ] **Step 2: 提交**

```bash
git add .env.example
git commit -m "feat(config): add root .env.example with sensible defaults"
```

---

### Task 19: 修改 .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: 追加新条目（保留原有内容）**

打开 `.gitignore`，在末尾追加：

```
# Python
backend/.venv/
__pycache__/
*.py[cod]
*.egg-info/

# Frontend
frontend/node_modules/
frontend/dist/

# 数据 / 日志 / PID（运行时生成，不入库）
data/*.db
data/*.db-wal
data/*.db-shm
data/uploads/*
!data/uploads/.gitkeep
data/logs/*
!data/logs/.gitkeep
data/.pids/*
!data/.pids/.gitkeep

# 环境变量
.env

# IDE
.vscode/
.idea/
*.swp

# 系统
.DS_Store
Thumbs.db

# 便携包产物
repair-system-portable-*.zip
```

- [ ] **Step 2: 验证结构**

```bash
cat .gitignore | head -30
```

Expected: 看到 `backend/.venv/` 和 `data/*.db` 等条目

- [ ] **Step 3: 提交**

```bash
git add .gitignore
git commit -m "chore(gitignore): exclude data/, venv, node_modules, portable zips"
```

---

### Task 20: 重写 README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 用 Write 整体替换 README.md**

`README.md`：
```markdown
# 维修商贸一体化管理系统（便携版）

## 系统概述

维修商贸一体化管理系统的便携部署版本。**无需 Docker、无需 MySQL、无需 Redis**，解压即用，数据存本地 SQLite 文件。

适用于：
- 单店 / 小团队（≤ 5 并发用户）
- 跨电脑迁移（zip → 解压 → 启动）
- 离线 / 内网环境

## 技术栈

### 前端
- Vue 3.2.47 + Vite 4.4.9 + Element Plus 2.2.28

### 后端
- Python 3.11 + Flask 2.3.3 + Flask-SQLAlchemy 3.0.5 + Flask-JWT-Extended 4.5.2

### 数据
- SQLite（Python 内置，单文件）
- 本地文件系统（上传文件）

## 快速开始

### Windows

1. 安装 Python 3.11+：<https://www.python.org/downloads/>
2. 解压项目到任意目录
3. 双击 `start.bat`
4. 浏览器打开 <http://localhost:5173>
5. 默认账号：`admin` / `123456`

### Linux / macOS

```bash
chmod +x start.sh stop.sh
./start.sh
```

首次启动会自动：
- 复制 `.env.example` → `.env`
- 创建 `backend/.venv/` 并安装依赖
- 执行 `backend/scripts/init_db.py` 建库 + 种子数据
- 安装 `frontend/node_modules/`
- 启动 Flask（5000）+ Vite（5173）

## 目录结构

```
repair-system/
├── backend/                    # 后端代码
│   ├── app/                    # 工厂 + blueprints + services + utils
│   ├── models/                 # SQLAlchemy 模型
│   ├── database/init.sql       # SQLite schema
│   ├── scripts/                # init_db / start_dev
│   ├── tests/
│   └── requirements.txt
├── frontend/                   # 前端代码（dist/ 预构建在 zip 中）
├── data/                       # ★ 运行时数据（备份这个目录就够了）
│   ├── repair_system.db        # SQLite 主库
│   ├── uploads/                # 上传文件
│   ├── logs/                   # flask.log / vite.log
│   └── .pids/                  # flask.pid / vite.pid
├── docs/
│   ├── superpowers/specs/
│   ├── superpowers/plans/
│   └── archive/                # 旧 MySQL schema + docker 文件（参考用）
├── start.bat / start.sh        # 开发模式入口
├── start_prod.bat / start_prod.sh  # 生产模式入口
├── stop.bat / stop.sh          # 停止服务
├── .env.example
├── .gitignore
├── README.md
└── VERSION.txt
```

## 数据备份

```bash
# 1. 停止服务
stop.bat   # 或 ./stop.sh

# 2. 备份整个 data/ 目录
xcopy /E data\ data_backup_20260630\
# 或 Linux：cp -r data/ data_backup_20260630/

# 3. 重启
start.bat
```

仅备份 `data/repair_system.db*` 三个文件即可完整恢复业务数据。

## 跨电脑迁移

在源机器上：
```cmd
build_portable.bat 2026.06.30
```
产出 `repair-system-portable-v2026.06.30.zip`（含预构建的 `frontend/dist/`）。

在目标机器上：
1. 安装 Python 3.11+
2. 解压 zip
3. **如果需要带上旧数据**：把旧机器的 `data/repair_system.db*` 覆盖到解压目录的 `data/`
4. 双击 `start.bat` → 自动检测 `data/repair_system.db` 已存在，跳过初始化

## 生产模式

- Windows：`start_prod.bat`（用 waitress / flask run）
- Linux：`./start_prod.sh`（用 gunicorn -w 2）
- 前端使用 `frontend/dist/` 预构建静态文件（不是 dev server）

## 限制

- SQLite 串行化写：≤ 5 并发用户适用
- 没有全文搜索（`LIKE '%xxx%'` 仍可用）
- 没有对象存储（上传文件走本地 `data/uploads/`）

## 故障排查

| 问题 | 解决 |
|------|------|
| `python: command not found` | 安装 Python 3.11+ 并加入 PATH |
| `OperationalError: database is locked` | 关闭其他连接，或删除 `data/.pids/*.pid` 后重启 |
| 前端 404 | 检查 `frontend/dist/` 是否存在；缺失则 `cd frontend && npm run build` |
| 端口 5000/5173 占用 | 改 `start_dev.py` 中的端口，或 `netstat` / `lsof` 找到占用进程 |

## 技术支持

查看日志：
- `data/logs/flask.log`
- `data/logs/vite.log`

## 许可证

本项目仅供学习和内部使用。
```

- [ ] **Step 2: 验证渲染**

```bash
head -30 README.md
```

Expected: 看到「便携版」「数据存本地 SQLite 文件」字样

- [ ] **Step 3: 提交**

```bash
git add README.md
git commit -m "docs: rewrite README for portable SQLite deployment"
```

---

### Task 21: 创建 VERSION.txt

**Files:**
- Create: `VERSION.txt`

- [ ] **Step 1: 写入版本号**

```bash
echo "2026.06.30" > VERSION.txt
```

- [ ] **Step 2: 提交**

```bash
git add VERSION.txt
git commit -m "chore: add VERSION.txt"
```

---

## Phase 6: 测试

### Task 22: 验证 conftest.py 与跑测试套件

**Files:**
- Verify (no modify): `backend/tests/conftest.py`

> `conftest.py` 已经在之前的 read 中确认设置 `DATABASE_URL=sqlite:///:memory:`，无需修改。

- [ ] **Step 1: 安装 dev 依赖**

```bash
cd backend
pip install pytest==7.4.0
```

- [ ] **Step 2: 跑 smoke 测试**

```bash
cd backend
pytest tests/test_smoke.py -v
```

Expected: 全部 PASS（即使慢也是 PASS），或部分因数据库连接失败 —— 记录实际输出。

- [ ] **Step 3: 跑 utils 测试**

```bash
cd backend
pytest tests/test_utils.py -v
```

Expected: 全部 PASS

- [ ] **Step 4: 跑 blueprints 测试**

```bash
cd backend
pytest tests/test_blueprints.py -v
```

Expected: 大部分 PASS；个别 blueprint 可能因为表未建而失败（回到 Task 4 补 init.sql）

- [ ] **Step 5: 跑完整套件**

```bash
cd backend
pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_output.txt
```

记录实际 pass/fail 数；如果有失败，根据 traceback 回到对应任务修复。

- [ ] **Step 6: 提交测试状态（如果修改了 init.sql）**

如果上一步为了修复测试而修改了 `backend/database/init.sql`：
```bash
git add backend/database/init.sql
git commit -m "fix(db):补齐测试中发现的缺失表"
```

否则跳过此步。

---

### Task 23: 端到端冒烟测试（手工）

- [ ] **Step 1: 启动开发服务**

```bash
start.bat
```

Expected:
- 自动复制 `.env`
- 自动创建 venv + pip install
- 自动 `init_db.py` 提示创建 admin / 123456
- 自动 `npm install`
- 启动 Flask + Vite，看到 `[start_dev] Flask 日志: .../flask.log`

- [ ] **Step 2: 验证前端可访问**

浏览器打开 <http://localhost:5173>

Expected: 看到登录页

- [ ] **Step 3: 用 admin / 123456 登录**

Expected: 登录成功，跳到主页

- [ ] **Step 4: 创建一个商品**

Expected: 商品创建成功，库存列表可见

- [ ] **Step 5: 停止服务**

```bash
stop.bat
```

Expected: `[stop] 停止 Flask (pid=...)` `[stop] 停止 Vite (pid=...)` `[stop] 完成`

- [ ] **Step 6: 验证数据持久化**

```bash
ls data/repair_system.db*
sqlite3 data/repair_system.db "SELECT COUNT(*) FROM product"
```

Expected: `1`（上一步创建的商品仍在）

---

## Phase 7: 清理

### Task 24: 删除根 app.py shim

**Files:**
- Delete: `app.py`（根目录）

- [ ] **Step 1: 验证不再被引用**

```bash
grep -rn "from app import\|import app\b" --include="*.py" --include="*.md" --include="*.bat" --include="*.sh" --include="*.yml" 2>/dev/null | grep -v node_modules | grep -v __pycache__
```

Expected: 只看到 `from app import create_app`（这是 backend/app 的内部导入，OK）和 `app.py` 自身。除此之外应无 `from app import app` 或 `python app.py`。

- [ ] **Step 2: 删除 app.py**

```bash
git rm app.py
```

- [ ] **Step 3: 提交**

```bash
git commit -m "chore: remove root app.py shim (replaced by backend/run.py)"
```

---

### Task 25: 设置 archive 清理提醒（后置）

> 这是**未来任务**，不立刻执行。在 2 周后做：
- 删除 `docs/archive/docker-configs/`
- 删除 `docs/archive/database_complete_v3.sql`
- 删除 `.env.example` 中的 `DATABASE_URL` 默认值中的 `data/` 路径（让用户强制设置）

创建提醒：在 README.md 顶部或本任务末尾加 TODO 注释。

- [ ] **Step 1: 在 README 加清理提醒**

打开 `README.md`，在「故障排查」章节后追加：

```markdown
## 归档清理（2026-07-14 后执行）

两个过渡性目录将在 2 周后删除：
- `docs/archive/docker-configs/` —— 旧 docker 文件
- `docs/archive/database_complete_v3.sql` —— MySQL 原版 schema（参考用）

届时会再发一个 commit 完成清理。
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: schedule archive cleanup for 2026-07-14"
```

---

## 完成清单

完成所有 25 个任务后，项目应该能够：

1. ✅ 在干净 Windows 机器上：装 Python 3.11+ → 解压 → 双击 `start.bat` → 浏览器登录 → 跑通业务
2. ✅ 数据库是单文件 `data/repair_system.db`，可备份、可整目录迁移
3. ✅ JWT 黑名单存 SQLite，重启不丢
4. ✅ 无 docker、无 MySQL、无 Redis
5. ✅ `build_portable.bat` 产出可分发的 zip
6. ✅ 现有 27 个 blueprint 测试通过（或已修复缺失表）
7. ✅ 旧 docker 文件暂存在 archive，2 周后清理