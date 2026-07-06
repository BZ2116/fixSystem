"""权限/ownership 辅助函数。

解决技师工作流的两个核心问题：
1. 后端几乎无 ownership 校验 → 技师可看/改任意工单
2. 列表过滤硬编码 'engineer' in role_code → 实际对 technician 角色不生效

设计原则：
- admin/* 通配符：永过
- technician 等"个人角色"：仅看自己 assigned_user_id == self 的工单
- finance/warehouse 等"跨工单角色"：看全部（按 workorder:view 权限）
- 角色判断：用 SysRole.permissions + 角色名约定，不用硬编码 role_code 字符串

待重构：未来若引入 workorder:view-all 权限码，可统一替换本模块的 role_code 判断。
"""
from typing import Optional

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity


# 需要数据隔离的角色（仅看自己 assigned 的数据）
DATA_SCOPED_ROLES = {'technician'}


def claims_to_perms(claims) -> list:
    """从 JWT claims 提取 permissions 列表。"""
    if claims is None or not isinstance(claims, dict):
        return []
    perms = claims.get('permissions') or []
    if perms:
        return perms
    # 旧 token 兼容：claims 缺 permissions 时回退查库
    from flask_jwt_extended import get_jwt_identity
    from models.system import SysUser, SysRole
    uid = get_jwt_identity()
    if uid:
        user = SysUser.query.get(int(uid))
        if user and user.role_id:
            role = SysRole.query.get(user.role_id)
            if role and role.permissions:
                return list(role.permissions)
    return perms


def claims_to_role_code(claims) -> str:
    """从 JWT claims 提取 role_code。"""
    if claims is None:
        return ''
    if isinstance(claims, dict):
        return claims.get('role_code', '') or ''
    return ''


def current_user_id_from_claims(claims) -> Optional[int]:
    """从 JWT claims 取 user_id（sub 字段）。"""
    if claims is None:
        return get_jwt_identity()
    sub = claims.get('sub') if isinstance(claims, dict) else None
    if sub is not None:
        try:
            return int(sub)
        except (TypeError, ValueError):
            return sub
    return get_jwt_identity()


def is_wildcard_admin(perms: list) -> bool:
    """是否通配符 admin。"""
    return '*' in (perms or [])


def is_data_scoped(role_code: str) -> bool:
    """该角色是否需要数据隔离（仅看自己 assigned）。"""
    return (role_code or '').lower() in DATA_SCOPED_ROLES


def filter_visible_workorders(query, claims):
    """按用户角色过滤工单查询。

    - admin/*：不过滤
    - 数据隔离角色（technician）：assigned_user_id == self
    - 其他（finance/warehouse 等）：不过滤（依赖 workorder:view 权限）
    - 无权限：返回空集
    """
    perms = claims_to_perms(claims)
    if is_wildcard_admin(perms):
        return query

    if 'workorder:view' not in perms and 'workorder:edit' not in perms:
        # 无任何工单权限
        from extensions import db
        return query.filter(db.literal(False))

    if is_data_scoped(claims_to_role_code(claims)):
        uid = current_user_id_from_claims(claims)
        from models.workorder import WorkOrder
        return query.filter(WorkOrder.assigned_user_id == uid)

    return query


def filter_visible_receiveorders(query, claims):
    """按用户角色过滤接件单查询。

    规则与工单一致。接件单没有 assigned_user_id，使用 receiver_id。
    """
    perms = claims_to_perms(claims)
    if is_wildcard_admin(perms):
        return query

    if 'receive:view' not in perms and 'receive:edit' not in perms:
        from extensions import db
        return query.filter(db.literal(False))

    if is_data_scoped(claims_to_role_code(claims)):
        uid = current_user_id_from_claims(claims)
        from models.receive import ReceiveOrder
        # 接件单的"数据隔离"按 receiver_id
        return query.filter(ReceiveOrder.receiver_id == uid)

    return query


def _forbidden(message: str = '无权访问该资源'):
    """标准 403 响应。"""
    return jsonify({'code': 403, 'message': message}), 403


def assert_can_view_workorder(order, claims) -> Optional[tuple]:
    """检查用户能否查看该工单。返回 None 表示通过，否则返回 (response, status)。"""
    perms = claims_to_perms(claims)
    if is_wildcard_admin(perms):
        return None
    if 'workorder:view' not in perms and 'workorder:edit' not in perms:
        return _forbidden('无工单查看权限')
    if is_data_scoped(claims_to_role_code(claims)):
        uid = current_user_id_from_claims(claims)
        if order.assigned_user_id != uid:
            return _forbidden('只能查看自己接的工单')
    return None


def assert_can_modify_workorder(order, claims, action: str = 'edit') -> Optional[tuple]:
    """检查用户能否修改该工单。返回 None 表示通过，否则返回 (response, status)。

    action:
    - 'edit': 修改工单字段（需要 workorder:edit + ownership）
    - 'delete': 删除工单（需要 workorder:delete + ownership）
    - 'status': 通用状态变更（需要 workorder:status + ownership；技师应使用 accept/finish/cancel 专用端点）
    - 'settle': 结算（需要 workorder:settle + ownership；生成销售单/应收）
    - 'allocate': 领用配件（需要 workorder:allocate + ownership；生成出库/采购）
    - 'quote': 转报价单（需要 quote:add）
    - 'sales': 转销售单（需要 sales:add）
    - 'dispatch': 派单（需要 dispatch:edit）
    - 'finish': 完工提交（workorder:edit + ownership）
    - 'accept': 接单（workorder:edit + ownership）
    - 'cancel': 取消工单（workorder:edit + ownership）
    """
    perms = claims_to_perms(claims)
    if is_wildcard_admin(perms):
        return None

    required_perm_map = {
        'edit': 'workorder:edit',
        'delete': 'workorder:delete',
        'status': 'workorder:status',
        'settle': 'workorder:settle',
        'allocate': 'workorder:allocate',
        'quote': 'quote:add',
        'sales': 'sales:add',
        'dispatch': 'dispatch:edit',
        'finish': 'workorder:edit',
        'accept': 'workorder:edit',
        'cancel': 'workorder:edit',
    }
    required = required_perm_map.get(action, 'workorder:edit')
    if required not in perms:
        return _forbidden(f'无{action}权限')

    # 数据隔离角色：必须 assigned_user_id == self
    if is_data_scoped(claims_to_role_code(claims)):
        uid = current_user_id_from_claims(claims)
        if order.assigned_user_id != uid:
            return _forbidden('只能修改自己接的工单')

    return None


def assert_can_modify_receiveorder(order, claims, action: str = 'edit') -> Optional[tuple]:
    """检查用户能否修改该接件单。"""
    perms = claims_to_perms(claims)
    if is_wildcard_admin(perms):
        return None

    required_perm_map = {
        'edit': 'receive:edit',
        'delete': 'receive:delete',
    }
    required = required_perm_map.get(action, 'receive:edit')
    if required not in perms:
        return _forbidden(f'无{action}权限')

    if is_data_scoped(claims_to_role_code(claims)):
        uid = current_user_id_from_claims(claims)
        if order.receiver_id != uid:
            return _forbidden('只能修改自己接的接件单')

    return None
