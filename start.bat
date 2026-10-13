@echo off
chcp 65001 >nul
title Still Here - backend
cd /d %~dp0
set "PY=C:\Users\LEOVO\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"
netstat -ano | findstr :8898 | findstr LISTENING >nul
if %errorlevel%==0 (
  echo 服务已经在运行，正在为你打开页面...
  start "" "http://127.0.0.1:8898/test1.html"
  timeout /t 3 >nul
  exit /b
)
echo ==========================================
echo   Still Here backend starting...
echo   Page: http://127.0.0.1:8898/test1.html
echo   请保持本窗口开启（关闭窗口即停止服务）
echo ==========================================
start "" "http://127.0.0.1:8898/test1.html"
"%PY%" main.py
echo.
echo Backend stopped. Run start.bat again to restart.
pause
