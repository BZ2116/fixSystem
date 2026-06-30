-- ============================================================
-- 维修商贸一体化管理系统 - 数据库完整重构脚本 V3
-- 目标：零报错、全字段、强约束、高关联、商用级
-- 特性：保留现有数据、补全缺失字段、添加约束索引、初始化数据
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- ============================================================
-- 第1部分：创建安全添加字段的存储过程
-- ============================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS safe_add_column$$
CREATE PROCEDURE safe_add_column(
    IN p_table VARCHAR(100),
    IN p_column VARCHAR(100),
    IN p_definition VARCHAR(500),
    IN p_after VARCHAR(100)
)
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    DECLARE after_exists INT DEFAULT 0;
    
    -- 检查列是否已存在
    SELECT COUNT(*) INTO col_exists 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = p_table 
    AND column_name = p_column;
    
    IF col_exists = 0 THEN
        -- 检查AFTER列是否存在
        IF p_after IS NOT NULL AND p_after != '' THEN
            SELECT COUNT(*) INTO after_exists
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = p_table 
            AND column_name = p_after;
            
            IF after_exists > 0 THEN
                SET @sql = CONCAT('ALTER TABLE `', p_table, '` ADD COLUMN `', p_column, '` ', p_definition, ' AFTER `', p_after, '`');
            ELSE
                SET @sql = CONCAT('ALTER TABLE `', p_table, '` ADD COLUMN `', p_column, '` ', p_definition);
            END IF;
        ELSE
            SET @sql = CONCAT('ALTER TABLE `', p_table, '` ADD COLUMN `', p_column, '` ', p_definition);
        END IF;
        
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        
        SELECT CONCAT('Added column: ', p_table, '.', p_column) AS result;
    ELSE
        SELECT CONCAT('Column already exists: ', p_table, '.', p_column) AS result;
    END IF;
END$$

