"""
开发模式进程管理器：同时启动 Flask（5000）和 Vite（5173）。
通过 PID 文件管理两个进程；任一进程崩溃则全部退出。

用法：
    python scripts/start_dev.py
"""
import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
_PROJECT_ROOT = _BACKEND.parent
_FRONTEND = _PROJECT_ROOT / 'frontend'

PID_DIR = _PROJECT_ROOT / 'data' / '.pids'
LOG_DIR = _PROJECT_ROOT / 'data' / 'logs'
FLASK_PID = PID_DIR / 'flask.pid'
VITE_PID = PID_DIR / 'vite.pid'
FLASK_LOG = LOG_DIR / 'flask.log'
VITE_LOG = LOG_DIR / 'vite.log'


def _ensure_dirs():
    PID_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == 'nt':
            # Windows: 用 tasklist 验证
            out = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True, text=True,
            ).stdout
            return str(pid) in out
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def _read_pid(path: Path) -> int:
    try:
        return int(path.read_text().strip())
    except Exception:
        return 0


def _spawn(cmd, cwd, log_path, env):
    """启动子进程，stdout/stderr 重定向到日志，返回 Popen。"""
    log_f = open(log_path, 'a', encoding='utf-8')
    log_f.write(f'\n===== start at {datetime.now().isoformat()} =====\n')
    log_f.flush()
    proc = subprocess.Popen(
        cmd, cwd=str(cwd), env=env,
        stdout=log_f, stderr=subprocess.STDOUT,
    )
    return proc


def main():
    _ensure_dirs()

    # 检查现有进程
    for name, pid_file in [('flask', FLASK_PID), ('vite', VITE_PID)]:
        old = _read_pid(pid_file)
        if old and _is_alive(old):
            print(f'[start_dev] {name} (pid={old}) 已在运行，先停止')
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(old)],
                               capture_output=True)
            else:
                os.kill(old, signal.SIGTERM)
            time.sleep(1)
        if pid_file.exists():
            pid_file.unlink()

    # 构造环境
    env = os.environ.copy()
    env.setdefault('FLASK_ENV', 'development')

    flask_cmd = [sys.executable, str(_BACKEND / 'run.py')]
    vite_cmd = ['npm', 'run', 'dev']
    if os.name == 'nt':
        # npm 在 Windows 上是 npm.cmd
        vite_cmd[0] = 'npm.cmd'

    print('[start_dev] 启动 Flask :5000 ...')
    flask_proc = _spawn(flask_cmd, _BACKEND, FLASK_LOG, env)
    FLASK_PID.write_text(str(flask_proc.pid))

    print('[start_dev] 启动 Vite :5173 ...')
    vite_proc = _spawn(vite_cmd, _FRONTEND, VITE_LOG, env)
    VITE_PID.write_text(str(vite_proc.pid))

    print('[start_dev] Flask 日志:', FLASK_LOG)
    print('[start_dev] Vite  日志:', VITE_LOG)
    print('[start_dev] 浏览器打开 http://localhost:5173  (Ctrl+C 退出)')

    def cleanup(*_):
        print('\n[start_dev] 正在停止子进程 ...')
        for proc, name in [(flask_proc, 'flask'), (vite_proc, 'vite')]:
            try:
                if os.name == 'nt':
                    subprocess.run(
                        ['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                        capture_output=True,
                    )
                else:
                    proc.terminate()
                    proc.wait(timeout=3)
            except Exception:
                pass
        for p in (FLASK_PID, VITE_PID):
            try:
                p.unlink()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, cleanup)

    # 主循环：任一进程死亡就退出
    try:
        while True:
            time.sleep(2)
            if flask_proc.poll() is not None:
                print('[start_dev] Flask 进程退出，停止所有服务')
                cleanup()
            if vite_proc.poll() is not None:
                print('[start_dev] Vite 进程退出，停止所有服务')
                cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == '__main__':
    main()
