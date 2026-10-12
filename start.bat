@echo off
chcp 65001 >nul
title Still Here - backend
cd /d %~dp0
set "PY=C:\Users\LEOVO\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"
echo ==========================================
echo   Still Here backend starting...
echo   Page: http://127.0.0.1:8898/test1.html
echo   Keep this window OPEN while using the site.
echo   Close this window to stop the server.
echo ==========================================
"%PY%" main.py
echo.
echo Backend stopped. (If you saw a port error, the server is already running in another window.)
pause
