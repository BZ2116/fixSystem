@echo off
REM ============================================================
REM Repair System - 停止开发服务 (Windows)
REM ============================================================
setlocal

set PID_DIR=data\.pids

if not exist %PID_DIR%\flask.pid (
    echo [stop] 没有运行的 Flask 进程
    goto :check_vite
)
set /p FLASK_PID=<%PID_DIR%\flask.pid
echo [stop] 停止 Flask (pid=%FLASK_PID%)
taskkill /F /T /PID %FLASK_PID% >nul 2>&1
del %PID_DIR%\flask.pid

:check_vite
if not exist %PID_DIR%\vite.pid (
    echo [stop] 没有运行的 Vite 进程
    goto :done
)
set /p VITE_PID=<%PID_DIR%\vite.pid
echo [stop] 停止 Vite (pid=%VITE_PID%)
taskkill /F /T /PID %VITE_PID% >nul 2>&1
del %PID_DIR%\vite.pid

:done
echo [stop] 完成
endlocal