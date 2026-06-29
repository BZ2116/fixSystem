"""
冒烟测试：验证应用启动和基础端点。
运行：cd backend && pytest tests/
"""
import os
import pytest

os.environ['FLASK_ENV'] = 'testing'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-testing-only-not-for-prod'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'  # 测试时跳过实际连接
os.environ['CORS_ORIGINS'] = 'http://localhost'


@pytest.fixture
def app():
    from app import create_app
    from extensions import db
    app = create_app('testing')
    with app.app_context():
        db.create_all()  # 测试用内存数据库，建表
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health(client):
    """健康检查端点可访问。"""
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['code'] == 200
    assert data['data']['status'] == 'healthy'


def test_setup_status(client):
    """setup status 端点可访问。"""
    res = client.get('/api/setup/status')
    assert res.status_code == 200


def test_customers_unauthorized(client):
    """未带 cookie 访问业务端点 → 401。阶段 0 customers 蓝图尚未注册，跳过。"""
    res = client.get('/api/customers')
    # 阶段 0：customers blueprint 尚未注册，返回 404
    # 阶段 2 后应改为 401
    assert res.status_code in (401, 404)


def test_404_returns_json(client):
    """未知端点返回 JSON 格式 404。"""
    res = client.get('/api/does-not-exist')
    assert res.status_code == 404
    data = res.get_json()
    assert data['code'] == 404
    assert 'request_id' in data