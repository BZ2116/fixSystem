"""认证：登录、注册。"""
from datetime import datetime

import bcrypt
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from app.utils import ok, fail

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return fail('用户名和密码不能为空', code=400)

    from models.system import SysUser
    user = SysUser.query.filter_by(username=username, status=1, is_deleted=0).first()

    # 支持 bcrypt 和 werkzeug 两种密码哈希格式
    password_valid = False
    if user:
        if user.password.startswith('$2'):
            # bcrypt 格式
            password_valid = bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))
        else:
            # werkzeug pbkdf2 格式
            password_valid = check_password_hash(user.password, password)

    if not user or not password_valid:
        return fail('用户名或密码错误', code=401)

    # 更新登录信息
    user.last_login_time = datetime.now()
    user.last_login_ip = request.remote_addr
    db.session.commit()

    # 生成JWT令牌
    access_token = create_access_token(identity=str(user.id))

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
                # 超级管理员，返回所有权限code
                all_perms = SysPermission.query.filter_by(status=1).all()
                permissions = [p.code for p in all_perms]
            else:
                permissions = perms

    return ok({
        'token': access_token,
        'userInfo': {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'avatar': user.avatar,
            'role_id': user.role_id,
            'role_name': role_name,
            'role_code': role_code,
            'permissions': permissions,
            'role': {
                'role_name': role_name,
                'role_code': role_code,
                'permissions': permissions
            }
        }
    }, '登录成功')


@bp.route('/register', methods=['POST'])
@jwt_required()
def register():
    """用户注册（需要管理员权限）"""
    claims = get_jwt()
    user_perms = claims.get('permissions', []) if hasattr(claims, 'get') else []
    if '*' not in user_perms and 'user:add' not in user_perms:
        return fail('无权限创建用户', code=403)
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    real_name = data.get('real_name')

    if not username or not password:
        return fail('用户名和密码不能为空', code=400)
    if len(password) < 8:
        return fail('密码至少 8 个字符', code=400)

    from models.system import SysUser
    existing_user = SysUser.query.filter_by(username=username).first()
    if existing_user:
        return fail('用户名已存在', code=400)

    hashed_password = generate_password_hash(password)
    new_user = SysUser(
        username=username,
        password=hashed_password,
        real_name=real_name
    )

    db.session.add(new_user)
    db.session.commit()

    return ok({'id': new_user.id}, '注册成功')
