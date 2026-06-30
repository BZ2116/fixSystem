@echo off
REM ============================================================
REM Repair System - 生产模式启动 (Windows)
REM ============================================================
setlocal

if not exist .env (
    echo [start_prod] 复制 .env.example 为 .env
    copy .env.example .env >nul
)
if not exist backend\.venv (
    echo [start_prod] 创建虚拟环境
    cd backend
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)
if not exist data\repair_system.db (
    echo [start_prod] 初始化数据库
    cd backend
    call .venv\Scripts\activate.bat
    python scripts\init_db.py
    cd ..
)

if not exist frontend\dist\index.html (
    echo [start_prod] 构建前端
    cd frontend
    call npm install
    call npm run build
    cd ..
)

echo [start_prod] 启动 Flask（生产模式）...
cd backend
call .venv\Scripts\activate.bat
set FLASK_ENV=production
python run.py

endlocal