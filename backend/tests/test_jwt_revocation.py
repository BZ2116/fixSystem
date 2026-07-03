"""
回归测试：JWT 撤销 (C1) + 登录下发 cookie (C2)。

C1: 撤销 token 时必须把 revoked_at 写入 jwt_blacklist，
    否则 logout 后用旧 token/cookie 仍能访问受保护端点。
C2: 登录必须 set_access_cookies，否则 cookie-only 模式下后续请求 401。
"""
import os
import pytest

os.environ['FLASK_ENV'] = 'testing'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-jwt-revocation-only'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['CORS_ORIGINS'] = 'http://localhost'


@pytest.fixture
def app():
    from app import create_app
    from extensions import db
    from werkzeug.security import generate_password_hash
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # jwt_blacklist 没有 SQLAlchemy model，需手动建表（init.sql 里定义）
        db.session.execute(db.text(
            'CREATE TABLE IF NOT EXISTS jwt_blacklist ('
            '  jti TEXT PRIMARY KEY,'
            '  revoked_at DATETIME NOT NULL,'
            '  expires_at DATETIME NOT NULL'
            ')'
        ))
        db.session.commit()
        # 用原生 SQL 插入，避免 BigInteger 主键在 SQLite 下不自增的限制
        # （系统预存问题，与本次修复无关；用 INTEGER 列绕过）
        db.session.execute(db.text(
            'INSERT INTO sys_user (id, username, password, real_name, status, is_deleted) '
            'VALUES (1, :u, :p, :n, 1, 0)'
        ), {
            'u': 'admin',
            'p': generate_password_hash('admin123'),
            'n': '测试管理员',
        })
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, username='admin', password='admin123'):
    return client.post(
        '/api/auth/login',
        json={'username': username, 'password': password},
    )


def test_login_sets_access_cookie(client):
    """C2 回归：登录响应必须包含 access_token_cookie。"""
    res = _login(client)
    assert res.status_code == 200, res.get_data(as_text=True)
    body = res.get_json()
    assert body['code'] == 200
    # flask-jwt-extended 默认 cookie 名
    set_cookies = res.headers.getlist('Set-Cookie')
    cookie_names = [c.split('=', 1)[0] for c in set_cookies]
    assert 'access_token_cookie' in cookie_names, (
        f'Set-Cookie 缺少 access_token_cookie，实际: {set_cookies}'
    )
    # 兼容旧前端读取 body.token 的场景
    assert body['data']['token']


def test_cookie_works_for_protected_endpoint(client):
    """C2 回归：拿到 cookie 后访问受保护端点不再 401。"""
    res = _login(client)
    assert res.status_code == 200
    protected = client.get('/api/customers')
    assert protected.status_code != 401, (
        f'带 cookie 仍 401，说明 C2 未真正修复；body={protected.get_data(as_text=True)}'
    )


def test_no_cookie_still_401(client):
    """不带 cookie 访问受保护端点仍应 401（回归保护）。"""
    res = client.get('/api/customers')
    assert res.status_code == 401


def test_logout_revokes_token(client):
    """C1 回归：登出后旧 token 访问受保护端点 → 401 '登录已失效'。

    logout 会同时清除 cookie；这里我们手动从登录响应里取出 token，
    把 access_token_cookie 重新塞进请求来验证它真的进了黑名单
    （而不是单纯因为没 cookie 才 401）。
    """
    res = _login(client)
    assert res.status_code == 200
    body = res.get_json()
    token = body['data']['token']

    access_cookie = client.get_cookie('access_token_cookie')
    csrf_cookie = client.get_cookie('csrf_access_token')
    assert access_cookie is not None and csrf_cookie is not None

    # 登出需要 CSRF header
    logout = client.post(
        '/api/auth/logout',
        headers={'X-CSRF-TOKEN': csrf_cookie.value},
    )
    assert logout.status_code == 200, logout.get_data(as_text=True)

    # 重新挂载旧 token 的 cookie（模拟前端没刷新仍带着旧 cookie 的场景）
    client.set_cookie(
        'localhost', 'access_token_cookie', token,
    )
    post = client.get(
        '/api/customers',
        headers={'X-CSRF-TOKEN': csrf_cookie.value},
    )
    assert post.status_code == 401, post.get_data(as_text=True)
    body = post.get_json()
    assert '登录已失效' in body['message']


def test_revoke_token_writes_revoked_at(app):
    """C1 单元级回归：直接调用 revoke_token 后表中应有 revoked_at。"""
    from datetime import datetime, timedelta
    from app.security import revoke_token
    from extensions import db

    payload = {
        'jti': 'test-jti-revoke-001',
        'exp': (datetime.now() + timedelta(days=1)).timestamp(),
    }
    with app.app_context():
        revoke_token(payload)
        row = db.session.execute(
            db.text(
                'SELECT jti, revoked_at, expires_at FROM jwt_blacklist '
                'WHERE jti = :jti'
            ),
            {'jti': 'test-jti-revoke-001'},
        ).first()
    assert row is not None, '黑名单写入失败（C1 未修复）'
    assert row[1] is not None, 'revoked_at 列为 NULL（C1 未修复）'
    assert row[2] is not None


def test_orm_insert_sys_user_writes_id(app):
    """Regression: db.BigInteger PK must auto-increment on SQLite."""
    from extensions import db
    from models.system import SysUser

    with app.app_context():
        u = SysUser(
            username='orm_insert_test',
            password='x',
            real_name='ORM',
            role_id=1,
        )
        db.session.add(u)
        db.session.commit()
        assert u.id is not None and u.id > 0, f'PK not populated: id={u.id}'
        fetched = SysUser.query.get(u.id)
        assert fetched is not None
        assert fetched.username == 'orm_insert_test'