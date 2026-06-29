"""
种子数据：仅在空库时运行（sys_user 表为空）。
"""
import logging
from flask import current_app

from extensions import db  # runtime resolved via sys.path

logger = logging.getLogger(__name__)


def run_seeds_if_empty():
    """如果数据库为空，记录警告，由 setup 端点引导创建管理员。"""
    try:
        # 延迟导入避免循环依赖
        from models.system import SysUser
        if db.session.query(SysUser).count() == 0:
            logger.warning(
                '数据库为空。请通过 setup 端点创建初始管理员：'
                'POST /api/setup/init {username, password}'
            )
    except Exception as e:
        # 表不存在（首次迁移未执行）时静默
        logger.debug('seed check skipped: %s', e)