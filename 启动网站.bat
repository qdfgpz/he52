@echo off
chcp 65001 >nul
title Still Here - 个人网站后端
echo ========================================
echo   Still Here 个人网站启动中...
echo   页面地址: http://127.0.0.1:8898/test1.html
echo   接口文档: http://127.0.0.1:8898/docs
echo   关闭此窗口即停止服务
echo ========================================
cd /d C:\Users\LEOVO\.zcode\workspace\default\my-website
"C:\Users\LEOVO\AppData\Local\Programs\Python\Python312\python.exe" main.py
pause
