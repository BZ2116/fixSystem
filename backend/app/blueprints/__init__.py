"""蓝图注册入口。"""
from flask import Flask


def register_blueprints(app: Flask):
    from .setup import bp as setup_bp
    from .health import bp as health_bp
    from .auth import bp as auth_bp
    app.register_blueprint(setup_bp, url_prefix='/api/setup')
    app.register_blueprint(health_bp)  # /api/health
    app.register_blueprint(auth_bp)  # 自带 url_prefix='/api/auth'
