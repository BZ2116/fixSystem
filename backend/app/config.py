"""
配置类。所有敏感配置从环境变量读取，无 fallback。
"""
import os
from datetime import timedelta


def _required(key: str) -> str:
    """读取必填环境变量，缺失直接抛错（避免静默使用默认值）。"""
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f'缺少必填环境变量: {key}')
    return val


class Config:
    # Flask 基础
    SECRET_KEY = os.environ['JWT_SECRET_KEY']  # 必填，无 fallback
    JSON_AS_ASCII = False
    RESTFUL_JSON = {'ensure_ascii': False, 'charset': 'utf-8'}

    # JWT
    JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = os.environ.get('COOKIE_SAMESITE', 'Lax')
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = True
    JWT_CSRF_HEADER_NAME = 'X-CSRF-TOKEN'

    # 数据库（默认指向 data/repair_system.db；DATABASE_URL 可覆盖）
    _DEFAULT_DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data',
        'repair_system.db',
    )
    # SQLite URI 必须用正斜杠（Windows 反斜杠会被 SQLAlchemy 当成 scheme 分隔符）
    _DEFAULT_DB_URI = 'sqlite:///' + _DEFAULT_DB_PATH.replace('\\', '/')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or _DEFAULT_DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 按方言返回 engine options
    if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {
                'timeout': 5,           # busy_timeout (seconds)
                'check_same_thread': False,
            },
            'pool_pre_ping': True,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        }

    # Redis 已移除（JWT 黑名单改用 SQLite jwt_blacklist 表）
    # 保留 REDIS_URL 配置项以兼容旧 .env；不读取
    REDIS_URL = os.environ.get('REDIS_URL', '')  # 兼容旧 env，实际不使用

    # 上传
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/app/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH_MB', '16')) * 1024 * 1024

    # CORS（白名单，逗号分隔字符串 → 列表）
    _origins = os.environ.get('CORS_ORIGINS', '')
    CORS_ORIGINS = [o.strip() for o in _origins.split(',') if o.strip()]

    # 安全头（默认开启 Talisman）
    TALISMAN_ENABLED = os.environ.get('TALISMAN_ENABLED', 'false').lower() == 'true'
    TALISMAN_OPTIONS = {
        'force_https': False,  # 由 Nginx 处理 HTTPS
        'strict_transport_security': True,
        'content_security_policy': {
            'default-src': "'self'",
            'img-src': ["'self'", 'data:', 'blob:'],
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            'style-src': ["'self'", "'unsafe-inline'"],
        },
    }

    # 分页
    PER_PAGE_DEFAULT = 20
    PER_PAGE_MAX = 200

    # Setup 端点开关
    SETUP_ENABLED = os.environ.get('SETUP_ENABLED', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    JWT_COOKIE_SECURE = False
    TALISMAN_ENABLED = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL',
                                              'sqlite:///:memory:')
    JWT_COOKIE_SECURE = False
    TALISMAN_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


_CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def get_config(name=None):
    name = name or os.environ.get('FLASK_ENV', 'production')
    return _CONFIG_MAP.get(name, ProductionConfig)