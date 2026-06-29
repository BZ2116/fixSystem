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

    # 数据库
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    # pymysql 专属参数（sqlite 测试不需要）
    if SQLALCHEMY_DATABASE_URI.startswith('mysql'):
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
            'charset': 'utf8mb4',
            'init_command': "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
        }

    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

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