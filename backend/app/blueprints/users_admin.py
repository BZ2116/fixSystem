"""管理端用户列表。"""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.utils import ok

bp = Blueprint('users_admin', __name__, url_prefix='/api/users')


@bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表（未删除）。"""
    from models.system import SysUser
    users = SysUser.query.filter_by(is_deleted=0).all()
    return ok([{
        'id': u.id,
        'username': u.username,
        'real_name': u.real_name,
        'phone': u.phone,
        'email': u.email,
        'role_id': u.role_id,
        'department': u.department,
        'position': u.position,
        'base_salary': float(u.base_salary) if u.base_salary else 0,
        'status': u.status,
        'last_login_time': u.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if u.last_login_time else None,
    } for u in users])
