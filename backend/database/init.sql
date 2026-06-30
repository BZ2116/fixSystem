-- ============================================
-- Repair System SQLite Schema
-- Generated from MySQL version (docs/archive/database_complete_v3.sql); SQLite-compatible.
-- Translation rules applied:
--   ENGINE=InnoDB / CHARSET=utf8mb4 -> removed (SQLite defaults)
--   AUTO_INCREMENT -> INTEGER PRIMARY KEY AUTOINCREMENT
--   ON UPDATE CURRENT_TIMESTAMP -> handled in app layer (TimestampMixin)
--   JSON columns -> TEXT (SQLAlchemy db.JSON is dialect-agnostic)
--   ENUM -> none present in current schema
--   Stored procedures (safe_add_*) -> dropped per spec
-- ============================================

PRAGMA foreign_keys = ON;

-- ============================================
-- system
-- ============================================
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

-- ============================================
-- product / inventory
-- ============================================
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

-- ============================================
-- customer / supplier
-- ============================================
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

-- ============================================
-- workorder
-- ============================================
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

-- ============================================
-- purchase / receive / sales
-- ============================================
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

-- ============================================
-- quote / dispatch
-- ============================================
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

-- ============================================
-- finance
-- ============================================
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

-- ============================================
-- asset / device
-- ============================================
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

-- ============================================
-- office
-- ============================================
CREATE TABLE office (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,
    config TEXT,  -- JSON
    status INTEGER DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- ============================================
-- JWT blacklist (new for portable migration)
-- ============================================
CREATE TABLE jwt_blacklist (
    jti TEXT PRIMARY KEY,
    revoked_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL
);
CREATE INDEX idx_jwt_blacklist_expires_at ON jwt_blacklist(expires_at);

-- ============================================
-- indexes -- hot query paths
-- ============================================
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