@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON=C:\Program Files\Python312\python.exe"
if not exist "%PYTHON%" (
    echo ========================================
    echo [错误] 找不到 Python
    echo 期望路径: %PYTHON%
    echo ========================================
    pause
    exit /b 1
)

echo 正在运行 WCL 对比分析...
echo.
"%PYTHON%" main.py %*

echo.
echo ========================================
echo 运行结束。按任意键关闭...
echo ========================================
pause >nul
