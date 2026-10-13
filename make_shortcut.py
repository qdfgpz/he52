# -*- coding: utf-8 -*-
"""在桌面创建'启动网站'快捷方式：启动后端(pythonw 无窗口) + 打开浏览器页面"""
import os

import pythoncom
from win32com.client import Dispatch

DESKTOP = os.path.join(os.environ["USERPROFILE"], "Desktop")
LNK = os.path.join(DESKTOP, "启动网站.lnk")
PYW = r"C:\Users\LEOVO\AppData\Local\Programs\Python\Python312\pythonw.exe"
MAIN = r"C:\Users\LEOVO\.zcode\workspace\default\my-website\main.py"
URL = "http://127.0.0.1:8898/test1.html"

# 快捷方式本体：启动后端（无窗口），并用默认浏览器打开页面
shell = Dispatch("WScript.Shell")
lnk = shell.CreateShortCut(LNK)
lnk.TargetPath = PYW
lnk.Arguments = '"%s" && start "" "%s"' % (MAIN, URL)
lnk.WorkingDirectory = os.path.dirname(MAIN)
lnk.IconLocation = r"C:\Windows\System32\shell32.dll,13"  # 网页图标
lnk.Description = "启动个人网站后端并打开页面"
lnk.Save()
print("created:", LNK, os.path.exists(LNK))
