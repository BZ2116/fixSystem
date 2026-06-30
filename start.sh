#!/usr/bin/env bash
# ============================================================
# Repair System - 开发模式启动脚本 (Linux/macOS)
# ============================================================
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[start] 检查 Python ..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] 未检测到 python3，请先安装 Python 3.11+"
    exit 1
fi

# 第一次启动：复制 .env.example
if [ ! -f .env ]; then
    echo "[start] 复制 .env.example 为 .env"
    cp .env.example .env
fi

# 第一次启动：创建虚拟环境
if [ ! -d backend/.venv ]; then
    echo "[start] 创建 Python 虚拟环境 backend/.venv"
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# 第一次启动：初始化数据库
if [ ! -f data/repair_system.db ]; then
    echo "[start] 初始化 SQLite 数据库"
    cd backend
    source .venv/bin/activate
    python scripts/init_db.py
    cd ..
fi

# 第一次启动：安装前端依赖
if [ ! -d frontend/node_modules ]; then
    echo "[start] 安装前端依赖（首次较慢）"
    cd frontend
    npm install
    cd ..
fi

# 启动开发服务
echo "[start] 启动 Flask + Vite ..."
cd backend
source .venv/bin/activate
python scripts/start_dev.py