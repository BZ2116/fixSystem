"""
安全相关：JWT 配置、token 黑名单、文件上传白名单。

2026-06-30: JWT 黑名单从 Redis 迁移到 SQLite jwt_blacklist 表。
"""
import os
from datetime import datetime
from uuid import uuid4
from flask import jsonify, g, request

# extensions 在 backend/ 根目录（不在 backend/app/ 下）
from extensions import jwt, db

REVOKED_JTI_KEY = 'jwt:revoked:{}'  # 保留兼容旧 import；新逻辑使用 SQL 表


def configure_jwt(jwt_instance):
    """注册 JWT 回调：撤销检查、错误响应。"""

    @jwt_instance.token_in_blocklist_loader
    def check_revoked(_jwt_header, jwt_payload):
        """从 SQLite jwt_blacklist 表查询。"""
        jti = jwt_payload.get('jti')
        if not jti:
            return False
        try:
            row = db.session.execute(
                db.text(
                    'SELECT 1 FROM jwt_blacklist '
                    'WHERE jti = :jti AND expires_at > :now'
                ),
                {'jti': jti, 'now': datetime.now()},
            ).first()
            return row is not None
        except Exception:
            return False

    @jwt_instance.revoked_token_loader
    def revoked_response(_jwt_header, _jwt_payload):
        return jsonify({'code': 401, 'message': '登录已失效，请重新登录'}), 401

    @jwt_instance.expired_token_loader
    def expired_response(_jwt_header, _jwt_payload):
        return jsonify({'code': 401, 'message': '登录已过期，请重新登录'}), 401

    @jwt_instance.unauthorized_loader
    def missing_token_response(reason):
        return jsonify({'code': 401, 'message': '未登录或登录已过期'}), 401

    @jwt_instance.invalid_token_loader
    def invalid_token_response(reason):
        return jsonify({'code': 401, 'message': 'token 无效'}), 401


def revoke_token(jwt_payload: dict):
    """把 jti 写入 SQLite jwt_blacklist；过期由 token exp 决定。"""
    jti = jwt_payload.get('jti')
    exp = jwt_payload.get('exp')
    if not jti:
        return
    expires_at = (
        datetime.fromtimestamp(exp) if exp
        else datetime.now()
    )
    try:
        db.session.execute(
            db.text(
                'INSERT OR IGNORE INTO jwt_blacklist (jti, expires_at) '
                'VALUES (:jti, :exp)'
            ),
            {'jti': jti, 'exp': expires_at},
        )
        db.session.commit()
    except Exception:
        db.session.rollback()


def cleanup_expired_blacklist():
    """清理已过期的黑名单条目（启动时 + 每日调用）。"""
    try:
        db.session.execute(
            db.text('DELETE FROM jwt_blacklist WHERE expires_at < :now'),
            {'now': datetime.now()},
        )
        db.session.commit()
    except Exception:
        db.session.rollback()


# ===================== 文件上传白名单 =====================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'xlsx', 'xls', 'csv'}
ALLOWED_MIME = {
    'image/png', 'image/jpeg', 'image/gif',
    'application/pdf',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
}

# 文件 magic number（前 4-8 字节）
MAGIC_SIGNATURES = [
    (b'\x89PNG\r\n\x1a\n', 'png'),
    (b'\xff\xd8\xff', 'jpg'),  # JPEG
    (b'GIF87a', 'gif'),
    (b'GIF89a', 'gif'),
    (b'%PDF', 'pdf'),
    (b'PK\x03\x04', 'xlsx'),  # ZIP / OOXML
    (b'\xd0\xcf\x11\xe0', 'xls'),  # OLE2
]


def safe_save(file_storage, target_dir: str) -> str:
    """安全保存上传文件，返回保存的文件名。

    校验：
    1. 扩展名白名单
    2. MIME 白名单
    3. 文件内容 magic number
    4. UUID 重命名（避免路径穿越）
    """
    if not file_storage or file_storage.filename == '':
        raise ValueError('empty file')

    ext = file_storage.filename.rsplit('.', 1)[-1].lower() if '.' in file_storage.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f'extension not allowed: {ext}')

    mimetype = (file_storage.mimetype or '').lower()
    if mimetype not in ALLOWED_MIME:
        raise ValueError(f'mime not allowed: {mimetype}')

    head = file_storage.stream.read(8)
    file_storage.stream.seek(0)
    if not _match_magic(head, ext):
        raise ValueError('file content does not match extension')

    safe_name = f'{uuid4().hex}.{ext}'
    os.makedirs(target_dir, exist_ok=True)
    file_storage.save(os.path.join(target_dir, safe_name))
    return safe_name


def _match_magic(head: bytes, ext: str) -> bool:
    for sig, sig_ext in MAGIC_SIGNATURES:
        if head.startswith(sig):
            return sig_ext == ext
    return False


# ===================== 权限装饰器 =====================

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def permission(*required_codes: str):
    """权限装饰器：要求 JWT claims 中包含指定 permission code。"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_perms = claims.get('permissions', [])
            if '*' in user_perms:
                return fn(*args, **kwargs)
            if not any(code in user_perms for code in required_codes):
                return jsonify({'code': 403, 'message': '无权限'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_id() -> int:
    """从 JWT claims 取当前用户 ID。"""
    from flask_jwt_extended import get_jwt_identity
    return get_jwt_identity()


def get_current_user():
    """取当前用户对象。"""
    from models.system import SysUser
    uid = get_current_user_id()
    return SysUser.query.get(uid) if uid else None