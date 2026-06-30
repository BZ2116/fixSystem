#!/usr/bin/env bash
# ============================================================
# Repair System - 停止开发服务 (Linux/macOS)
# ============================================================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PID_DIR="data/.pids"

kill_pid() {
    local name="$1"
    local pid_file="$PID_DIR/$1.pid"
    if [ ! -f "$pid_file" ]; then
        echo "[stop] 没有运行的 $name 进程"
        return
    fi
    local pid=$(cat "$pid_file")
    echo "[stop] 停止 $name (pid=$pid)"
    kill -TERM "$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    rm -f "$pid_file"
}

kill_pid flask
kill_pid vite
echo "[stop] 完成"