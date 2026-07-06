"""
SQLite 数据库初始化脚本。
- 读取 backend/database/init.sql 并执行
- 插入种子数据（权限目录 + 默认角色 + 默认用户）

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


# ============================================================
# 权限目录（与 frontend MainLayout.vue menuPermissionMap 对齐）
# type: 1=菜单 2=按钮；parent_id 全部置 0（前端不消费 menus 字段）
# ============================================================
PERMISSIONS = [
    # --- 首页 ---
    ('首页', 'dashboard:view', 1, '/dashboard', 'HomeFilled', 10),

    # --- 前台管理 ---
    ('工单管理', 'workorder:view', 1, '/workorder', 'Tools', 20),
    ('工单-新增', 'workorder:add', 2, None, None, 0),
    ('工单-编辑', 'workorder:edit', 2, None, None, 0),
    ('工单-删除', 'workorder:delete', 2, None, None, 0),
    ('工单-导出', 'workorder:export', 2, None, None, 0),

    ('接件管理', 'receive:view', 1, '/receive', 'Document', 21),
    ('接件-新增', 'receive:add', 2, None, None, 0),
    ('接件-编辑', 'receive:edit', 2, None, None, 0),
    ('接件-删除', 'receive:delete', 2, None, None, 0),

    ('派单管理', 'dispatch:view', 1, '/dispatch', 'Van', 22),
    ('派单-编辑', 'dispatch:edit', 2, None, None, 0),

    ('报价管理', 'quote:view', 1, '/quote', 'Tickets', 23),
    ('报价-新增', 'quote:add', 2, None, None, 0),
    ('报价-编辑', 'quote:edit', 2, None, None, 0),
    ('报价-删除', 'quote:delete', 2, None, None, 0),

    ('资产管理', 'asset:view', 1, '/asset', 'Box', 24),
    ('资产-新增', 'asset:add', 2, None, None, 0),
    ('资产-编辑', 'asset:edit', 2, None, None, 0),
    ('资产-删除', 'asset:delete', 2, None, None, 0),

    # --- 物资管理 ---
    ('商品管理', 'product:view', 1, '/product', 'GoodsFilled', 30),
    ('商品-新增', 'product:add', 2, None, None, 0),
    ('商品-编辑', 'product:edit', 2, None, None, 0),
    ('商品-删除', 'product:delete', 2, None, None, 0),

    ('销售管理', 'sales:view', 1, '/sales', 'Sell', 31),
    ('销售-新增', 'sales:add', 2, None, None, 0),
    ('销售-编辑', 'sales:edit', 2, None, None, 0),
    ('销售-删除', 'sales:delete', 2, None, None, 0),

    ('销售预订', 'preorder-sale:view', 1, '/preorder/sale', 'Notebook', 32),
    ('销售预订-新增', 'preorder-sale:add', 2, None, None, 0),
    ('销售预订-编辑', 'preorder-sale:edit', 2, None, None, 0),

    # --- 采购相关 ---
    ('采购管理', 'purchase:view', 1, '/purchase', 'ShoppingCart', 33),
    ('采购-新增', 'purchase:add', 2, None, None, 0),
    ('采购-编辑', 'purchase:edit', 2, None, None, 0),
    ('采购-删除', 'purchase:delete', 2, None, None, 0),

    ('采购预订', 'preorder:view', 1, '/preorder', 'Notebook', 34),
    ('采购预订-新增', 'preorder:add', 2, None, None, 0),
    ('采购预订-编辑', 'preorder:edit', 2, None, None, 0),

    ('采购退货', 'purchase-return:view', 1, '/return', 'RefreshLeft', 35),
    ('采购退货-新增', 'purchase-return:add', 2, None, None, 0),
    ('采购退货-编辑', 'purchase-return:edit', 2, None, None, 0),

    ('销售退货', 'sales-return:view', 1, '/return/sale', 'RefreshLeft', 36),
    ('销售退货-新增', 'sales-return:add', 2, None, None, 0),
    ('销售退货-编辑', 'sales-return:edit', 2, None, None, 0),

    # --- 库房管理 ---
    ('库存查询', 'inventory:view', 1, '/inventory', 'Box', 40),
    ('入库管理', 'inventory-in:view', 1, '/inventory/in', 'Download', 41),
    ('入库-新增', 'inventory-in:add', 2, None, None, 0),
    ('入库-编辑', 'inventory-in:edit', 2, None, None, 0),
    ('出库管理', 'inventory-out:view', 1, '/inventory/out', 'Upload', 42),
    ('出库-新增', 'inventory-out:add', 2, None, None, 0),
    ('出库-编辑', 'inventory-out:edit', 2, None, None, 0),
    ('库存盘点', 'inventory-check:view', 1, '/inventory/check', 'Box', 43),
    ('盘点-新增', 'inventory-check:add', 2, None, None, 0),
    ('盘点-编辑', 'inventory-check:edit', 2, None, None, 0),
    ('仓库管理', 'warehouse:view', 1, '/warehouse', 'OfficeBuilding', 44),
    ('仓库-新增', 'warehouse:add', 2, None, None, 0),
    ('仓库-编辑', 'warehouse:edit', 2, None, None, 0),
    ('库存变动明细', 'inventory-log:view', 1, '/inventory/logs', 'List', 45),
    ('调拨管理', 'transfer:view', 1, '/inventory/transfer', 'Sort', 46),
    ('调拨-新增', 'transfer:add', 2, None, None, 0),
    ('调拨-编辑', 'transfer:edit', 2, None, None, 0),
    ('成本调价', 'cost-adjust:view', 1, '/inventory/cost-adjust', 'Money', 47),
    ('调价-新增', 'cost-adjust:add', 2, None, None, 0),
    ('调价-编辑', 'cost-adjust:edit', 2, None, None, 0),

    # --- 合作方 ---
    ('客户管理', 'customer:view', 1, '/customer', 'UserFilled', 50),
    ('客户-新增', 'customer:add', 2, None, None, 0),
    ('客户-编辑', 'customer:edit', 2, None, None, 0),
    ('客户-删除', 'customer:delete', 2, None, None, 0),

    ('供应商管理', 'supplier:view', 1, '/supplier', 'OfficeBuilding', 51),
    ('供应商-新增', 'supplier:add', 2, None, None, 0),
    ('供应商-编辑', 'supplier:edit', 2, None, None, 0),
    ('供应商-删除', 'supplier:delete', 2, None, None, 0),

    # --- 财务 ---
    ('财务管理', 'finance:view', 1, '/finance', 'Money', 60),
    ('应收管理', 'finance-receivable:view', 1, '/finance/receivables', 'Wallet', 61),
    ('应收-编辑', 'finance-receivable:edit', 2, None, None, 0),
    ('应付管理', 'finance-payable:view', 1, '/finance/payables', 'CreditCard', 62),
    ('应付-编辑', 'finance-payable:edit', 2, None, None, 0),
    ('收款管理', 'finance-receipt:view', 1, '/finance/receipt', 'Money', 63),
    ('收款-编辑', 'finance-receipt:edit', 2, None, None, 0),
    ('付款管理', 'finance-payment:view', 1, '/finance/payment', 'Money', 64),
    ('付款-编辑', 'finance-payment:edit', 2, None, None, 0),
    ('工资发放', 'finance-salary:view', 1, '/finance/salary', 'Money', 65),
    ('工资-编辑', 'finance-salary:edit', 2, None, None, 0),
    ('费用管理', 'finance-expense:view', 1, '/finance/expense', 'Money', 66),
    ('费用-编辑', 'finance-expense:edit', 2, None, None, 0),
    ('业绩统计', 'finance-statistics:view', 1, '/finance/statistics', 'TrendCharts', 67),
    ('对账管理', 'finance-reconciliation:view', 1, '/finance/reconciliation', 'Document', 68),
    ('对账-编辑', 'finance-reconciliation:edit', 2, None, None, 0),

    # --- 系统设置 ---
    ('用户管理', 'settings-users:view', 1, '/settings/users', 'User', 70),
    ('用户-新增', 'settings-users:add', 2, None, None, 0),
    ('用户-编辑', 'settings-users:edit', 2, None, None, 0),
    ('用户-分配角色', 'settings-users:role', 2, None, None, 0),
    ('用户-重置密码', 'settings-users:password', 2, None, None, 0),
    ('用户-删除', 'settings-users:delete', 2, None, None, 0),

    ('角色管理', 'settings-roles:view', 1, '/settings/roles', 'UserFilled', 71),
    ('角色-新增', 'settings-roles:add', 2, None, None, 0),
    ('角色-编辑', 'settings-roles:edit', 2, None, None, 0),
    ('角色-分配权限', 'settings-roles:permission', 2, None, None, 0),
    ('角色-删除', 'settings-roles:delete', 2, None, None, 0),

    ('商品分类', 'settings-category:view', 1, '/settings/category', 'Setting', 72),
    ('分类-新增', 'settings-category:add', 2, None, None, 0),
    ('分类-编辑', 'settings-category:edit', 2, None, None, 0),
    ('分类-删除', 'settings-category:delete', 2, None, None, 0),

    ('计量单位', 'settings-unit:view', 1, '/settings/unit', 'Setting', 73),
    ('单位-新增', 'settings-unit:add', 2, None, None, 0),
    ('单位-编辑', 'settings-unit:edit', 2, None, None, 0),
    ('单位-删除', 'settings-unit:delete', 2, None, None, 0),

    ('打印模版', 'settings-print:view', 1, '/settings/print', 'Setting', 74),
    ('打印-新增', 'settings-print:add', 2, None, None, 0),
    ('打印-编辑', 'settings-print:edit', 2, None, None, 0),
    ('打印-删除', 'settings-print:delete', 2, None, None, 0),

    ('操作日志', 'settings-log:view', 1, '/settings/log', 'Document', 75),
]


# ============================================================
# 角色默认权限（统一 ":" 风格，跟前端 menuPermissionMap 对齐）
# admin 用通配符 "*"
# ============================================================
ROLES = [
    # name, code, permissions_json, description
    ('系统管理员', 'admin', '["*"]', '全部权限'),
    (
        '维修技师', 'technician',
        # 工单（增改，但不导出/删除）+ 接件（增改）+ 派单只查看（不参与改派）
        # + 资产查看（查设备归属）+ 库存查询/仓库查看/变动明细（看但不操作进出库）
        # + 客户查看
        # 不给：dispatch:edit（改派是店长活）、workorder:export（导出报表是店长/财务）
        #      inventory-in/out/check:view（出入库/盘点操作菜单给库管）
        '["workorder:view","workorder:add","workorder:edit",'
        '"receive:view","receive:add","receive:edit",'
        '"dispatch:view",'
        '"asset:view",'
        '"inventory:view","warehouse:view","inventory-log:view",'
        '"customer:view"]',
        '工单/接件/资产/库存查询',
    ),
    (
        '财务', 'finance',
        # 全套 finance（含编辑，但无删除权限 —— 删除走管理员审批）
        # + 采购/销售/库存/工单查看（对账要看到业务单据）+ 客户/供应商查看
        # + 业绩统计
        # 不给：product:view（不需要看商品 SKU）、system 全部
        '["finance:view","finance-statistics:view",'
        '"finance-receivable:view","finance-receivable:edit",'
        '"finance-payable:view","finance-payable:edit",'
        '"finance-receipt:view","finance-receipt:edit",'
        '"finance-payment:view","finance-payment:edit",'
        '"finance-salary:view","finance-salary:edit",'
        '"finance-expense:view","finance-expense:edit",'
        '"finance-reconciliation:view","finance-reconciliation:edit",'
        '"purchase:view","sales:view","inventory:view","workorder:view",'
        '"customer:view","supplier:view"]',
        '财务全模块 + 业务单据查看',
    ),
    (
        '库管', 'warehouse',
        # 库存全套（含编辑）+ 商品（增改）+ 采购（增改）+ 仓库 + 调拨调价
        # + 接件/工单查看（仓库接到接件/工单后要备货出库，所以需要看这两个单据）
        # 不给：sales:view（销售是销售员做）、customer:view（库管对外只联系供应商）
        '["inventory:view","inventory-in:view","inventory-in:add","inventory-in:edit",'
        '"inventory-out:view","inventory-out:add","inventory-out:edit",'
        '"inventory-check:view","inventory-check:add","inventory-check:edit",'
        '"warehouse:view","warehouse:add","warehouse:edit",'
        '"inventory-log:view",'
        '"transfer:view","transfer:add","transfer:edit",'
        '"cost-adjust:view","cost-adjust:add","cost-adjust:edit",'
        '"product:view","product:add","product:edit",'
        '"purchase:view","purchase:add","purchase:edit",'
        '"receive:view","workorder:view",'
        '"supplier:view"]',
        '库存/商品/采购/仓库',
    ),
]

# 默认用户：(username, plain_password_or_None, real_name, role_code)
# plain_password=None 表示使用 DEFAULT_ADMIN_PASSWORD 环境变量
DEFAULT_USERS = [
    ('admin', None, '系统管理员', 'admin'),
    ('test1', '123456', '测试技师', 'technician'),
]


def init_database():
    """执行 init.sql + 写入种子数据。"""
    import argparse
    parser = argparse.ArgumentParser(description='初始化 SQLite 数据库')
    parser.add_argument(
        '--force', action='store_true',
        help='已存在数据库时也覆盖（危险：会清空所有业务数据）',
    )
    args, _ = parser.parse_known_args()

    db_file = _resolve_sqlite_uri()
    if db_file is None:
        raise RuntimeError('DATABASE_URL 指向内存数据库，不应执行 init_db 脚本')

    db_file.parent.mkdir(parents=True, exist_ok=True)
    sql_file = _BACKEND / 'database' / 'init.sql'
    if not sql_file.exists():
        raise FileNotFoundError(f'找不到 init.sql: {sql_file}')

    print(f'[init_db] 目标数据库: {db_file}')
    if db_file.exists():
        if not args.force:
            raise RuntimeError(
                f'数据库已存在：{db_file}\n'
                f'如确认要重建，请加 --force 参数（会清空全部业务数据）。'
            )
        print(f'[init_db] --force：覆盖 {db_file}')
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

    # 状态机迁移（即使刚 init 也跑，幂等无副作用）
    from scripts.migrate_status import migrate as migrate_status
    result = migrate_status(str(db_file))
    if result['work_order'] or result['receive_order']:
        print(f'[init_db] 状态迁移: {result}')


def _seed(conn: sqlite3.Connection):
    """插入权限目录 + 默认角色 + 默认用户。"""
    now = datetime.now().isoformat(sep=' ')
    admin_default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', '123456')

    # 1) 权限目录
    perm_rows = [
        (name, code, type, path, icon, sort_order)
        for (name, code, type, path, icon, sort_order) in PERMISSIONS
    ]
    conn.executemany(
        'INSERT INTO sys_permission (name, code, type, parent_id, path, icon, sort_order, status, created_at) '
        'VALUES (?, ?, ?, 0, ?, ?, ?, 1, ?)',
        [r + (now,) for r in perm_rows],
    )
    print(f'[init_db] 已写入 {len(perm_rows)} 条权限到 sys_permission')

    # 2) 角色
    for role_name, role_code, perms, desc in ROLES:
        conn.execute(
            'INSERT INTO sys_role (role_name, role_code, permissions, description, status, created_at, updated_at) '
            'VALUES (?, ?, ?, ?, 1, ?, ?)',
            (role_name, role_code, perms, desc, now, now),
        )
    print(f'[init_db] 已写入 {len(ROLES)} 个角色到 sys_role')

    # 3) 默认用户（需要先拿到 role.id）
    created_users = []
    for username, plain_pw, real_name, role_code in DEFAULT_USERS:
        role = conn.execute(
            'SELECT id FROM sys_role WHERE role_code = ?', (role_code,)
        ).fetchone()
        if not role:
            print(f'[init_db] 跳过用户 {username}：角色 {role_code} 不存在')
            continue
        role_id = role[0]
        pw_to_hash = plain_pw if plain_pw is not None else admin_default_password
        pw_hash = bcrypt.hashpw(
            pw_to_hash.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')
        conn.execute(
            'INSERT INTO sys_user (username, password, real_name, status, role_id, created_at, updated_at) '
            'VALUES (?, ?, ?, 1, ?, ?, ?)',
            (username, pw_hash, real_name, role_id, now, now),
        )
        created_users.append((username, role_code))

    print('[init_db] 已创建用户：')
    for u, rc in created_users:
        print(f'  - {u} (role: {rc})')


if __name__ == '__main__':
    init_database()
