"""健康检查端点。"""
from flask import Blueprint
from extensions import db
from app.utils import ok

bp = Blueprint('health', __name__)


@bp.route('/api/health')
def health():
    """健康检查：验证数据库连通性。"""
    try:
        db.session.execute(db.text('SELECT 1'))
        db_ok = True
    except Exception:
        db_ok = False
    return ok({'status': 'healthy' if db_ok else 'degraded', 'db': db_ok})
