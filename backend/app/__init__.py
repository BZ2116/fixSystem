"""
应用工厂 create_app
"""
import uuid
import logging
from flask import Flask, g, request

from .config import get_config
# 注意：extensions 在 backend/ 根目录（不在 backend/app/ 下，避免与项目根的 app.py 命名冲突）
# 通过 sys.path 解析：cwd=backend/ 时直接是顶级；cwd=source-code/ 时由 app.py 注入
from extensions import db, migrate, cors, jwt, talisman
from .errors import register_error_handlers
from .security import configure_jwt

logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """创建 Flask 应用实例。

    Args:
        config_name: 'development' / 'production' / 'testing'，默认读 FLASK_ENV
    """
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # 每个请求生成 request_id，便于日志追踪
    @app.before_request
    def _attach_request_id():
        g.request_id = request.headers.get('X-Request-ID', uuid.uuid4().hex)

    @app.after_request
    def _expose_request_id(response):
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        return response

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    cors.init_app(
        app,
        resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}},
        supports_credentials=True,
    )

    # JWT 黑名单使用 SQLite jwt_blacklist 表（无需 Redis）

    if app.config.get('TALISMAN_ENABLED', False):
        talisman.init_app(app, **app.config['TALISMAN_OPTIONS'])

    configure_jwt(jwt)
    jwt.init_app(app)  # 注册 JWTManager，触发默认值（cookie name、CSRF 等）
    register_error_handlers(app)

    # 业务路由
    from .blueprints import register_blueprints
    register_blueprints(app)

    # 启动时清理过期 JWT 黑名单
    with app.app_context():
        from .security import cleanup_expired_blacklist
        cleanup_expired_blacklist()

    # 初始化种子（仅空库时）
    with app.app_context():
        from .seed import run_seeds_if_empty
        run_seeds_if_empty()

    logger.info('app created (env=%s)', config_name or app.config.get('ENV', 'unknown'))
    return app