DROP PROCEDURE IF EXISTS safe_add_index$$
CREATE PROCEDURE safe_add_index(
    IN p_table VARCHAR(100),
    IN p_index VARCHAR(100),
    IN p_columns VARCHAR(500)
)
BEGIN
    DECLARE idx_exists INT DEFAULT 0;
    
    SELECT COUNT(*) INTO idx_exists 
    FROM information_schema.statistics 
    WHERE table_schema = DATABASE() 
    AND table_name = p_table 
    AND index_name = p_index;
    
    IF idx_exists = 0 THEN
        SET @sql = CONCAT('CREATE INDEX `', p_index, '` ON `', p_table, '` (', p_columns, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('Created index: ', p_index, ' on ', p_table) AS result;
    ELSE
        SELECT CONCAT('Index already exists: ', p_index) AS result;
    END IF;
END$$

DROP PROCEDURE IF EXISTS safe_modify_column$$
CREATE PROCEDURE safe_modify_column(
    IN p_table VARCHAR(100),
    IN p_column VARCHAR(100),
    IN p_definition VARCHAR(500)
)
BEGIN
    DECLARE col_exists INT DEFAULT 0;
    
    SELECT COUNT(*) INTO col_exists 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = p_table 
    AND column_name = p_column;
    
    IF col_exists = 1 THEN
        SET @sql = CONCAT('ALTER TABLE `', p_table, '` MODIFY COLUMN `', p_column, '` ', p_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('Modified column: ', p_table, '.', p_column) AS result;
    ELSE
        SELECT CONCAT('Column not found: ', p_table, '.', p_column) AS result;
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- 第2部分：修复 sys_user 表（核心用户表）
-- ============================================================

-- 重命名现有字段以匹配代码模型
ALTER TABLE sys_user CHANGE COLUMN created_time created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';
ALTER TABLE sys_user CHANGE COLUMN update_time updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- 补全缺失字段
CALL safe_add_column('sys_user', 'email', 'VARCHAR(100) DEFAULT NULL COMMENT "邮箱"', 'phone');
CALL safe_add_column('sys_user', 'avatar', 'VARCHAR(255) DEFAULT NULL COMMENT "头像URL"', 'email');
CALL safe_add_column('sys_user', 'role_id', 'BIGINT DEFAULT NULL COMMENT "角色ID"', 'avatar');
CALL safe_add_column('sys_user', 'department', 'VARCHAR(50) DEFAULT NULL COMMENT "部门"', 'role_id');
CALL safe_add_column('sys_user', 'position', 'VARCHAR(50) DEFAULT NULL COMMENT "职位"', 'department');
CALL safe_add_column('sys_user', 'last_login_time', 'DATETIME DEFAULT NULL COMMENT "最后登录时间"', 'status');
CALL safe_add_column('sys_user', 'last_login_ip', 'VARCHAR(50) DEFAULT NULL COMMENT "最后登录IP"', 'last_login_time');
CALL safe_add_column('sys_user', 'created_by', 'BIGINT DEFAULT NULL COMMENT "创建人ID"', 'updated_at');

-- 添加约束
ALTER TABLE sys_user 
    MODIFY COLUMN username VARCHAR(50) NOT NULL COMMENT '用户名',
    MODIFY COLUMN password VARCHAR(255) NOT NULL COMMENT '密码',
    MODIFY COLUMN real_name VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
    MODIFY COLUMN phone VARCHAR(20) DEFAULT NULL COMMENT '电话',
    MODIFY COLUMN status INT DEFAULT 1 NOT NULL COMMENT '状态:0禁用1启用',
    MODIFY COLUMN is_deleted INT DEFAULT 0 NOT NULL COMMENT '是否删除:0否1是',
    ADD CONSTRAINT chk_sys_user_status CHECK (status IN (0, 1)),
    ADD CONSTRAINT chk_sys_user_is_deleted CHECK (is_deleted IN (0, 1));

-- 添加索引
CALL safe_add_index('sys_user', 'idx_username', 'username');
CALL safe_add_index('sys_user', 'idx_status', 'status');
CALL safe_add_index('sys_user', 'idx_role_id', 'role_id');

-- ============================================================
-- 第3部分：创建/完善 sys_role 表
-- ============================================================

CREATE TABLE IF NOT EXISTS sys_role (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '角色ID',
    role_name VARCHAR(50) NOT NULL COMMENT '角色名称',
    role_code VARCHAR(50) NOT NULL COMMENT '角色编码',
    description VARCHAR(255) DEFAULT NULL COMMENT '描述',
    permissions JSON DEFAULT NULL COMMENT '权限列表',
    status INT DEFAULT 1 NOT NULL COMMENT '状态:0禁用1启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_role_code (role_code),
    CONSTRAINT chk_sys_role_status CHECK (status IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统角色表';

-- 初始化默认角色
INSERT IGNORE INTO sys_role (id, role_name, role_code, description, permissions, status) VALUES
(1, '超级管理员', 'admin', '系统超级管理员，拥有所有权限', '["*"]', 1),
(2, '维修技师', 'technician', '维修技师，可处理工单', '["workorder:view","workorder:edit"]', 1),
(3, '财务人员', 'finance', '财务人员，可管理财务', '["finance:view","finance:edit"]', 1),
(4, '库管员', 'warehouse', '库管员，可管理库存', '["inventory:view","inventory:edit"]', 1);

-- ============================================================
-- 第4部分：创建 sys_permission 和 sys_role_permission 表
-- ============================================================

CREATE TABLE IF NOT EXISTS sys_permission (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '权限ID',
    name VARCHAR(50) NOT NULL COMMENT '权限名称',
    code VARCHAR(100) NOT NULL COMMENT '权限编码',
    type INT DEFAULT 1 COMMENT '类型:1菜单2按钮3接口',
    parent_id BIGINT DEFAULT 0 COMMENT '父级ID',
    path VARCHAR(255) DEFAULT NULL COMMENT '路径',
    icon VARCHAR(50) DEFAULT NULL COMMENT '图标',
    sort_order INT DEFAULT 0 COMMENT '排序',
    status INT DEFAULT 1 COMMENT '状态:0禁用1启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_permission_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统权限表';

CREATE TABLE IF NOT EXISTS sys_role_permission (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_id BIGINT NOT NULL COMMENT '角色ID',
    permission_id BIGINT NOT NULL COMMENT '权限ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_role_permission (role_id, permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';

-- ============================================================
-- 第5部分：修复 base_customer 表（客户表）
-- ============================================================

-- 重命名字段
ALTER TABLE base_customer CHANGE COLUMN create_time created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';
ALTER TABLE base_customer CHANGE COLUMN update_time updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- 补全缺失字段
CALL safe_add_column('base_customer', 'customer_code', 'VARCHAR(50) DEFAULT NULL COMMENT "客户编码"', 'id');
CALL safe_add_column('base_customer', 'customer_type', 'INT DEFAULT 1 COMMENT "客户类型:1个人2企业"', 'customer_name');
CALL safe_add_column('base_customer', 'pinyin_code', 'VARCHAR(100) DEFAULT NULL COMMENT "拼音简码"', 'customer_name');
CALL safe_add_column('base_customer', 'contact_name', 'VARCHAR(50) DEFAULT NULL COMMENT "联系人"', 'customer_type');
CALL safe_add_column('base_customer', 'phone2', 'VARCHAR(20) DEFAULT NULL COMMENT "备用电话"', 'phone');
CALL safe_add_column('base_customer', 'discount_rate', 'DECIMAL(5,2) DEFAULT 100.00 COMMENT "折扣率%"', 'address');
CALL safe_add_column('base_customer', 'credit_limit', 'DECIMAL(15,2) DEFAULT 0.00 COMMENT "信用额度"', 'discount_rate');
CALL safe_add_column('base_customer', 'tax_number', 'VARCHAR(50) DEFAULT NULL COMMENT "税号"', 'credit_limit');
CALL safe_add_column('base_customer', 'bank_name', 'VARCHAR(100) DEFAULT NULL COMMENT "开户行"', 'tax_number');
CALL safe_add_column('base_customer', 'bank_account', 'VARCHAR(50) DEFAULT NULL COMMENT "银行账号"', 'bank_name');
CALL safe_add_column('base_customer', 'total_sales_amount', 'DECIMAL(15,2) DEFAULT 0.00 COMMENT "累计消费金额"', 'remark');
CALL safe_add_column('base_customer', 'total_sales_count', 'INT DEFAULT 0 COMMENT "累计消费次数"', 'total_sales_amount');
CALL safe_add_column('base_customer', 'last_sales_date', 'DATE DEFAULT NULL COMMENT "最后消费日期"', 'total_sales_count');

-- 添加约束
ALTER TABLE base_customer
    MODIFY COLUMN customer_name VARCHAR(100) NOT NULL COMMENT '客户名称',
    MODIFY COLUMN phone VARCHAR(20) DEFAULT NULL COMMENT '电话',
    MODIFY COLUMN status INT DEFAULT 1 NOT NULL COMMENT '状态:0删除1正常',
    ADD CONSTRAINT chk_base_customer_status CHECK (status IN (0, 1)),
    ADD CONSTRAINT chk_base_customer_type CHECK (customer_type IN (1, 2));

-- 添加索引
CALL safe_add_index('base_customer', 'idx_customer_name', 'customer_name');
CALL safe_add_index('base_customer', 'idx_customer_phone', 'phone');
CALL safe_add_index('base_customer', 'idx_customer_status', 'status');

-- ============================================================
-- 第6部分：修复 base_supplier 表（供应商表）
-- ============================================================

-- 重命名字段
ALTER TABLE base_supplier CHANGE COLUMN create_time created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';
ALTER TABLE base_supplier CHANGE COLUMN update_time updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- 补全缺失字段
CALL safe_add_column('base_supplier', 'supplier_code', 'VARCHAR(50) DEFAULT NULL COMMENT "供应商编码"', 'id');
CALL safe_add_column('base_supplier', 'pinyin_code', 'VARCHAR(100) DEFAULT NULL COMMENT "拼音简码"', 'supplier_name');
CALL safe_add_column('base_supplier', 'contact_name', 'VARCHAR(50) DEFAULT NULL COMMENT "联系人"', 'supplier_name');
CALL safe_add_column('base_supplier', 'tax_number', 'VARCHAR(50) DEFAULT NULL COMMENT "税号"', 'address');
CALL safe_add_column('base_supplier', 'bank_name', 'VARCHAR(100) DEFAULT NULL COMMENT "开户行"', 'tax_number');
CALL safe_add_column('base_supplier', 'bank_account', 'VARCHAR(50) DEFAULT NULL COMMENT "银行账号"', 'bank_name');
CALL safe_add_column('base_supplier', 'is_repair_partner', 'INT DEFAULT 0 COMMENT "是否维修合作方:0否1是"', 'bank_account');
CALL safe_add_column('base_supplier', 'repair_types', 'JSON DEFAULT NULL COMMENT "可维修类型"', 'is_repair_partner');
CALL safe_add_column('base_supplier', 'total_purchase_amount', 'DECIMAL(15,2) DEFAULT 0.00 COMMENT "累计采购金额"', 'remark');
CALL safe_add_column('base_supplier', 'total_purchase_count', 'INT DEFAULT 0 COMMENT "累计采购次数"', 'total_purchase_amount');
CALL safe_add_column('base_supplier', 'total_repair_amount', 'DECIMAL(15,2) DEFAULT 0.00 COMMENT "累计维修金额"', 'total_purchase_count');
CALL safe_add_column('base_supplier', 'total_repair_count', 'INT DEFAULT 0 COMMENT "累计维修次数"', 'total_repair_amount');

-- 添加约束
ALTER TABLE base_supplier
    MODIFY COLUMN supplier_name VARCHAR(100) NOT NULL COMMENT '供应商名称',
    MODIFY COLUMN status INT DEFAULT 1 NOT NULL COMMENT '状态:0删除1正常',
    ADD CONSTRAINT chk_base_supplier_status CHECK (status IN (0, 1));

-- 添加索引
CALL safe_add_index('base_supplier', 'idx_supplier_name', 'supplier_name');
CALL safe_add_index('base_supplier', 'idx_is_repair_partner', 'is_repair_partner');

-- ============================================================
-- 第7部分：修复 product_info 表（商品表）
-- ============================================================

-- 重命名字段
ALTER TABLE product_info CHANGE COLUMN create_time created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';
ALTER TABLE product_info CHANGE COLUMN update_time updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- 补全缺失字段
CALL safe_add_column('product_info', 'barcode', 'VARCHAR(50) DEFAULT NULL COMMENT "条形码"', 'product_code');
CALL safe_add_column('product_info', 'pinyin_code', 'VARCHAR(200) DEFAULT NULL COMMENT "拼音简码"', 'product_name');
CALL safe_add_column('product_info', 'category_name', 'VARCHAR(50) DEFAULT NULL COMMENT "分类名称"', 'category_id');
CALL safe_add_column('product_info', 'sub_unit_id', 'BIGINT DEFAULT NULL COMMENT "辅助单位ID"', 'unit_id');
CALL safe_add_column('product_info', 'sub_unit_rate', 'DECIMAL(10,4) DEFAULT 1.0000 COMMENT "换算率"', 'sub_unit_id');
CALL safe_add_column('product_info', 'wholesale_price', 'DECIMAL(15,4) DEFAULT 0.0000 COMMENT "批发价"', 'member_price');
CALL safe_add_column('product_info', 'customer_price', 'DECIMAL(15,4) DEFAULT 0.0000 COMMENT "客户价"', 'wholesale_price');
CALL safe_add_column('product_info', 'weight', 'DECIMAL(10,3) DEFAULT NULL COMMENT "重量kg"', 'max_stock');
CALL safe_add_column('product_info', 'volume', 'DECIMAL(10,3) DEFAULT NULL COMMENT "体积m³"', 'weight');
CALL safe_add_column('product_info', 'shelf_life', 'INT DEFAULT NULL COMMENT "保质期天数"', 'volume');
CALL safe_add_column('product_info', 'is_serial', 'INT DEFAULT 0 COMMENT "是否序列号管理:0否1是"', 'shelf_life');
CALL safe_add_column('product_info', 'is_batch', 'INT DEFAULT 0 COMMENT "是否批次管理:0否1是"', 'is_serial');
CALL safe_add_column('product_info', 'is_assembly', 'INT DEFAULT 0 COMMENT "是否组装件:0否1是"', 'is_batch');
CALL safe_add_column('product_info', 'is_gift', 'INT DEFAULT 0 COMMENT "是否赠品:0否1是"', 'is_assembly');
CALL safe_add_column('product_info', 'no_cost', 'INT DEFAULT 0 COMMENT "是否不计成本:0否1是"', 'is_gift');
CALL safe_add_column('product_info', 'no_stock', 'INT DEFAULT 0 COMMENT "是否不计库存:0否1是"', 'no_cost');

-- 添加约束
ALTER TABLE product_info
    MODIFY COLUMN product_code VARCHAR(50) NOT NULL COMMENT '商品编码',
    MODIFY COLUMN product_name VARCHAR(200) NOT NULL COMMENT '商品名称',
    MODIFY COLUMN purchase_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '采购价',
    MODIFY COLUMN sale_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '销售价',
    MODIFY COLUMN cost_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '成本价',
    MODIFY COLUMN current_stock INT DEFAULT 0 COMMENT '当前库存',
    MODIFY COLUMN status INT DEFAULT 1 NOT NULL COMMENT '状态:0删除1正常',
    ADD CONSTRAINT chk_product_info_status CHECK (status IN (0, 1)),
    ADD CONSTRAINT chk_product_info_price CHECK (purchase_price >= 0 AND sale_price >= 0 AND cost_price >= 0),
    ADD CONSTRAINT chk_product_info_stock CHECK (current_stock >= 0);

-- 添加索引
CALL safe_add_index('product_info', 'idx_product_code', 'product_code');
CALL safe_add_index('product_info', 'idx_product_name', 'product_name');
CALL safe_add_index('product_info', 'idx_category_id', 'category_id');
CALL safe_add_index('product_info', 'idx_barcode', 'barcode');
CALL safe_add_index('product_info', 'idx_status', 'status');

-- ============================================================
-- 第8部分：创建 product_category 表（商品分类）
-- ============================================================

CREATE TABLE IF NOT EXISTS product_category (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
    category_name VARCHAR(50) NOT NULL COMMENT '分类名称',
    parent_id BIGINT DEFAULT 0 COMMENT '父级ID,0为顶级',
    sort_order INT DEFAULT 0 COMMENT '排序',
    status INT DEFAULT 1 COMMENT '状态:0禁用1启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_parent_id (parent_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';

-- 初始化默认分类
INSERT IGNORE INTO product_category (id, category_name, parent_id, sort_order) VALUES
(1, '手机配件', 0, 1),
(2, '屏幕', 1, 1),
(3, '电池', 1, 2),
(4, '外壳', 1, 3),
(5, '电脑配件', 0, 2),
(6, '其他配件', 0, 3);

-- ============================================================
-- 第9部分：修复 work_order 表（工单表）- 核心业务表
-- ============================================================

-- 重命名字段
ALTER TABLE work_order CHANGE COLUMN create_time created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';
ALTER TABLE work_order CHANGE COLUMN update_time updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- 补全缺失字段
CALL safe_add_column('work_order', 'wo_type', 'VARCHAR(50) DEFAULT NULL COMMENT "工单类型"', 'wo_no');
CALL safe_add_column('work_order', 'customer_id', 'BIGINT DEFAULT NULL COMMENT "客户ID"', 'customer_name');
CALL safe_add_column('work_order', 'customer_phone', 'VARCHAR(20) DEFAULT NULL COMMENT "客户电话"', 'customer_name');
CALL safe_add_column('work_order', 'device_type', 'VARCHAR(50) DEFAULT NULL COMMENT "设备类型"', 'customer_phone');
CALL safe_add_column('work_order', 'device_brand', 'VARCHAR(50) DEFAULT NULL COMMENT "设备品牌"', 'device_type');
CALL safe_add_column('work_order', 'device_model', 'VARCHAR(100) DEFAULT NULL COMMENT "设备型号"', 'device_brand');
CALL safe_add_column('work_order', 'device_sn', 'VARCHAR(100) DEFAULT NULL COMMENT "序列号"', 'device_model');
CALL safe_add_column('work_order', 'device_imei', 'VARCHAR(50) DEFAULT NULL COMMENT "IMEI"', 'device_sn');
CALL safe_add_column('work_order', 'device_password', 'VARCHAR(100) DEFAULT NULL COMMENT "设备密码"', 'device_imei');
CALL safe_add_column('work_order', 'appearance_desc', 'TEXT DEFAULT NULL COMMENT "外观描述"', 'fault_desc');
CALL safe_add_column('work_order', 'accessories', 'TEXT DEFAULT NULL COMMENT "随机配件"', 'appearance_desc');
CALL safe_add_column('work_order', 'labor_cost', 'DECIMAL(15,2) DEFAULT 0.00 COMMENT "人工费"', 'status');
CALL safe_add_column('work_order', 'parts_cost', 'DECIMAL(15,2) DEFAULT 0.00 COMMENT "配件费"', 'labor_cost');
CALL safe_add_column('work_order', 'total_cost', 'DECIMAL(15,2) DEFAULT 0.00 COMMENT "总费用"', 'parts_cost');
CALL safe_add_column('work_order', 'settlement_status', 'INT DEFAULT 0 COMMENT "结算状态:0未结算1已结算"', 'total_cost');
CALL safe_add_column('work_order', 'settlement_account_id', 'BIGINT DEFAULT NULL COMMENT "结算账户ID"', 'settlement_status');
CALL safe_add_column('work_order', 'settlement_time', 'DATETIME DEFAULT NULL COMMENT "结算时间"', 'settlement_account_id');
CALL safe_add_column('work_order', 'assigned_user_id', 'BIGINT DEFAULT NULL COMMENT "指派技师ID"', 'settlement_time');
CALL safe_add_column('work_order', 'assigned_time', 'DATETIME DEFAULT NULL COMMENT "指派时间"', 'assigned_user_id');
CALL safe_add_column('work_order', 'delivery_type', 'INT DEFAULT 0 COMMENT "送修方式:0本店1外送"', 'assigned_time');
CALL safe_add_column('work_order', 'external_repair', 'INT DEFAULT 0 COMMENT "是否外送修:0否1是"', 'delivery_type');
CALL safe_add_column('work_order', 'external_shop', 'VARCHAR(100) DEFAULT NULL COMMENT "外送店铺"', 'external_repair');
CALL safe_add_column('work_order', 'external_quote', 'DECIMAL(15,2) DEFAULT NULL COMMENT "外送报价"', 'external_shop');
CALL safe_add_column('work_order', 'external_status', 'INT DEFAULT 0 COMMENT "外送状态"', 'external_quote');
CALL safe_add_column('work_order', 'customer_confirmed', 'INT DEFAULT 0 COMMENT "客户确认:0否1是"', 'external_status');
CALL safe_add_column('work_order', 'confirmed_time', 'DATETIME DEFAULT NULL COMMENT "确认时间"', 'customer_confirmed');
CALL safe_add_column('work_order', 'abnormal_remark', 'TEXT DEFAULT NULL COMMENT "异常备注"', 'confirmed_time');
CALL safe_add_column('work_order', 'barcode', 'VARCHAR(100) DEFAULT NULL COMMENT "条码"', 'abnormal_remark');
CALL safe_add_column('work_order', 'receive_order_id', 'BIGINT DEFAULT NULL COMMENT "关联接件单ID"', 'barcode');
CALL safe_add_column('work_order', 'priority', 'INT DEFAULT 0 COMMENT "优先级:0-3"', 'receive_order_id');
CALL safe_add_column('work_order', 'estimated_time', 'DATETIME DEFAULT NULL COMMENT "预计完成时间"', 'priority');
CALL safe_add_column('work_order', 'actual_time', 'DATETIME DEFAULT NULL COMMENT "实际完成时间"', 'estimated_time');
CALL safe_add_column('work_order', 'created_by', 'BIGINT DEFAULT NULL COMMENT "创建人ID"', 'updated_at');

-- 添加约束
ALTER TABLE work_order
    MODIFY COLUMN wo_no VARCHAR(50) NOT NULL COMMENT '工单编号',
    MODIFY COLUMN customer_name VARCHAR(100) DEFAULT NULL COMMENT '客户名称',
    MODIFY COLUMN fault_desc TEXT DEFAULT NULL COMMENT '故障描述',
    MODIFY COLUMN status INT DEFAULT 0 NOT NULL COMMENT '状态:0待接单1已接单2派单中3处理中4待配件5待审核6配件待入库7维修中8待结算9已完成10已取消',
    MODIFY COLUMN labor_cost DECIMAL(15,2) DEFAULT 0.00 COMMENT '人工费',
    MODIFY COLUMN parts_cost DECIMAL(15,2) DEFAULT 0.00 COMMENT '配件费',
    MODIFY COLUMN total_cost DECIMAL(15,2) DEFAULT 0.00 COMMENT '总费用',
    ADD CONSTRAINT chk_work_order_status CHECK (status BETWEEN 0 AND 10),
    ADD CONSTRAINT chk_work_order_cost CHECK (labor_cost >= 0 AND parts_cost >= 0 AND total_cost >= 0),
    ADD CONSTRAINT chk_work_order_settlement CHECK (settlement_status IN (0, 1));

-- 添加索引
CALL safe_add_index('work_order', 'idx_wo_no', 'wo_no');
CALL safe_add_index('work_order', 'idx_customer_id', 'customer_id');
CALL safe_add_index('work_order', 'idx_customer_phone', 'customer_phone');
CALL safe_add_index('work_order', 'idx_status', 'status');
CALL safe_add_index('work_order', 'idx_wo_type', 'wo_type');
CALL safe_add_index('work_order', 'idx_assigned_user_id', 'assigned_user_id');
CALL safe_add_index('work_order', 'idx_created_at', 'created_at');

-- ============================================================
-- 第10部分：创建 work_order_part 表（工单配件明细）
-- ============================================================

CREATE TABLE IF NOT EXISTS work_order_part (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    wo_id BIGINT NOT NULL COMMENT '工单ID',
    product_id BIGINT DEFAULT NULL COMMENT '商品ID',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '商品名称',
    product_code VARCHAR(50) DEFAULT NULL COMMENT '商品编码',
    quantity DECIMAL(10,3) DEFAULT 1.000 COMMENT '数量',
    unit_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '单价',
    total_price DECIMAL(15,2) DEFAULT 0.00 COMMENT '总价',
    cost_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '成本价',
    is_own INT DEFAULT 1 COMMENT '是否本店配件:0客户自带1本店',
    status INT DEFAULT 0 COMMENT '状态:0待用1已用2已退',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_wo_id (wo_id),
    INDEX idx_product_id (product_id),
    CONSTRAINT chk_wop_quantity CHECK (quantity > 0),
    CONSTRAINT chk_wop_price CHECK (unit_price >= 0 AND total_price >= 0),
    CONSTRAINT chk_wop_is_own CHECK (is_own IN (0, 1)),
    CONSTRAINT chk_wop_status CHECK (status IN (0, 1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单配件明细表';

-- ============================================================
-- 第11部分：创建 work_order_log 表（工单操作日志）
-- ============================================================

CREATE TABLE IF NOT EXISTS work_order_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    wo_id BIGINT NOT NULL COMMENT '工单ID',
    action VARCHAR(50) NOT NULL COMMENT '操作动作',
    old_status INT DEFAULT NULL COMMENT '原状态',
    new_status INT DEFAULT NULL COMMENT '新状态',
    content TEXT DEFAULT NULL COMMENT '操作内容',
    operator_id BIGINT DEFAULT NULL COMMENT '操作人ID',
    operator_name VARCHAR(50) DEFAULT NULL COMMENT '操作人姓名',
    ip_address VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_wo_id (wo_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单操作日志表';

-- ============================================================
-- 第12部分：创建 receive_order 表（接件单）
-- ============================================================

CREATE TABLE IF NOT EXISTS receive_order (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '接件单ID',
    receive_no VARCHAR(50) NOT NULL COMMENT '接件单号',
    customer_id BIGINT DEFAULT NULL COMMENT '客户ID',
    customer_name VARCHAR(100) DEFAULT NULL COMMENT '客户名称',
    customer_phone VARCHAR(20) DEFAULT NULL COMMENT '客户电话',
    receive_type INT DEFAULT 1 COMMENT '接件类型:1本店修2外送修',
    external_shop_id BIGINT DEFAULT NULL COMMENT '外送供应商ID',
    external_shop_name VARCHAR(100) DEFAULT NULL COMMENT '外送供应商名称',
    status INT DEFAULT 0 COMMENT '状态:0待处理1已接单2已派单3维修中4待结算5已完成6已取消',
    total_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '总金额',
    paid_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '已付金额',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    UNIQUE KEY uk_receive_no (receive_no),
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status),
    INDEX idx_receive_type (receive_type),
    CONSTRAINT chk_ro_status CHECK (status BETWEEN 0 AND 6),
    CONSTRAINT chk_ro_amount CHECK (total_amount >= 0 AND paid_amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接件单表';

-- ============================================================
-- 第13部分：创建 receive_order_device 表（接件单设备明细）
-- ============================================================

CREATE TABLE IF NOT EXISTS receive_order_device (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    receive_order_id BIGINT NOT NULL COMMENT '接件单ID',
    device_archive_id BIGINT DEFAULT NULL COMMENT '设备档案ID',
    device_type VARCHAR(50) DEFAULT NULL COMMENT '设备类型',
    device_brand VARCHAR(50) DEFAULT NULL COMMENT '品牌',
    device_model VARCHAR(100) DEFAULT NULL COMMENT '型号',
    device_sn VARCHAR(100) DEFAULT NULL COMMENT '序列号',
    device_imei VARCHAR(50) DEFAULT NULL COMMENT 'IMEI',
    fault_desc TEXT DEFAULT NULL COMMENT '故障描述',
    appearance_desc TEXT DEFAULT NULL COMMENT '外观描述',
    accessories TEXT DEFAULT NULL COMMENT '随机配件',
    work_order_id BIGINT DEFAULT NULL COMMENT '关联工单ID',
    status INT DEFAULT 0 COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_receive_order_id (receive_order_id),
    INDEX idx_work_order_id (work_order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接件单设备明细表';

-- ============================================================
-- 第14部分：创建 device_archive 表（设备档案）
-- ============================================================

CREATE TABLE IF NOT EXISTS device_archive (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '档案ID',
    device_code VARCHAR(50) DEFAULT NULL COMMENT '设备编码',
    customer_id BIGINT DEFAULT NULL COMMENT '客户ID',
    device_type VARCHAR(50) DEFAULT NULL COMMENT '设备类型',
    device_brand VARCHAR(50) DEFAULT NULL COMMENT '品牌',
    device_model VARCHAR(100) DEFAULT NULL COMMENT '型号',
    device_sn VARCHAR(100) DEFAULT NULL COMMENT '序列号',
    device_imei VARCHAR(50) DEFAULT NULL COMMENT 'IMEI',
    purchase_date DATE DEFAULT NULL COMMENT '购买日期',
    warranty_expire DATE DEFAULT NULL COMMENT '保修到期日',
    remark TEXT DEFAULT NULL COMMENT '备注',
    repair_count INT DEFAULT 0 COMMENT '维修次数',
    last_repair_date DATE DEFAULT NULL COMMENT '最后维修日期',
    status INT DEFAULT 1 COMMENT '状态:0删除1正常',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_device_code (device_code),
    INDEX idx_customer_id (customer_id),
    INDEX idx_device_sn (device_sn),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备档案表';

-- ============================================================
-- 第15部分：修复 inventory_stock 表（库存明细）
-- ============================================================

-- 重命名字段
ALTER TABLE inventory_stock CHANGE COLUMN create_time created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';
ALTER TABLE inventory_stock CHANGE COLUMN update_time updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- 补全缺失字段
CALL safe_add_column('inventory_stock', 'warehouse_id', 'BIGINT DEFAULT 1 COMMENT "仓库ID"', 'product_name');
CALL safe_add_column('inventory_stock', 'warehouse_name', 'VARCHAR(50) DEFAULT "主仓库" COMMENT "仓库名称"', 'warehouse_id');
CALL safe_add_column('inventory_stock', 'frozen_quantity', 'DECIMAL(10,3) DEFAULT 0.000 COMMENT "冻结数量"', 'quantity');
CALL safe_add_column('inventory_stock', 'available_quantity', 'DECIMAL(10,3) GENERATED ALWAYS AS (quantity - frozen_quantity) STORED COMMENT "可用数量"', 'frozen_quantity');
CALL safe_add_column('inventory_stock', 'batch_no', 'VARCHAR(50) DEFAULT NULL COMMENT "批次号"', 'cost_price');
CALL safe_add_column('inventory_stock', 'serial_no', 'VARCHAR(100) DEFAULT NULL COMMENT "序列号"', 'batch_no');

-- 添加约束
ALTER TABLE inventory_stock
    MODIFY COLUMN product_id BIGINT NOT NULL COMMENT '商品ID',
    MODIFY COLUMN quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '库存数量',
    MODIFY COLUMN cost_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '成本价',
    ADD CONSTRAINT chk_inventory_stock_quantity CHECK (quantity >= 0),
    ADD CONSTRAINT chk_inventory_stock_frozen CHECK (frozen_quantity >= 0 AND frozen_quantity <= quantity),
    ADD CONSTRAINT chk_inventory_stock_cost CHECK (cost_price >= 0);

-- 添加索引
CALL safe_add_index('inventory_stock', 'idx_product_id', 'product_id');
CALL safe_add_index('inventory_stock', 'idx_warehouse_id', 'warehouse_id');
CALL safe_add_index('inventory_stock', 'idx_batch_no', 'batch_no');

-- ============================================================
-- 第16部分：创建 inventory_in 表（入库单）
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_in (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '入库单ID',
    in_no VARCHAR(50) NOT NULL COMMENT '入库单号',
    in_type INT DEFAULT 1 COMMENT '入库类型:1采购入库2退货入库3调拨入库4组装入库5其他入库',
    supplier_id BIGINT DEFAULT NULL COMMENT '供应商ID',
    supplier_name VARCHAR(100) DEFAULT NULL COMMENT '供应商名称',
    warehouse_id BIGINT DEFAULT 1 COMMENT '仓库ID',
    warehouse_name VARCHAR(50) DEFAULT '主仓库' COMMENT '仓库名称',
    total_quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '总数量',
    total_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '总金额',
    status INT DEFAULT 0 COMMENT '状态:0待审核1已审核2已入库',
    auditor_id BIGINT DEFAULT NULL COMMENT '审核人ID',
    auditor_name VARCHAR(50) DEFAULT NULL COMMENT '审核人姓名',
    audit_time DATETIME DEFAULT NULL COMMENT '审核时间',
    remark TEXT DEFAULT NULL COMMENT '备注',
    related_order_id BIGINT DEFAULT NULL COMMENT '关联单据ID',
    related_order_no VARCHAR(50) DEFAULT NULL COMMENT '关联单据号',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    UNIQUE KEY uk_in_no (in_no),
    INDEX idx_supplier_id (supplier_id),
    INDEX idx_status (status),
    INDEX idx_in_type (in_type),
    CONSTRAINT chk_inventory_in_status CHECK (status IN (0, 1, 2)),
    CONSTRAINT chk_inventory_in_amount CHECK (total_amount >= 0),
    CONSTRAINT chk_inventory_in_quantity CHECK (total_quantity >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库单表';

-- ============================================================
-- 第17部分：创建 inventory_in_item 表（入库单明细）
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_in_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    in_id BIGINT NOT NULL COMMENT '入库单ID',
    product_id BIGINT DEFAULT NULL COMMENT '商品ID',
    product_code VARCHAR(50) DEFAULT NULL COMMENT '商品编码',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '商品名称',
    specification VARCHAR(100) DEFAULT NULL COMMENT '规格',
    unit_name VARCHAR(20) DEFAULT NULL COMMENT '单位',
    quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '数量',
    unit_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '单价',
    total_price DECIMAL(15,2) DEFAULT 0.00 COMMENT '总价',
    cost_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '成本价',
    batch_no VARCHAR(50) DEFAULT NULL COMMENT '批次号',
    serial_no VARCHAR(100) DEFAULT NULL COMMENT '序列号',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_in_id (in_id),
    INDEX idx_product_id (product_id),
    CONSTRAINT chk_in_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_in_item_price CHECK (unit_price >= 0 AND total_price >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库单明细表';

-- ============================================================
-- 第18部分：创建 inventory_out 表（出库单）
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_out (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '出库单ID',
    out_no VARCHAR(50) NOT NULL COMMENT '出库单号',
    out_type INT DEFAULT 1 COMMENT '出库类型:1销售出库2维修领料3调拨出库4拆卸出库5其他出库',
    customer_id BIGINT DEFAULT NULL COMMENT '客户ID',
    customer_name VARCHAR(100) DEFAULT NULL COMMENT '客户名称',
    warehouse_id BIGINT DEFAULT 1 COMMENT '仓库ID',
    warehouse_name VARCHAR(50) DEFAULT '主仓库' COMMENT '仓库名称',
    total_quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '总数量',
    total_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '总金额',
    status INT DEFAULT 0 COMMENT '状态:0待审核1已审核2已出库',
    auditor_id BIGINT DEFAULT NULL COMMENT '审核人ID',
    auditor_name VARCHAR(50) DEFAULT NULL COMMENT '审核人姓名',
    audit_time DATETIME DEFAULT NULL COMMENT '审核时间',
    remark TEXT DEFAULT NULL COMMENT '备注',
    related_order_id BIGINT DEFAULT NULL COMMENT '关联单据ID',
    related_order_no VARCHAR(50) DEFAULT NULL COMMENT '关联单据号',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    UNIQUE KEY uk_out_no (out_no),
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status),
    INDEX idx_out_type (out_type),
    CONSTRAINT chk_inventory_out_status CHECK (status IN (0, 1, 2)),
    CONSTRAINT chk_inventory_out_amount CHECK (total_amount >= 0),
    CONSTRAINT chk_inventory_out_quantity CHECK (total_quantity >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库单表';

-- ============================================================
-- 第19部分：创建 inventory_out_item 表（出库单明细）
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_out_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    out_id BIGINT NOT NULL COMMENT '出库单ID',
    product_id BIGINT DEFAULT NULL COMMENT '商品ID',
    product_code VARCHAR(50) DEFAULT NULL COMMENT '商品编码',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '商品名称',
    specification VARCHAR(100) DEFAULT NULL COMMENT '规格',
    unit_name VARCHAR(20) DEFAULT NULL COMMENT '单位',
    quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '数量',
    unit_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '单价',
    total_price DECIMAL(15,2) DEFAULT 0.00 COMMENT '总价',
    cost_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '成本价',
    batch_no VARCHAR(50) DEFAULT NULL COMMENT '批次号',
    serial_no VARCHAR(100) DEFAULT NULL COMMENT '序列号',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_out_id (out_id),
    INDEX idx_product_id (product_id),
    CONSTRAINT chk_out_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_out_item_price CHECK (unit_price >= 0 AND total_price >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库单明细表';

-- ============================================================
-- 第20部分：创建 inventory_check 表（盘点单）
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_check (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '盘点单ID',
    check_no VARCHAR(50) NOT NULL COMMENT '盘点单号',
    warehouse_id BIGINT DEFAULT 1 COMMENT '仓库ID',
    warehouse_name VARCHAR(50) DEFAULT '主仓库' COMMENT '仓库名称',
    check_date DATE DEFAULT NULL COMMENT '盘点日期',
    status INT DEFAULT 0 COMMENT '状态:0待盘点1盘点中2已完成',
    total_quantity INT DEFAULT 0 COMMENT '商品数量',
    diff_quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '差异数量',
    diff_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '差异金额',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    UNIQUE KEY uk_check_no (check_no),
    INDEX idx_warehouse_id (warehouse_id),
    INDEX idx_status (status),
    CONSTRAINT chk_inventory_check_status CHECK (status IN (0, 1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点单表';

-- ============================================================
-- 第21部分：创建 inventory_check_item 表（盘点单明细）
-- ============================================================

CREATE TABLE IF NOT EXISTS inventory_check_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    check_id BIGINT NOT NULL COMMENT '盘点单ID',
    product_id BIGINT DEFAULT NULL COMMENT '商品ID',
    product_code VARCHAR(50) DEFAULT NULL COMMENT '商品编码',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '商品名称',
    specification VARCHAR(100) DEFAULT NULL COMMENT '规格',
    unit_name VARCHAR(20) DEFAULT NULL COMMENT '单位',
    system_quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '系统库存',
    actual_quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '实际库存',
    diff_quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '差异',
    cost_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '成本价',
    diff_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '差异金额',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_check_id (check_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点单明细表';

-- ============================================================
-- 第22部分：创建 transfer_order 表（调拨单）
-- ============================================================

CREATE TABLE IF NOT EXISTS transfer_order (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '调拨单ID',
    transfer_no VARCHAR(50) NOT NULL COMMENT '调拨单号',
    from_warehouse_id BIGINT DEFAULT NULL COMMENT '调出仓库ID',
    from_warehouse_name VARCHAR(50) DEFAULT NULL COMMENT '调出仓库名称',
    to_warehouse_id BIGINT DEFAULT NULL COMMENT '调入仓库ID',
    to_warehouse_name VARCHAR(50) DEFAULT NULL COMMENT '调入仓库名称',
    total_quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '总数量',
    status INT DEFAULT 0 COMMENT '状态:0待审核1已审核2已完成',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    UNIQUE KEY uk_transfer_no (transfer_no),
    INDEX idx_status (status),
    CONSTRAINT chk_transfer_status CHECK (status IN (0, 1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='调拨单表';

-- ============================================================
-- 第23部分：创建 transfer_order_item 表（调拨单明细）
-- ============================================================

CREATE TABLE IF NOT EXISTS transfer_order_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    transfer_id BIGINT NOT NULL COMMENT '调拨单ID',
    product_id BIGINT DEFAULT NULL COMMENT '商品ID',
    product_code VARCHAR(50) DEFAULT NULL COMMENT '商品编码',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '商品名称',
    specification VARCHAR(100) DEFAULT NULL COMMENT '规格',
    unit_name VARCHAR(20) DEFAULT NULL COMMENT '单位',
    quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '数量',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_transfer_id (transfer_id),
    INDEX idx_product_id (product_id),
    CONSTRAINT chk_transfer_item_quantity CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='调拨单明细表';

-- ============================================================
-- 第24部分：创建 assemble_order 表（组装单）
-- ============================================================

CREATE TABLE IF NOT EXISTS assemble_order (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '组装单ID',
    assemble_no VARCHAR(50) NOT NULL COMMENT '组装单号',
    product_id BIGINT DEFAULT NULL COMMENT '成品商品ID',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '成品名称',
    quantity DECIMAL(10,3) DEFAULT 1.000 COMMENT '组装数量',
    warehouse_id BIGINT DEFAULT 1 COMMENT '仓库ID',
    warehouse_name VARCHAR(50) DEFAULT '主仓库' COMMENT '仓库名称',
    status INT DEFAULT 0 COMMENT '状态:0待审核1已审核2已完成',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    UNIQUE KEY uk_assemble_no (assemble_no),
    INDEX idx_status (status),
    CONSTRAINT chk_assemble_status CHECK (status IN (0, 1, 2)),
    CONSTRAINT chk_assemble_quantity CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组装单表';

-- ============================================================
-- 第25部分：创建 assemble_order_item 表（组装单明细）
-- ============================================================

CREATE TABLE IF NOT EXISTS assemble_order_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    assemble_id BIGINT NOT NULL COMMENT '组装单ID',
    product_id BIGINT DEFAULT NULL COMMENT '子件商品ID',
    product_code VARCHAR(50) DEFAULT NULL COMMENT '子件编码',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '子件名称',
    specification VARCHAR(100) DEFAULT NULL COMMENT '规格',
    unit_name VARCHAR(20) DEFAULT NULL COMMENT '单位',
    quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '数量',
    cost_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '成本价',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_assemble_id (assemble_id),
    INDEX idx_product_id (product_id),
    CONSTRAINT chk_assemble_item_quantity CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组装单明细表';

-- ============================================================
-- 第26部分：创建 pre_order 表（预订单）
-- ============================================================

CREATE TABLE IF NOT EXISTS pre_order (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '预订单ID',
    pre_no VARCHAR(50) NOT NULL COMMENT '预订单号',
    pre_type INT DEFAULT 1 COMMENT '预订类型:1采购预定2销售预定',
    customer_id BIGINT DEFAULT NULL COMMENT '客户ID',
    customer_name VARCHAR(100) DEFAULT NULL COMMENT '客户名称',
    supplier_id BIGINT DEFAULT NULL COMMENT '供应商ID',
    supplier_name VARCHAR(100) DEFAULT NULL COMMENT '供应商名称',
    total_quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '总数量',
    total_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '总金额',
    status INT DEFAULT 0 COMMENT '状态:0待处理1已转单2已取消',
    related_order_id BIGINT DEFAULT NULL COMMENT '关联单据ID',
    related_order_no VARCHAR(50) DEFAULT NULL COMMENT '关联单据号',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    UNIQUE KEY uk_pre_no (pre_no),
    INDEX idx_status (status),
    INDEX idx_pre_type (pre_type),
    CONSTRAINT chk_pre_status CHECK (status IN (0, 1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预订单表';

-- ============================================================
-- 第27部分：创建 pre_order_item 表（预订单明细）
-- ============================================================

CREATE TABLE IF NOT EXISTS pre_order_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    pre_id BIGINT NOT NULL COMMENT '预订单ID',
    product_id BIGINT DEFAULT NULL COMMENT '商品ID',
    product_code VARCHAR(50) DEFAULT NULL COMMENT '商品编码',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '商品名称',
    quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '数量',
    unit_price DECIMAL(15,4) DEFAULT 0.0000 COMMENT '单价',
    total_price DECIMAL(15,2) DEFAULT 0.00 COMMENT '总价',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_pre_id (pre_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预订单明细表';

-- ============================================================
-- 第28部分：创建 cost_adjust 表（成本调价单）
-- ============================================================

CREATE TABLE IF NOT EXISTS cost_adjust (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '调价单ID',
    adjust_no VARCHAR(50) NOT NULL COMMENT '调价单号',
    product_id BIGINT DEFAULT NULL COMMENT '商品ID',
    product_code VARCHAR(50) DEFAULT NULL COMMENT '商品编码',
    product_name VARCHAR(200) DEFAULT NULL COMMENT '商品名称',
    old_cost DECIMAL(15,4) DEFAULT 0.0000 COMMENT '原成本',
    new_cost DECIMAL(15,4) DEFAULT 0.0000 COMMENT '新成本',
    quantity DECIMAL(10,3) DEFAULT 0.000 COMMENT '数量',
    diff_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '差异金额',
    status INT DEFAULT 0 COMMENT '状态:0待审核1已审核',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    UNIQUE KEY uk_adjust_no (adjust_no),
    INDEX idx_status (status),
    CONSTRAINT chk_cost_adjust_status CHECK (status IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成本调价单表';

-- ============================================================
-- 第29部分：创建 wo_type 表（工单类型）
-- ============================================================

CREATE TABLE IF NOT EXISTS wo_type (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '类型ID',
    type_name VARCHAR(50) NOT NULL COMMENT '类型名称',
    type_code VARCHAR(50) NOT NULL COMMENT '类型编码',
    default_labor_cost DECIMAL(15,2) DEFAULT 0.00 COMMENT '默认人工费',
    estimated_days INT DEFAULT 1 COMMENT '预计天数',
    sort_order INT DEFAULT 0 COMMENT '排序',
    status INT DEFAULT 1 COMMENT '状态:0禁用1启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_type_code (type_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单类型表';

-- 初始化工单类型
INSERT IGNORE INTO wo_type (id, type_name, type_code, default_labor_cost, estimated_days, sort_order) VALUES
(1, '手机维修', 'phone', 50.00, 1, 1),
(2, '电脑维修', 'computer', 80.00, 2, 2),
(3, '平板维修', 'tablet', 60.00, 1, 3),
(4, '其他维修', 'other', 30.00, 1, 4);

-- ============================================================
-- 第30部分：创建 project 表（维修项目）
-- ============================================================

CREATE TABLE IF NOT EXISTS project (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '项目ID',
    project_name VARCHAR(100) NOT NULL COMMENT '项目名称',
    project_code VARCHAR(50) DEFAULT NULL COMMENT '项目编码',
    category VARCHAR(50) DEFAULT NULL COMMENT '维修类别',
    default_price DECIMAL(15,2) DEFAULT 0.00 COMMENT '默认价格',
    estimated_hours DECIMAL(5,1) DEFAULT 1.0 COMMENT '预计工时',
    remark TEXT DEFAULT NULL COMMENT '备注',
    status INT DEFAULT 1 COMMENT '状态:0禁用1启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_project_code (project_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维修项目表';

-- ============================================================
-- 第31部分：创建 finance_account 表（财务账户）
-- ============================================================

CREATE TABLE IF NOT EXISTS finance_account (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '账户ID',
    account_name VARCHAR(50) NOT NULL COMMENT '账户名称',
    account_type INT DEFAULT 1 COMMENT '账户类型:1现金2银行3支付宝4微信',
    account_no VARCHAR(50) DEFAULT NULL COMMENT '账号',
    balance DECIMAL(15,2) DEFAULT 0.00 COMMENT '余额',
    status INT DEFAULT 1 COMMENT '状态:0禁用1启用',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_account_type (account_type),
    INDEX idx_status (status),
    CONSTRAINT chk_finance_account_type CHECK (account_type IN (1, 2, 3, 4)),
    CONSTRAINT chk_finance_account_balance CHECK (balance >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务账户表';

-- 初始化默认财务账户
INSERT IGNORE INTO finance_account (id, account_name, account_type, balance) VALUES
(1, '现金', 1, 0.00),
(2, '银行账户', 2, 0.00),
(3, '微信', 4, 0.00),
(4, '支付宝', 3, 0.00);

-- ============================================================
-- 第32部分：创建 finance_record 表（财务流水）
-- ============================================================

CREATE TABLE IF NOT EXISTS finance_record (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '流水ID',
    account_id BIGINT DEFAULT NULL COMMENT '账户ID',
    account_name VARCHAR(50) DEFAULT NULL COMMENT '账户名称',
    record_type INT DEFAULT 1 COMMENT '类型:1收入2支出',
    amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '金额',
    balance_before DECIMAL(15,2) DEFAULT 0.00 COMMENT '变动前余额',
    balance_after DECIMAL(15,2) DEFAULT 0.00 COMMENT '变动后余额',
    related_type VARCHAR(50) DEFAULT NULL COMMENT '关联类型',
    related_id BIGINT DEFAULT NULL COMMENT '关联ID',
    related_no VARCHAR(50) DEFAULT NULL COMMENT '关联单号',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by BIGINT DEFAULT NULL COMMENT '操作人ID',
    INDEX idx_account_id (account_id),
    INDEX idx_record_type (record_type),
    INDEX idx_related (related_type, related_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT chk_finance_record_type CHECK (record_type IN (1, 2)),
    CONSTRAINT chk_finance_record_amount CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务流水表';

-- ============================================================
-- 第33部分：创建 finance_invoice 表（发票管理）
-- ============================================================

CREATE TABLE IF NOT EXISTS finance_invoice (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '发票ID',
    invoice_no VARCHAR(50) DEFAULT NULL COMMENT '发票号码',
    invoice_type INT DEFAULT 1 COMMENT '发票类型:1普通发票2增值税发票',
    customer_id BIGINT DEFAULT NULL COMMENT '客户ID',
    customer_name VARCHAR(100) DEFAULT NULL COMMENT '客户名称',
    amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '金额',
    tax_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '税额',
    total_amount DECIMAL(15,2) DEFAULT 0.00 COMMENT '价税合计',
    status INT DEFAULT 0 COMMENT '状态:0待开票1已开票',
    related_type VARCHAR(50) DEFAULT NULL COMMENT '关联类型',
    related_id BIGINT DEFAULT NULL COMMENT '关联ID',
    related_no VARCHAR(50) DEFAULT NULL COMMENT '关联单号',
    remark TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by BIGINT DEFAULT NULL COMMENT '创建人ID',
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status),
    INDEX idx_related (related_type, related_id),
    CONSTRAINT chk_invoice_type CHECK (invoice_type IN (1, 2)),
    CONSTRAINT chk_invoice_status CHECK (status IN (0, 1)),
    CONSTRAINT chk_invoice_amount CHECK (amount >= 0 AND tax_amount >= 0 AND total_amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票管理表';

-- ============================================================
-- 第34部分：创建 operation_log 表（操作日志）
-- ============================================================

CREATE TABLE IF NOT EXISTS operation_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_id BIGINT DEFAULT NULL COMMENT '用户ID',
    user_name VARCHAR(50) DEFAULT NULL COMMENT '用户名',
    module VARCHAR(50) DEFAULT NULL COMMENT '模块',
    action VARCHAR(50) DEFAULT NULL COMMENT '操作',
    target_type VARCHAR(50) DEFAULT NULL COMMENT '目标类型',
    target_id BIGINT DEFAULT NULL COMMENT '目标ID',
    content TEXT DEFAULT NULL COMMENT '操作内容',
    ip_address VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
    user_agent VARCHAR(500) DEFAULT NULL COMMENT '用户代理',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_module (module),
    INDEX idx_target (target_type, target_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- ============================================================
-- 第35部分：创建 print_template 表（打印模板）
-- ============================================================

CREATE TABLE IF NOT EXISTS print_template (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '模板ID',
    template_name VARCHAR(50) NOT NULL COMMENT '模板名称',
    template_type VARCHAR(50) DEFAULT NULL COMMENT '模板类型:work_order/invoice/receipt',
    template_content TEXT DEFAULT NULL COMMENT '模板内容',
    paper_size VARCHAR(20) DEFAULT 'A4' COMMENT '纸张尺寸',
    is_default INT DEFAULT 0 COMMENT '是否默认:0否1是',
    status INT DEFAULT 1 COMMENT '状态:0禁用1启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_template_type (template_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='打印模板表';

-- ============================================================
-- 第36部分：初始化默认管理员用户
-- ============================================================

-- 检查并创建默认管理员
INSERT IGNORE INTO sys_user (id, username, password, real_name, role_id, status, is_deleted) 
VALUES (1, 'admin', 'pbkdf2:sha256:600000$...', '系统管理员', 1, 1, 0);

-- 如果密码不对，更新为默认密码 123456
-- 注意：实际密码需要用 werkzeug 生成，这里先占位

-- ============================================================
-- 第37部分：清理存储过程
-- ============================================================

DROP PROCEDURE IF EXISTS safe_add_column;
DROP PROCEDURE IF EXISTS safe_add_index;
DROP PROCEDURE IF EXISTS safe_modify_column;

-- ============================================================
-- 完成
-- ============================================================

SET FOREIGN_KEY_CHECKS = 1;

SELECT '数据库重构完成！所有表结构已完善，约束已添加，索引已创建，初始化数据已插入。' AS result;
