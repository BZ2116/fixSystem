@echo off
REM ============================================================
REM Repair System - 开发模式启动脚本 (Windows)
REM ============================================================
setlocal

echo [start] 检查 Python ...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未检测到 Python，请先安装 Python 3.11+: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 第一次启动：复制 .env.example
if not exist .env (
    echo [start] 复制 .env.example 为 .env
    copy .env.example .env >nul
)

REM 第一次启动：创建虚拟环境
if not exist backend\.venv (
    echo [start] 创建 Python 虚拟环境 backend\.venv
    cd backend
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)

REM 第一次启动：初始化数据库
if not exist data\repair_system.db (
    echo [start] 初始化 SQLite 数据库
    cd backend
    call .venv\Scripts\activate.bat
    python scripts\init_db.py
    cd ..
)

REM 第一次启动：安装前端依赖
if not exist frontend\node_modules (
    echo [start] 安装前端依赖（首次较慢）
    cd frontend
    call npm install
    cd ..
)

REM 启动开发服务
echo [start] 启动 Flask + Vite ...
cd backend
call .venv\Scripts\activate.bat
python scripts\start_dev.py
cd ..

endlocal