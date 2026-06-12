@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON="C:\Program Files\Python312\python.exe"

start "WCL Web App" cmd /k "chcp 65001 >nul && %PYTHON% web_app.py"

echo Waiting for server to start...
timeout /t 3 /nobreak >nul

start http://127.0.0.1:5000
