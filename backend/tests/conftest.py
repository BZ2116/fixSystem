"""pytest 配置：在 session 启动时注入测试用环境变量，避免每个测试都手动设置。

Config 类在类体里读 os.environ（无 fallback），所以必须在导入 app.* 之前
设置 JWT_SECRET_KEY/DATABASE_URL/REDIS_URL。
"""
import os


def pytest_configure(config):
    os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-for-pytest-only')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
    os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
    os.environ.setdefault('CORS_ORIGINS', 'http://localhost')
    os.environ.setdefault('FLASK_ENV', 'testing')
    os.environ.setdefault('SETUP_ENABLED', 'false')