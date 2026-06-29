"""Setup 端点：仅在 sys_user 为空时可调用，用于创建初始管理员。"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash

from extensions import db  # noqa: F401  - 实际路径在 backend/extensions.py，运行时通过 sys.path 解析

bp = Blueprint('setup', __name__)


@bp.route('/init', methods=['POST'])
def init_admin():
    """创建初始管理员。仅当数据库为空且 SETUP_ENABLED=true 时可用。"""
    if not current_app.config.get('SETUP_ENABLED', False):
        return jsonify({'code': 403, 'message': 'setup 已禁用'}), 403

    from models.system import SysUser
    if db.session.query(SysUser).count() > 0:
        return jsonify({'code': 400, 'message': '管理员已存在，请走正常注册流程'}), 400

    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if len(username) < 3:
        return jsonify({'code': 400, 'message': '用户名至少 3 个字符'}), 400
    if len(password) < 8:
        return jsonify({'code': 400, 'message': '密码至少 8 个字符'}), 400

    user = SysUser(
        username=username,
        password=generate_password_hash(password),
        real_name=data.get('real_name', username),
        status=1,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'code': 200, 'message': '管理员创建成功', 'data': {'id': user.id}}), 200


@bp.route('/status', methods=['GET'])
def setup_status():
    """查询系统是否需要初始化（前端首次访问时判断是否引导到 setup 页）。"""
    from models.system import SysUser
    needs_setup = db.session.query(SysUser).count() == 0
    return jsonify({
        'code': 200,
        'message': 'ok',
        'data': {
            'needs_setup': needs_setup,
            'setup_enabled': current_app.config.get('SETUP_ENABLED', False),
        },
    }), 200