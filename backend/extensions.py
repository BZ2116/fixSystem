"""
扩展实例，单例。在 create_app 中通过 init_app 绑定。

放在 backend/ 根目录（不是 backend/app/）是为了避免与项目根的 app.py
发生命名冲突。同时让 models 子包可以用 `from extensions import db` 直接导入。
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_talisman import Talisman
import redis

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()
talisman = Talisman()

# Redis 连接池（在 create_app 中初始化）
redis_client: redis.Redis = None  # type: ignore


def init_redis(url: str):
    global redis_client
    redis_client = redis.from_url(url, decode_responses=True)
    return redis_client