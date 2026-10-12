@echo off
chcp 65001 >nul
title Still Here - backend
cd /d %~dp0
set "PY=C:\Users\LEOVO\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"
netstat -ano | findstr :8898 | findstr LISTENING >nul
if %errorlevel%==0 (
  echo 服务已经在运行，无需重复启动。
  echo 浏览器访问 http://127.0.0.1:8898/test1.html 即可。
  timeout /t 4 >nul
  exit /b
)
echo ==========================================
echo   Still Here backend starting...
echo   Page: http://127.0.0.1:8898/test1.html
echo   Keep this window OPEN while using the site.
echo   Close this window to stop the server.
echo ==========================================
"%PY%" main.py
echo.
echo Backend stopped. Run start.bat again to restart.
pause
