@echo off
chcp 65001 >nul
title Still Here - personal website backend
echo ========================================
echo   Still Here personal website starting...
echo   Page:  http://127.0.0.1:8898/test1.html
echo   API docs: http://127.0.0.1:8898/docs
echo   Close this window to stop the server
echo ========================================
cd /d %~dp0
python main.py
pause
