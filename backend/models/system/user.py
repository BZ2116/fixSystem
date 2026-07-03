from datetime import datetime

from extensions import db
from .._base import BigIntPK


class SysUser(db.Model):
    """系统用户"""
    __tablename__ = 'sys_user'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    avatar = db.Column(db.String(255))
    role_id = db.Column(BigIntPK)
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    base_salary = db.Column(db.Numeric(15, 2), default=0.00)  # 基本工资
    status = db.Column(db.Integer, default=1)
    last_login_time = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(BigIntPK)
    is_deleted = db.Column(db.Integer, default=0)


class SysRole(db.Model):
    """系统角色"""
    __tablename__ = 'sys_role'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(50), nullable=False)
    role_code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.JSON)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class SysPermission(db.Model):
    """系统权限"""
    __tablename__ = 'sys_permission'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.Integer, default=1)  # 1:菜单 2:按钮 3:接口
    parent_id = db.Column(BigIntPK, default=0)
    path = db.Column(db.String(255))
    icon = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)


class SysRolePermission(db.Model):
    """角色权限关联"""
    __tablename__ = 'sys_role_permission'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    role_id = db.Column(BigIntPK, nullable=False)
    permission_id = db.Column(BigIntPK, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class OperationLog(db.Model):
    """操作日志"""
    __tablename__ = 'operation_log'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    user_id = db.Column(BigIntPK)
    user_name = db.Column(db.String(50))
    module = db.Column(db.String(50))
    action = db.Column(db.String(50))
    target_type = db.Column(db.String(50))
    target_id = db.Column(BigIntPK)
    content = db.Column(db.Text)
    ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)