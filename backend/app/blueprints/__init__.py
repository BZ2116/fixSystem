"""蓝图注册入口。"""
from flask import Flask


def register_blueprints(app: Flask):
    from .setup import bp as setup_bp
    from .health import bp as health_bp
    from .auth import bp as auth_bp
    from .user import bp as user_bp
    from .users_admin import bp as users_admin_bp
    from .customer import bp as customer_bp
    from .supplier import bp as supplier_bp
    from .product import bp as product_bp
    from .product_unit import bp as product_unit_bp
    from .product_category import bp as product_category_bp
    from .device import bp as device_bp
    from .quote import bp as quote_bp
    from .office import bp as office_bp
    from .dashboard import bp as dashboard_bp
    from .inventory import bp as inventory_bp
    app.register_blueprint(setup_bp, url_prefix='/api/setup')
    app.register_blueprint(health_bp)  # /api/health
    app.register_blueprint(auth_bp)  # 自带 url_prefix='/api/auth'
    app.register_blueprint(user_bp)  # 自带 url_prefix='/api/user'
    app.register_blueprint(users_admin_bp)  # 自带 url_prefix='/api/users'
    app.register_blueprint(customer_bp)  # 自带 url_prefix='/api/customers'
    app.register_blueprint(supplier_bp)  # 自带 url_prefix='/api/suppliers'
    app.register_blueprint(product_bp)  # 自带 url_prefix='/api/products'
    app.register_blueprint(product_unit_bp)  # 自带 url_prefix='/api/product/units'
    app.register_blueprint(product_category_bp)  # 自带 url_prefix='/api/product/categories'
    app.register_blueprint(device_bp)  # 自带 url_prefix='/api/devices'
    app.register_blueprint(quote_bp)  # 自带 url_prefix='/api/quotes'
    app.register_blueprint(office_bp)  # 自带 url_prefix='/api/offices'
    app.register_blueprint(dashboard_bp)  # 自带 url_prefix='/api/dashboard'
    # inventory 自带各路由的完整路径（/api/inventory/... / /api/warehouses /api/transfer/... /api/cost-adjusts 等）
    app.register_blueprint(inventory_bp)
