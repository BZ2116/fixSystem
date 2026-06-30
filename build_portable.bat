@echo off
REM ============================================================
REM Repair System - 便携包构建脚本（仅开发机器运行，不进 zip）
REM 用法: build_portable.bat 2026.06.30
REM ============================================================
set VERSION=%1
if "%VERSION%"=="" (
    echo [ERROR] 用法: build_portable.bat ^<version^>
    echo 示例:   build_portable.bat 2026.06.30
    exit /b 1
)

echo [build] 清理临时文件 ...
for /d /r backend %%d in (__pycache__) do @rd /s /q "%%d" 2>nul
for /d /r frontend %%d in (node_modules) do @rd /s /q "%%d" 2>nul
for /d /r frontend %%d in (dist) do @rd /s /q "%%d" 2>nul
if exist backend\.venv rd /s /q backend\.venv

echo [build] 构建前端生产包 ...
cd frontend
call npm install
call npm run build
cd ..

echo [build] 写入 VERSION.txt ...
echo %VERSION%> VERSION.txt

echo [build] 打包 zip ...
powershell -Command "Compress-Archive -Path backend,frontend,data,docs,start.bat,start.sh,start_prod.bat,start_prod.sh,stop.bat,stop.sh,.env.example,.gitignore,README.md,VERSION.txt -DestinationPath repair-system-portable-v%VERSION%.zip -Force"

echo [build] 完成: repair-system-portable-v%VERSION%.zip