"""
扩展实例，单例。在 create_app 中通过 init_app 绑定。

放在 backend/ 根目录（不是 backend/app/）是为了避免与项目根的 app.py
发生命名冲突。同时让 models 子包可以用 `from extensions import db` 直接导入。

2026-06-30: 移除 Redis（已迁移到 SQLite jwt_blacklist 表）。
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_talisman import Talisman

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()
talisman = Talisman()


def init_redis(url: str):  # pragma: no cover
    """保留函数签名以兼容历史 import，但不再创建客户端。

    真实撤销状态保存在 SQLite jwt_blacklist 表。
    """
    import logging
    logging.getLogger(__name__).warning(
        'init_redis() 被调用但已弃用；JWT 黑名单使用 SQLite jwt_blacklist 表。'
    )
    return None
