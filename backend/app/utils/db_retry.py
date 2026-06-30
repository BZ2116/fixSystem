"""
SQLite 写入重试装饰器：捕获 'database is locked'，自动重试。

适用场景：workorder 创建、库存变更、财务写入（spec §8）。
"""
import time
import functools
import logging

from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


def retry_on_lock(max_retries: int = 3, delay: float = 0.5):
    """装饰器：捕获 SQLite 'database is locked' 错误并重试。

    Args:
        max_retries: 最大重试次数（含首次）
        delay: 重试间隔（秒）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    msg = str(e).lower()
                    if 'locked' not in msg or i == max_retries - 1:
                        raise
                    last_err = e
                    logger.warning(
                        'SQLite locked on %s, retry %d/%d',
                        func.__name__, i + 1, max_retries,
                    )
                    time.sleep(delay)
            if last_err:
                raise last_err
        return wrapper
    return decorator