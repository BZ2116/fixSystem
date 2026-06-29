"""
端到端蓝图测试：验证所有蓝图都已正确注册、路由可达、JWT 守卫按预期工作。

覆盖：
1. 所有 23 个蓝图都已被 register_blueprints 加载
2. 总路由数 >= 250（防止遗漏迁移）
3. 未授权请求访问受保护端点 → 401
4. 公开端点（health / setup/status）→ 200
5. 主要 URL 前缀集合（按业务域）都已注册

运行：cd backend && pytest tests/test_blueprints.py -v
"""
import pytest


EXPECTED_BLUEPRINTS = {
    'setup', 'health', 'auth', 'user', 'users_admin',
    'customer', 'supplier', 'product', 'product_unit', 'product_category',
    'device', 'quote', 'office', 'dashboard',
    'inventory', 'purchase', 'sales',
    'workorder', 'workorder_actions',
    'receive', 'receive_actions',
    'dispatch', 'asset', 'finance', 'reconciliation',
    'salary', 'expense', 'statistics',
    'settings', 'log', 'preorder', 'return_order',
}


URL_PREFIXES = [
    '/api/health',
    '/api/setup/status',
    '/api/auth',
    '/api/customers',
    '/api/suppliers',
    '/api/products',
    '/api/devices',
    '/api/quotes',
    '/api/offices',
    '/api/dashboard',
    '/api/inventory/stock',
    '/api/purchase/orders',
    '/api/sales/orders',
    '/api/workorders',
    '/api/receiveorders',
    '/api/dispatch',
    '/api/assets',
    '/api/asset/types',
    '/api/finance/accounts',
    '/api/finance/receivables',
    '/api/finance/payables',
    '/api/invoices',
    '/api/reconciliation/customer',
    '/api/salary',
    '/api/expense',
    '/api/statistics/revenue',
    '/api/settings/users',
    '/api/settings/roles',
    '/api/pre-orders',
    '/api/return-orders',
]


@pytest.fixture
def app():
    from app import create_app
    from extensions import db
    app = create_app('testing')
    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_all_expected_blueprints_registered(app):
    """所有期望的蓝图都已注册到 Flask app。"""
    registered = {bp.name for bp in app.blueprints.values()}
    missing = EXPECTED_BLUEPRINTS - registered
    assert not missing, f"未注册的蓝图: {missing}"


def test_route_count_above_threshold(app):
    """总路由数应 >= 250（防止遗漏迁移）。"""
    rules = list(app.url_map.iter_rules())
    assert len(rules) >= 250, f"路由数偏低: {len(rules)}"


@pytest.mark.parametrize('url', URL_PREFIXES)
def test_url_prefix_registered(app, url):
    """主要 URL 前缀都已被注册为路由。"""
    rules = [str(r) for r in app.url_map.iter_rules()]

    def matches(rule: str) -> bool:
        if rule == url:
            return True
        # 处理路径参数：/api/assets/<int:id> 应匹配 /api/assets
        if rule.startswith(url + '/'):
            return True
        return False

    assert any(matches(r) for r in rules), f"URL 前缀 {url} 未注册"


def test_health_endpoint_public(client):
    """/api/health 不需要 JWT。"""
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['code'] == 200


def test_setup_status_public(client):
    """/api/setup/status 不需要 JWT。"""
    res = client.get('/api/setup/status')
    assert res.status_code == 200


@pytest.mark.parametrize('protected_url,method', [
    ('/api/customers', 'GET'),
    ('/api/suppliers', 'GET'),
    ('/api/products', 'GET'),
    ('/api/devices', 'GET'),
    ('/api/quotes', 'GET'),
    ('/api/offices', 'GET'),
    ('/api/inventory/stock', 'GET'),
    ('/api/purchase/orders', 'GET'),
    ('/api/sales/orders', 'GET'),
    ('/api/workorders', 'GET'),
    ('/api/receiveorders', 'GET'),
    ('/api/asset/types', 'GET'),
    ('/api/assets', 'GET'),
    ('/api/finance/accounts', 'GET'),
    ('/api/finance/receivables', 'GET'),
    ('/api/finance/payables', 'GET'),
    ('/api/invoices', 'GET'),
    ('/api/reconciliation/customer', 'GET'),
    ('/api/salary', 'GET'),
    ('/api/expense', 'GET'),
    ('/api/statistics/revenue', 'GET'),
    ('/api/settings/users', 'GET'),
    ('/api/pre-orders', 'GET'),
    ('/api/return-orders', 'GET'),
])
def test_protected_endpoint_requires_auth(client, protected_url, method):
    """未带 token 访问受保护端点 → 401。"""
    res = client.open(protected_url, method=method)
    assert res.status_code == 401, f"{method} {protected_url} 返回 {res.status_code}，期望 401"
    data = res.get_json()
    assert data['code'] == 401


def test_diagnose_encoding_route_removed(app):
    """调试路由 /api/diagnose-encoding 已被删除。"""
    rules = [str(r) for r in app.url_map.iter_rules()]
    assert '/api/diagnose-encoding' not in rules


def test_fix_encoding_route_removed(app):
    """调试路由 /api/fix-encoding 已被删除。"""
    rules = [str(r) for r in app.url_map.iter_rules()]
    assert '/api/fix-encoding' not in rules


def test_404_returns_json(client):
    """未知端点返回 JSON 格式 404。"""
    res = client.get('/api/this-route-does-not-exist')
    assert res.status_code == 404
    data = res.get_json()
    assert data['code'] == 404
    assert 'request_id' in data
