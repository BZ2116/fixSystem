-- ============================================
-- Repair System SQLite Schema
-- Auto-derived from backend/models/*.py SQLAlchemy models.
-- Generated: 2026-06-30
-- Tables: 71 from models + 1 jwt_blacklist = 72 total
-- ============================================
--
-- Translation rules (SQLAlchemy -> SQLite):
--   db.BigInteger            -> INTEGER
--   db.Integer               -> INTEGER
--   db.String(N)             -> TEXT
--   db.Text                  -> TEXT
--   db.DateTime              -> DATETIME
--   db.Date                  -> DATE
--   db.Numeric(p, s)         -> DECIMAL(p, s)  (alias Numeric == Decimal)
--   db.Float                 -> REAL
--   db.Boolean               -> INTEGER (0/1)
--   db.JSON                  -> TEXT  (JSON-encoded by SQLAlchemy)
--   primary_key=True         -> INTEGER PRIMARY KEY AUTOINCREMENT
--   nullable=False           -> NOT NULL
--   default=X                -> DEFAULT X
--   unique=True              -> UNIQUE
--   db.ForeignKey(...)       -> omitted (FK enforced by app layer)
--   index=True               -> CREATE INDEX (after table)
--   db.relationship / __table_args__ / info / comment -> dropped (Python-only)
--
-- NOTE: This file mirrors SQLAlchemy model declarations.
--       Update it whenever backend/models/*.py change.
-- ============================================

-- ============================================
-- system
-- ============================================
CREATE TABLE sys_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    real_name TEXT,
    phone TEXT,
    email TEXT,
    avatar TEXT,
    role_id INTEGER,
    department TEXT,
    position TEXT,
    base_salary DECIMAL(15, 2) DEFAULT 0.00,
    status INTEGER DEFAULT 1,
    last_login_time DATETIME,
    last_login_ip TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER,
    is_deleted INTEGER DEFAULT 0
);

CREATE TABLE sys_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL,
    role_code TEXT UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT,  -- JSON
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE sys_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    type INTEGER DEFAULT 1,  -- 1:菜单 2:按钮 3:接口
    parent_id INTEGER DEFAULT 0,
    path TEXT,
    icon TEXT,
    sort_order INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME
);

CREATE TABLE sys_role_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at DATETIME
);

CREATE TABLE operation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    module TEXT,
    action TEXT,
    target_type TEXT,
    target_id INTEGER,
    content TEXT,
    ip TEXT,
    created_at DATETIME
);

CREATE TABLE office (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    sort_order INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

-- ============================================
-- customer / supplier
-- ============================================
CREATE TABLE base_customer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT UNIQUE,
    customer_name TEXT NOT NULL,
    customer_type INTEGER DEFAULT 1,  -- 1:个人 2:企业
    pinyin_code TEXT,
    contact_name TEXT,
    phone TEXT,
    phone2 TEXT,
    email TEXT,
    address TEXT,
    discount_rate DECIMAL(5, 2) DEFAULT 100.00,
    credit_limit DECIMAL(15, 2) DEFAULT 0.00,
    tax_number TEXT,
    bank_name TEXT,
    bank_account TEXT,
    remark TEXT,
    total_sales_amount DECIMAL(15, 2) DEFAULT 0.00,
    total_sales_count INTEGER DEFAULT 0,
    last_sales_date DATE,
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE base_supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_code TEXT UNIQUE,
    supplier_name TEXT NOT NULL,
    pinyin_code TEXT,
    contact_name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    tax_number TEXT,
    bank_name TEXT,
    bank_account TEXT,
    is_repair_partner INTEGER DEFAULT 0,
    repair_types TEXT,  -- JSON
    remark TEXT,
    total_purchase_amount DECIMAL(15, 2) DEFAULT 0.00,
    total_purchase_count INTEGER DEFAULT 0,
    total_repair_amount DECIMAL(15, 2) DEFAULT 0.00,
    total_repair_count INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

-- ============================================
-- asset
-- ============================================
CREATE TABLE asset_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_code TEXT UNIQUE NOT NULL,
    type_name TEXT NOT NULL,
    icon TEXT,
    sort_order INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE own_device (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_no TEXT UNIQUE NOT NULL,
    device_type TEXT,
    device_model TEXT,
    serial_number TEXT,
    cpu TEXT,
    memory TEXT,
    hard_disk TEXT,
    system TEXT,
    system_version TEXT,
    accessories TEXT,
    account TEXT,
    password TEXT,
    password_remark TEXT,
    purchase_date DATE,
    warranty_expire DATE,
    location TEXT,
    user_id INTEGER,
    cost DECIMAL(15, 2) DEFAULT 0.00,
    depreciation DECIMAL(15, 2) DEFAULT 0.00,
    status INTEGER DEFAULT 0,  -- 0正常 1维修中 2报废 3外借
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE asset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_no TEXT UNIQUE,
    customer_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    office_id INTEGER,
    office_name TEXT,
    location TEXT,
    asset_type_id INTEGER NOT NULL,
    asset_type_name TEXT,
    asset_name TEXT NOT NULL,
    device_no TEXT,
    sn_code TEXT,
    register_date DATE,
    purchase_date DATE,
    warranty_expire_date DATE,
    warranty_status INTEGER DEFAULT 1,  -- 0过保 1在保
    asset_status INTEGER DEFAULT 1,    -- 1正常 2维修中 3闲置 4报废 5停用
    responsible_person TEXT,
    contact_phone TEXT,
    ip_address TEXT,
    login_password TEXT,
    remark TEXT,
    asset_data TEXT,  -- JSON
    sales_order_id INTEGER,
    sales_order_no TEXT,
    created_by INTEGER,
    created_by_name TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- ============================================
-- product
-- ============================================
CREATE TABLE product_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL,
    parent_id INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME
);

CREATE TABLE product_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT UNIQUE NOT NULL,
    barcode TEXT UNIQUE,
    product_name TEXT NOT NULL,
    pinyin_code TEXT,
    category_id INTEGER,
    category_name TEXT,
    brand TEXT,
    specification TEXT,
    unit_id INTEGER,
    unit_name TEXT,
    sub_unit_id INTEGER,
    sub_unit_rate DECIMAL(10, 4),
    purchase_price DECIMAL(15, 4) DEFAULT 0.0000,
    sale_price DECIMAL(15, 4) DEFAULT 0.0000,
    member_price DECIMAL(15, 4) DEFAULT 0.0000,
    wholesale_price DECIMAL(15, 4) DEFAULT 0.0000,
    customer_price DECIMAL(15, 4) DEFAULT 0.0000,
    cost_price DECIMAL(15, 4) DEFAULT 0.0000,
    min_stock INTEGER DEFAULT 0,
    max_stock INTEGER DEFAULT 0,
    current_stock INTEGER DEFAULT 0,
    weight DECIMAL(10, 3),
    volume DECIMAL(10, 3),
    shelf_life INTEGER,
    is_serial INTEGER DEFAULT 0,
    is_batch INTEGER DEFAULT 0,
    is_assembly INTEGER DEFAULT 0,
    is_gift INTEGER DEFAULT 0,
    no_cost INTEGER DEFAULT 0,
    no_stock INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    remark TEXT,
    image_url TEXT,
    shelf_id INTEGER,
    shelf_name TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE product_unit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_name TEXT NOT NULL,
    unit_code TEXT UNIQUE,
    conversion_rate DECIMAL(10, 4) DEFAULT 1.0000,
    is_base INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME
);

CREATE TABLE product_unit_rel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    unit_id INTEGER NOT NULL,
    conversion_rate DECIMAL(10, 4) DEFAULT 1.0000,
    is_default INTEGER DEFAULT 0,
    created_at DATETIME
);

-- ============================================
-- inventory
-- ============================================
CREATE TABLE warehouse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_code TEXT UNIQUE,
    warehouse_name TEXT NOT NULL,
    address TEXT,
    contact_person TEXT,
    contact_phone TEXT,
    remark TEXT,
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE shelf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shelf_name TEXT NOT NULL,
    shelf_code TEXT UNIQUE,
    warehouse_id INTEGER NOT NULL,
    warehouse_name TEXT,
    location TEXT,
    sort_order INTEGER DEFAULT 0,
    remark TEXT,
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE inventory_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    product_code TEXT,
    product_name TEXT,
    warehouse_id INTEGER DEFAULT 1,
    warehouse_name TEXT DEFAULT '主仓库',
    shelf_id INTEGER,
    shelf_name TEXT,
    quantity DECIMAL(10, 2) DEFAULT 0,
    frozen_quantity DECIMAL(10, 2) DEFAULT 0,
    available_quantity DECIMAL(10, 2) DEFAULT 0,
    cost_price DECIMAL(15, 4) DEFAULT 0.0000,
    batch_no TEXT,
    serial_no TEXT,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE inventory_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    warehouse_id INTEGER,
    warehouse_name TEXT,
    change_type TEXT,
    order_type TEXT,
    order_id INTEGER,
    order_no TEXT,
    quantity_change DECIMAL(10, 2) DEFAULT 0,
    before_quantity DECIMAL(10, 2) DEFAULT 0,
    after_quantity DECIMAL(10, 2) DEFAULT 0,
    cost_price DECIMAL(15, 4) DEFAULT 0,
    amount DECIMAL(15, 2) DEFAULT 0,
    related_party TEXT,
    operator_id INTEGER,
    operator_name TEXT,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE cost_adjust (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adjust_no TEXT UNIQUE,
    warehouse_id INTEGER,
    warehouse_name TEXT,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    old_cost_price DECIMAL(15, 4) DEFAULT 0,
    new_cost_price DECIMAL(15, 4) DEFAULT 0,
    adjust_quantity DECIMAL(10, 2) DEFAULT 0,
    adjust_amount DECIMAL(15, 2) DEFAULT 0,
    status INTEGER DEFAULT 0,
    remark TEXT,
    created_by INTEGER,
    created_by_name TEXT,
    audited_by INTEGER,
    audited_by_name TEXT,
    audited_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE inventory_in (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    in_no TEXT UNIQUE NOT NULL,
    in_type INTEGER DEFAULT 1,  -- 1采购入库 2退货入库 3调拨入库 4组装入库 5其他入库
    supplier_id INTEGER,
    supplier_name TEXT,
    warehouse_id INTEGER DEFAULT 1,
    warehouse_name TEXT,
    total_quantity DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    status INTEGER DEFAULT 0,  -- 0待审核 1已审核 2已入库
    auditor_id INTEGER,
    auditor_name TEXT,
    audit_time DATETIME,
    remark TEXT,
    related_order_id INTEGER,
    related_order_no TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE inventory_in_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    in_id INTEGER NOT NULL,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    specification TEXT,
    unit_name TEXT,
    quantity DECIMAL(10, 2) DEFAULT 0,
    unit_price DECIMAL(15, 4) DEFAULT 0.0000,
    total_price DECIMAL(15, 2) DEFAULT 0.00,
    cost_price DECIMAL(15, 4) DEFAULT 0.0000,
    batch_no TEXT,
    serial_no TEXT,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE inventory_out (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    out_no TEXT UNIQUE NOT NULL,
    out_type INTEGER DEFAULT 1,  -- 1销售出库 2维修领料 3调拨出库 4拆卸出库 5其他出库
    customer_id INTEGER,
    customer_name TEXT,
    warehouse_id INTEGER DEFAULT 1,
    warehouse_name TEXT,
    total_quantity DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    status INTEGER DEFAULT 0,  -- 0待审核 1已审核 2已出库
    auditor_id INTEGER,
    auditor_name TEXT,
    audit_time DATETIME,
    remark TEXT,
    related_order_id INTEGER,
    related_order_no TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE inventory_out_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    out_id INTEGER NOT NULL,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    specification TEXT,
    unit_name TEXT,
    quantity DECIMAL(10, 2) DEFAULT 0,
    unit_price DECIMAL(15, 4) DEFAULT 0.0000,
    total_price DECIMAL(15, 2) DEFAULT 0.00,
    cost_price DECIMAL(15, 4) DEFAULT 0.0000,
    batch_no TEXT,
    serial_no TEXT,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE inventory_check (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_no TEXT UNIQUE NOT NULL,
    warehouse_id INTEGER DEFAULT 1,
    warehouse_name TEXT,
    shelf_id INTEGER,
    shelf_name TEXT,
    check_date DATE,
    status INTEGER DEFAULT 0,  -- 0待盘点 1盘点中 2已完成
    total_quantity INTEGER DEFAULT 0,
    diff_quantity INTEGER DEFAULT 0,
    diff_amount DECIMAL(15, 2) DEFAULT 0.00,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE inventory_check_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_id INTEGER NOT NULL,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    specification TEXT,
    unit_name TEXT,
    system_quantity DECIMAL(10, 2) DEFAULT 0,
    actual_quantity DECIMAL(10, 2) DEFAULT 0,
    diff_quantity DECIMAL(10, 2) DEFAULT 0,
    cost_price DECIMAL(15, 4) DEFAULT 0.0000,
    diff_amount DECIMAL(15, 2) DEFAULT 0.00,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE transfer_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_no TEXT UNIQUE NOT NULL,
    from_warehouse_id INTEGER,
    from_warehouse_name TEXT,
    to_warehouse_id INTEGER,
    to_warehouse_name TEXT,
    total_quantity DECIMAL(10, 2) DEFAULT 0,
    status INTEGER DEFAULT 0,  -- 0待审核 1已审核 2已完成
    transfer_type INTEGER DEFAULT 1,  -- 1同价调拨 2变价调拨
    from_cost_price DECIMAL(15, 4) DEFAULT 0,
    to_cost_price DECIMAL(15, 4) DEFAULT 0,
    operator_id INTEGER,
    operator_name TEXT,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE transfer_order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_id INTEGER NOT NULL,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    specification TEXT,
    unit_name TEXT,
    quantity DECIMAL(10, 2) DEFAULT 0,
    from_cost_price DECIMAL(15, 4) DEFAULT 0,
    to_cost_price DECIMAL(15, 4) DEFAULT 0,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE assemble_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assemble_no TEXT UNIQUE NOT NULL,
    product_id INTEGER,
    product_name TEXT,
    quantity DECIMAL(10, 2) DEFAULT 1,
    warehouse_id INTEGER DEFAULT 1,
    warehouse_name TEXT,
    status INTEGER DEFAULT 0,  -- 0待审核 1已审核 2已完成
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE assemble_order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assemble_id INTEGER NOT NULL,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    specification TEXT,
    unit_name TEXT,
    quantity DECIMAL(10, 2) DEFAULT 0,
    cost_price DECIMAL(15, 4) DEFAULT 0.0000,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE pre_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pre_no TEXT UNIQUE NOT NULL,
    pre_type INTEGER DEFAULT 1,  -- 1采购预定 2销售预定
    customer_id INTEGER,
    customer_name TEXT,
    supplier_id INTEGER,
    supplier_name TEXT,
    total_quantity DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    status INTEGER DEFAULT 0,  -- 0待处理 1已转单 2已取消
    related_order_id INTEGER,
    related_order_no TEXT,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE pre_order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pre_id INTEGER NOT NULL,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    quantity DECIMAL(10, 2) DEFAULT 0,
    unit_price DECIMAL(15, 4) DEFAULT 0.0000,
    total_price DECIMAL(15, 2) DEFAULT 0.00,
    remark TEXT,
    created_at DATETIME
);

-- ============================================
-- purchase
-- ============================================
CREATE TABLE purchase_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    supplier_id INTEGER,
    supplier_name TEXT,
    order_date DATE,
    delivery_date DATE,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    total_quantity INTEGER DEFAULT 0,
    status INTEGER DEFAULT 0,  -- 0待审核 1已审核 2已完成 3已取消
    has_invoice INTEGER DEFAULT 0,
    remark TEXT,
    created_by INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE purchase_order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    product_name TEXT,
    specification TEXT,
    unit TEXT,
    quantity INTEGER DEFAULT 0,
    price DECIMAL(15, 4) DEFAULT 0,
    amount DECIMAL(15, 2) DEFAULT 0,
    received_qty INTEGER DEFAULT 0,
    remark TEXT
);

CREATE TABLE return_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_no TEXT UNIQUE NOT NULL,
    return_type INTEGER DEFAULT 1,  -- 1采购退货 2销售退货
    related_order_id INTEGER,
    related_order_no TEXT,
    supplier_id INTEGER,
    supplier_name TEXT,
    customer_id INTEGER,
    customer_name TEXT,
    total_quantity INTEGER DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    refund_amount DECIMAL(15, 2) DEFAULT 0,
    status INTEGER DEFAULT 0,  -- 0待审核 1已审核 2已入库 3已取消
    reason TEXT,
    remark TEXT,
    created_by INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE return_order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    quantity INTEGER DEFAULT 0,
    unit_price DECIMAL(15, 4) DEFAULT 0,
    total_price DECIMAL(15, 2) DEFAULT 0,
    remark TEXT,
    created_at DATETIME
);

-- ============================================
-- sales
-- ============================================
CREATE TABLE sales_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    customer_address TEXT,
    contact_name TEXT,
    order_date DATE,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    total_quantity INTEGER DEFAULT 0,
    discount_amount DECIMAL(15, 2) DEFAULT 0,
    freight_amount DECIMAL(15, 2) DEFAULT 0,
    actual_amount DECIMAL(15, 2) DEFAULT 0,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    payment_method TEXT,
    delivery_method TEXT,
    salesperson_id INTEGER,
    salesperson_name TEXT,
    status INTEGER DEFAULT 0,  -- 0待审核 1已审核 2已出库 3已完成 4已取消
    remark TEXT,
    created_by INTEGER,
    created_at DATETIME,
    updated_at DATETIME,
    has_invoice INTEGER DEFAULT 0,
    has_receipt INTEGER DEFAULT 0
);

CREATE TABLE sales_order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    product_name TEXT,
    specification TEXT,
    unit TEXT,
    quantity INTEGER DEFAULT 0,
    price DECIMAL(15, 4) DEFAULT 0,
    amount DECIMAL(15, 2) DEFAULT 0,
    delivered_qty INTEGER DEFAULT 0,
    remark TEXT
);

CREATE TABLE sales_invoice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    order_no TEXT,
    invoice_type TEXT,
    invoice_status TEXT DEFAULT '未开票',
    invoice_no TEXT,
    invoice_date DATE,
    buyer_name TEXT,
    buyer_tax_no TEXT,
    buyer_address TEXT,
    buyer_phone TEXT,
    buyer_bank TEXT,
    buyer_bank_account TEXT,
    items TEXT,  -- JSON
    total_amount DECIMAL(15, 2) DEFAULT 0,
    total_tax DECIMAL(15, 2) DEFAULT 0,
    total_with_tax DECIMAL(15, 2) DEFAULT 0,
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    remark TEXT,
    attachment TEXT,
    created_by INTEGER,
    created_by_name TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE sales_receipt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    order_no TEXT,
    receipt_no TEXT,
    receipt_date DATE,
    customer_name TEXT,
    customer_phone TEXT,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    payment_method TEXT,
    items TEXT,  -- JSON
    remark TEXT,
    payee TEXT,
    status INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

-- ============================================
-- quote
-- ============================================
CREATE TABLE quote_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_no TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    contact_name TEXT,
    address TEXT,
    quote_date DATE,
    valid_until DATE,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    remark TEXT,
    status INTEGER DEFAULT 0,  -- 0待确认 1已确认 2已失效 3已转工单 4已转接件 5已转销售
    related_type TEXT,
    related_id INTEGER,
    created_by INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE quote_order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    product_name TEXT,
    specification TEXT,
    brand TEXT,
    unit TEXT,
    quantity DECIMAL(10, 2) DEFAULT 1,
    unit_price DECIMAL(15, 2) DEFAULT 0.00,
    subtotal DECIMAL(15, 2) DEFAULT 0.00,
    remark TEXT,
    created_at DATETIME
);

-- ============================================
-- receive (接件单 / 设备档案 / 接收单 / 配件 / 照片)
-- ============================================
CREATE TABLE receive_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receive_no TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    receive_type INTEGER DEFAULT 1,  -- 1本店修 2外送修
    external_shop_id INTEGER,
    external_shop_name TEXT,
    status INTEGER DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    paid_amount DECIMAL(15, 2) DEFAULT 0.00,
    remark TEXT,
    receiver_id INTEGER,
    receiver_name TEXT,
    engineer_id INTEGER,
    engineer_name TEXT,
    detect_result TEXT,
    detect_fault_reason TEXT,
    detect_repair_plan TEXT,
    detect_parts TEXT,
    quote_labor_cost DECIMAL(10, 2) DEFAULT 0.00,
    quote_material_cost DECIMAL(10, 2) DEFAULT 0.00,
    quote_other_cost DECIMAL(10, 2) DEFAULT 0.00,
    quote_total DECIMAL(10, 2) DEFAULT 0.00,
    quote_confirmed INTEGER DEFAULT 0,
    quote_confirm_time DATETIME,
    external_quote DECIMAL(10, 2) DEFAULT 0.00,
    external_repair_reason TEXT,
    external_send_date DATE,
    external_return_date DATE,
    external_round INTEGER DEFAULT 1,
    external_history TEXT,
    finish_report TEXT,
    finish_photos TEXT,
    test_result INTEGER DEFAULT 0,
    test_remark TEXT,
    notify_time DATETIME,
    notify_method TEXT,
    complete_time DATETIME,
    finance_record_id INTEGER,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE receive_order_device (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receive_order_id INTEGER NOT NULL,
    device_archive_id INTEGER,
    device_type TEXT,
    device_brand TEXT,
    device_model TEXT,
    device_sn TEXT,
    device_imei TEXT,
    fault_desc TEXT,
    appearance_desc TEXT,
    accessories TEXT,
    work_order_id INTEGER,
    status INTEGER DEFAULT 0,
    created_at DATETIME,
    device_name TEXT,
    cpu TEXT,
    memory TEXT,
    disk TEXT,
    os TEXT,
    os_version TEXT,
    toner_model TEXT,
    drum_model TEXT,
    ip_address TEXT,
    port INTEGER,
    camera_count INTEGER,
    monitor_brand TEXT,
    firmware_version TEXT,
    port_count INTEGER,
    label_printed INTEGER DEFAULT 0
);

CREATE TABLE receive_order_part (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receive_order_id INTEGER NOT NULL,
    product_id INTEGER,
    product_name TEXT,
    product_code TEXT,
    specification TEXT,
    unit_name TEXT,
    quantity DECIMAL(10, 2) DEFAULT 0,
    unit_price DECIMAL(10, 2) DEFAULT 0.00,
    total_price DECIMAL(10, 2) DEFAULT 0.00,
    cost_price DECIMAL(10, 2) DEFAULT 0.00,
    source INTEGER DEFAULT 1,
    inventory_out_item_id INTEGER,
    purchase_order_item_id INTEGER,
    status INTEGER DEFAULT 0,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE device_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_code TEXT UNIQUE,
    customer_id INTEGER,
    device_type TEXT,
    device_name TEXT,
    device_brand TEXT,
    device_model TEXT,
    device_sn TEXT,
    device_imei TEXT,
    device_password TEXT,
    ip_address TEXT,
    port INTEGER,
    quantity INTEGER DEFAULT 1,
    cpu TEXT,
    memory TEXT,
    disk TEXT,
    os TEXT,
    os_version TEXT,
    accessories TEXT,
    account TEXT,
    password TEXT,
    password_remark TEXT,
    consumable_model TEXT,
    toner_model TEXT,
    drum_model TEXT,
    purchase_date DATE,
    warranty_expire DATE,
    remark TEXT,
    repair_count INTEGER DEFAULT 0,
    last_repair_date DATE,
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE device_receive_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receive_no TEXT UNIQUE NOT NULL,
    wo_id INTEGER,
    customer_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    device_type TEXT,
    device_brand TEXT,
    device_model TEXT,
    device_sn TEXT,
    device_imei TEXT,
    appearance_desc TEXT,
    accessories TEXT,
    device_password TEXT,
    fault_desc TEXT,
    remark TEXT,
    receiver_id INTEGER,
    receiver_name TEXT,
    receive_time DATETIME,
    customer_sign TEXT,
    sign_time DATETIME,
    status INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE device_accessory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receive_order_id INTEGER NOT NULL,
    accessory_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    status TEXT DEFAULT '完好',
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE device_photo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receive_order_id INTEGER NOT NULL,
    photo_type TEXT DEFAULT '整体照',
    photo_url TEXT NOT NULL,
    remark TEXT,
    created_at DATETIME
);

-- ============================================
-- workorder
-- ============================================
CREATE TABLE work_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_no TEXT UNIQUE NOT NULL,
    wo_type TEXT,
    wo_sub_type TEXT,
    customer_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    customer_address TEXT,
    device_type TEXT,
    device_brand TEXT,
    device_model TEXT,
    device_sn TEXT,
    device_imei TEXT,
    device_password TEXT,
    device_need_door INTEGER DEFAULT 0,
    net_type TEXT,
    net_operator TEXT,
    net_need_device INTEGER DEFAULT 0,
    goods_type TEXT,
    goods_quantity INTEGER DEFAULT 1,
    goods_need_install INTEGER DEFAULT 0,
    goods_floor_type TEXT,
    goods_floor INTEGER DEFAULT 1,
    monitor_brand TEXT,
    camera_count INTEGER DEFAULT 0,
    camera_location TEXT,
    monitor_need_record INTEGER DEFAULT 0,
    record_days INTEGER DEFAULT 7,
    fault_desc TEXT,
    appearance_desc TEXT,
    accessories TEXT,
    remark TEXT,
    status INTEGER DEFAULT 0,
    status_name TEXT,
    labor_cost DECIMAL(15, 2) DEFAULT 0.00,
    parts_cost DECIMAL(15, 2) DEFAULT 0.00,
    material_cost DECIMAL(15, 2) DEFAULT 0.00,
    transport_cost DECIMAL(15, 2) DEFAULT 0.00,
    total_cost DECIMAL(15, 2) DEFAULT 0.00,
    settlement_status INTEGER DEFAULT 0,
    settlement_account_id INTEGER,
    settlement_time DATETIME,
    assigned_user_id INTEGER,
    assigned_user_name TEXT,
    assigned_time DATETIME,
    quote_id INTEGER,
    quote_confirmed INTEGER DEFAULT 0,
    quote_confirm_time DATETIME,
    receive_order_id INTEGER,
    receive_confirmed INTEGER DEFAULT 0,
    receive_confirm_time DATETIME,
    customer_sign TEXT,
    priority INTEGER DEFAULT 0,
    estimated_time DATETIME,
    actual_time DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER,
    customer_company TEXT,
    customer_office TEXT,
    receiver_id INTEGER,
    receiver_name TEXT,
    need_bring_back INTEGER DEFAULT 0,
    related_quote_id INTEGER,
    related_purchase_id INTEGER,
    related_sales_id INTEGER,
    related_finance_id INTEGER,
    auto_dispatch INTEGER DEFAULT 0,
    dispatch_rule TEXT,
    labor_hours DECIMAL(10, 2),
    labor_unit_price DECIMAL(10, 2),
    service_fee DECIMAL(10, 2) DEFAULT 0,
    delivery_address TEXT,
    install_position TEXT,
    arrival_time DATETIME,
    install_material TEXT,
    acceptance_standard TEXT,
    customer_confirm_items TEXT,
    survey_address TEXT,
    site_environment TEXT,
    device_status_desc TEXT,
    problem_summary TEXT,
    construction_plan TEXT,
    required_parts TEXT,
    estimated_duration TEXT,
    estimated_cost DECIMAL(10, 2),
    customer_device_model TEXT,
    device_source TEXT,
    install_requirement TEXT,
    consumable_usage TEXT,
    purchase_product TEXT,
    purchase_brand TEXT,
    purchase_spec TEXT,
    purchase_qty INTEGER,
    customer_demand TEXT,
    expected_arrival_date DATE,
    purchase_price DECIMAL(10, 2),
    finish_report TEXT,
    finish_photos TEXT,
    test_result INTEGER DEFAULT 0,
    test_remark TEXT,
    return_visit_time DATETIME,
    return_visit_result TEXT,
    customer_acceptance INTEGER DEFAULT 0,
    customer_acceptance_time DATETIME,
    customer_acceptance_sign TEXT,
    print_count INTEGER DEFAULT 0,
    net_topology TEXT,
    fault_location TEXT,
    net_ip TEXT,
    device_port TEXT,
    line_type TEXT,
    test_items TEXT,
    net_speed_data TEXT,
    maintenance_cycle TEXT,
    restart_record TEXT,
    debug_content TEXT,
    device_config TEXT,
    os_version TEXT,
    error_code TEXT,
    repair_part TEXT,
    maintenance_items TEXT,
    replaced_parts TEXT,
    retest_result TEXT,
    channel_no TEXT,
    nvr_model TEXT,
    disk_capacity TEXT,
    recording_status TEXT,
    screen_fault TEXT,
    infrared_status TEXT,
    power_status TEXT,
    line_inspection TEXT,
    point_debug_record TEXT,
    install_points TEXT,
    camera_model TEXT,
    storage_config TEXT,
    cable_length TEXT,
    consumable_qty TEXT,
    debug_result TEXT,
    picture_clarity TEXT,
    recording_settings TEXT,
    delivery_products TEXT,
    repair_camera_count INTEGER DEFAULT 0
);

CREATE TABLE work_order_part (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_id INTEGER NOT NULL,
    product_id INTEGER,
    product_name TEXT,
    product_code TEXT,
    specification TEXT,
    quantity DECIMAL(10, 2) DEFAULT 1,
    unit_price DECIMAL(15, 4) DEFAULT 0.0000,
    total_price DECIMAL(15, 2) DEFAULT 0.00,
    cost_price DECIMAL(15, 4) DEFAULT 0.0000,
    is_own INTEGER DEFAULT 1,
    status INTEGER DEFAULT 0,
    used_quantity DECIMAL(15, 3) DEFAULT 0,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE work_order_quote_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    spec TEXT,
    unit TEXT,
    quantity DECIMAL(10, 2) DEFAULT 1,
    unit_price DECIMAL(15, 4) DEFAULT 0.0000,
    subtotal DECIMAL(15, 2) DEFAULT 0.00,
    created_at DATETIME
);

CREATE TABLE work_order_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_id INTEGER NOT NULL,
    action TEXT,
    old_status INTEGER,
    new_status INTEGER,
    content TEXT,
    operator_id INTEGER,
    operator_name TEXT,
    created_at DATETIME
);

CREATE TABLE work_order_extend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_id INTEGER NOT NULL,
    order_source TEXT,
    service_type TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE wo_customer_part (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_id INTEGER NOT NULL,
    product_id INTEGER,
    product_name TEXT,
    specification TEXT,
    quantity REAL DEFAULT 1,
    unit_price REAL DEFAULT 0,
    remark TEXT,
    created_at DATETIME
);

CREATE TABLE wo_dynamic_field (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_id INTEGER NOT NULL,
    field_key TEXT NOT NULL,
    field_value TEXT,
    field_label TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE wo_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL,
    type_code TEXT UNIQUE NOT NULL,
    default_labor_cost DECIMAL(15, 2) DEFAULT 0.00,
    estimated_days INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME
);

CREATE TABLE wo_sub_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_type TEXT NOT NULL,
    sub_type_code TEXT UNIQUE NOT NULL,
    sub_type_name TEXT NOT NULL,
    device_category TEXT,
    sort_order INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME
);

CREATE TABLE project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    project_code TEXT UNIQUE,
    category TEXT,
    default_price DECIMAL(15, 2) DEFAULT 0.00,
    estimated_hours DECIMAL(5, 1) DEFAULT 1.0,
    remark TEXT,
    status INTEGER DEFAULT 1,
    created_at DATETIME
);

-- ============================================
-- dispatch
-- ============================================
CREATE TABLE dispatch_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_id INTEGER NOT NULL,
    dispatch_type TEXT DEFAULT 'manual',
    dispatcher_id INTEGER,
    dispatcher_name TEXT,
    staff_id INTEGER,
    staff_name TEXT,
    staff_phone TEXT,
    dispatch_time DATETIME,
    accept_status INTEGER DEFAULT 0,
    accept_time DATETIME,
    reject_reason TEXT,
    arrive_time DATETIME,
    start_time DATETIME,
    finish_time DATETIME,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE staff_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER UNIQUE NOT NULL,
    staff_name TEXT,
    online_status INTEGER DEFAULT 0,
    current_wo_id INTEGER,
    today_count INTEGER DEFAULT 0,
    today_finished INTEGER DEFAULT 0,
    max_daily INTEGER DEFAULT 10,
    skills TEXT,
    rating DECIMAL(3, 2) DEFAULT 5.00,
    location TEXT,
    updated_at DATETIME
);

CREATE TABLE dispatch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wo_id INTEGER NOT NULL,
    action TEXT,
    content TEXT,
    operator_id INTEGER,
    operator_name TEXT,
    created_at DATETIME
);

-- ============================================
-- finance
-- ============================================
CREATE TABLE finance_account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL,
    account_type INTEGER DEFAULT 1,
    account_no TEXT,
    balance DECIMAL(15, 2) DEFAULT 0.00,
    status INTEGER DEFAULT 1,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE finance_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    account_name TEXT,
    record_type INTEGER DEFAULT 1,
    amount DECIMAL(15, 2) DEFAULT 0.00,
    balance_before DECIMAL(15, 2) DEFAULT 0.00,
    balance_after DECIMAL(15, 2) DEFAULT 0.00,
    related_type TEXT,
    related_id INTEGER,
    related_no TEXT,
    remark TEXT,
    created_at DATETIME,
    created_by INTEGER
);

CREATE TABLE finance_receivable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receivable_no TEXT UNIQUE,
    related_type TEXT,
    related_id INTEGER,
    related_no TEXT,
    customer_id INTEGER,
    customer_name TEXT,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    received_amount DECIMAL(15, 2) DEFAULT 0,
    remaining_amount DECIMAL(15, 2) DEFAULT 0,
    status INTEGER DEFAULT 0,
    invoice_id INTEGER,
    due_date DATE,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE finance_payable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payable_no TEXT UNIQUE,
    related_type TEXT,
    related_id INTEGER,
    related_no TEXT,
    supplier_id INTEGER,
    supplier_name TEXT,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    remaining_amount DECIMAL(15, 2) DEFAULT 0,
    status INTEGER DEFAULT 0,
    invoice_id INTEGER,
    due_date DATE,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE finance_invoice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT UNIQUE,
    invoice_type INTEGER DEFAULT 1,
    customer_id INTEGER,
    customer_name TEXT,
    amount DECIMAL(15, 2) DEFAULT 0.00,
    tax_amount DECIMAL(15, 2) DEFAULT 0.00,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    status INTEGER DEFAULT 0,
    related_type TEXT,
    related_id INTEGER,
    related_no TEXT,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE purchase_invoice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT UNIQUE,
    invoice_code TEXT,
    invoice_type INTEGER DEFAULT 1,
    purchase_order_id INTEGER,
    purchase_order_no TEXT,
    supplier_id INTEGER,
    supplier_name TEXT,
    amount DECIMAL(15, 2) DEFAULT 0.00,
    tax_rate DECIMAL(5, 2) DEFAULT 0.00,
    tax_amount DECIMAL(15, 2) DEFAULT 0.00,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    invoice_date DATE,
    status INTEGER DEFAULT 0,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER
);

CREATE TABLE salary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    salary_no TEXT UNIQUE,
    user_id INTEGER NOT NULL,
    user_name TEXT NOT NULL,
    department TEXT,
    position TEXT,
    salary_month TEXT NOT NULL,
    base_salary DECIMAL(15, 2) DEFAULT 0.00,
    performance_salary DECIMAL(15, 2) DEFAULT 0.00,
    commission DECIMAL(15, 2) DEFAULT 0.00,
    subsidy DECIMAL(15, 2) DEFAULT 0.00,
    deduction DECIMAL(15, 2) DEFAULT 0.00,
    should_pay DECIMAL(15, 2) DEFAULT 0.00,
    tax DECIMAL(15, 2) DEFAULT 0.00,
    actual_pay DECIMAL(15, 2) DEFAULT 0.00,
    account_id INTEGER,
    account_name TEXT,
    status INTEGER DEFAULT 0,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by INTEGER,
    paid_at DATETIME
);

CREATE TABLE expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_no TEXT UNIQUE,
    expense_name TEXT NOT NULL,
    expense_type INTEGER DEFAULT 1,
    amount DECIMAL(15, 2) DEFAULT 0.00,
    record_type INTEGER DEFAULT 2,
    account_id INTEGER,
    account_name TEXT,
    partner_type TEXT,
    partner_id INTEGER,
    partner_name TEXT,
    expense_date DATE,
    status INTEGER DEFAULT 0,
    attachment TEXT,
    remark TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- ============================================
-- printer
-- ============================================
CREATE TABLE print_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_type TEXT,
    description TEXT,
    header_content TEXT,
    body_content TEXT,
    footer_content TEXT,
    style_content TEXT,
    paper_size TEXT DEFAULT 'A4',
    paper_width INTEGER DEFAULT 210,
    paper_height INTEGER DEFAULT 297,
    is_default INTEGER DEFAULT 0,
    status INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

-- ============================================
-- JWT blacklist (login/logout tracking)
-- ============================================
CREATE TABLE jwt_blacklist (
    jti TEXT PRIMARY KEY,
    revoked_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL
);

-- ============================================
-- indexes (from model index=True hints)
-- ============================================
CREATE INDEX idx_jwt_blacklist_expires_at ON jwt_blacklist(expires_at);

CREATE INDEX idx_wo_dynamic_field_wo_id ON wo_dynamic_field(wo_id);
CREATE INDEX idx_work_order_extend_wo_id ON work_order_extend(wo_id);
CREATE INDEX idx_wo_customer_part_wo_id ON wo_customer_part(wo_id);
CREATE INDEX idx_work_order_quote_item_work_order_id ON work_order_quote_item(work_order_id);