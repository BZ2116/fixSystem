"""兼容入口：新代码请用 backend/run.py。

保留此文件仅为向后兼容（部分旧文档/脚本可能引用 `python app.py`）。
由于本文件名为 app.py 且与 backend/app/ 包同名，Python 同名模块冲突让
`from app import app` 这种导入方式无法在本 shim 里工作。其他脚本请改用：
    from backend.run import app
或：
    cd backend && python run.py

本 shim 仅支持 `python app.py` 直接启动服务器。
"""
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_HERE, 'backend')

# 把当前 env 透传给子进程，FLASK_ENV / JWT_SECRET_KEY / DATABASE_URL / REDIS_URL 等
_env = os.environ.copy()

# 委托给 backend/run.py（flask debug auto-reload 由 run.py 自己处理，不会触发本 shim 递归）
_proc = subprocess.run(
    [sys.executable, os.path.join(_BACKEND, 'run.py')],
    cwd=_BACKEND,
    env=_env,
)
sys.exit(_proc.returncode)
