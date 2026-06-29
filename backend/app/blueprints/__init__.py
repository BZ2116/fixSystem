"""蓝图注册入口。"""
from flask import Flask


def register_blueprints(app: Flask):
    # 阶段 1：仅注册 setup 蓝图；其他蓝图在阶段 2 拆分时引入
    from .setup import bp as setup_bp
    app.register_blueprint(setup_bp, url_prefix='/api/setup')

    # 阶段 2 拆分后这里会加上：
    # from .auth import bp as auth_bp
    # from .customers import bp as customers_bp
    # ...