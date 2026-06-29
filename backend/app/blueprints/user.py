"""当前登录用户自己的信息。"""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.utils import ok
from app.security import get_current_user

bp = Blueprint('user', __name__, url_prefix='/api/user')


@bp.route('/info', methods=['GET'])
@jwt_required()
def get_user_info():
    """获取当前用户信息（含角色 + 菜单树）。"""
    user = get_current_user()
    if not user:
        return ok({'code': 404, 'message': '用户不存在'})

    # 获取角色和权限信息
    role_name = ''
    role_code = ''
    permissions = []
    if user.role_id:
        from models.system import SysRole, SysPermission
        role = SysRole.query.get(user.role_id)
        if role:
            role_name = role.role_name
            role_code = role.role_code
            perms = role.permissions if role.permissions else []
            if isinstance(perms, list) and '*' in perms:
                # 超级管理员，返回所有权限 code
                all_perms = SysPermission.query.filter_by(status=1).all()
                permissions = [p.code for p in all_perms]
            else:
                permissions = perms

    # 构建菜单树（type=1 的权限，用户有权限的菜单）
    menus = []
    if permissions:
        from models.system import SysRole as _SR, SysPermission
        all_menu_perms = SysPermission.query.filter_by(type=1, status=1).order_by(SysPermission.sort_order).all()
        role = _SR.query.get(user.role_id)
        role_perms = role.permissions if role else None
        if isinstance(role_perms, list) and '*' in role_perms:
            menu_list = all_menu_perms
        else:
            menu_list = [p for p in all_menu_perms if p.code in permissions]
        menu_dict = {}
        for m in menu_list:
            menu_dict[m.id] = {
                'id': m.id,
                'name': m.name,
                'code': m.code,
                'path': m.path,
                'icon': m.icon,
                'sort_order': m.sort_order,
                'parent_id': m.parent_id,
                'children': []
            }
        for m in menu_list:
            if m.parent_id and m.parent_id in menu_dict:
                menu_dict[m.parent_id]['children'].append(menu_dict[m.id])
        menus = [menu_dict[m.id] for m in menu_list if m.parent_id == 0 or m.parent_id not in menu_dict]
        menus.sort(key=lambda x: x.get('sort_order', 0))

    return ok({
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'phone': user.phone,
        'email': user.email,
        'avatar': user.avatar,
        'role_id': user.role_id,
        'department': user.department,
        'position': user.position,
        'role_name': role_name,
        'role_code': role_code,
        'permissions': permissions,
        'menus': menus,
    })
