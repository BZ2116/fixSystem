"""订单号生成器：按业务前缀 + 日期 + 序号。

⚠️ 进程内计数器：gunicorn 多 worker 部署时各 worker 独立计数，可能产生重复号。
生产环境应改用 DB sequence 或在 number 列上加 unique 约束兜底。本工具仅供：
1. 单 worker 开发模式
2. 测试场景（reset_counter 在 setUp/teardown 调用）
"""
from datetime import datetime
import threading

_lock = threading.Lock()
_counter = {}


def generate_code(prefix: str, width: int = 4) -> str:
    """生成形如 'WO202606290001' 的业务单号。

    Args:
        prefix: 业务前缀（WO/RC/SO/PO/QO...）
        width: 序号位数（默认 4 位，不足补 0）
    """
    today = datetime.now().strftime('%Y%m%d')
    key = f'{prefix}-{today}'
    with _lock:
        _counter[key] = _counter.get(key, 0) + 1
        seq = _counter[key]
    return f'{prefix}{today}{seq:0{width}d}'


def reset_counter(prefix: str = None):
    """测试用：重置计数器。"""
    global _counter
    if prefix is None:
        _counter = {}
    else:
        today = datetime.now().strftime('%Y%m%d')
        _counter.pop(f'{prefix}-{today}', None)