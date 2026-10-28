# -*- coding: utf-8 -*-
"""在桌面创建“启动网站”快捷方式：pythonw 无窗口运行 launch.pyw
（launch.pyw 自动检测端口 → 后台拉起后端 → 就绪后打开浏览器）。"""
import os
import sys
from pathlib import Path

import pythoncom
from win32com.client import Dispatch

BASE = Path(__file__).resolve().parent
DESKTOP = Path(os.environ["USERPROFILE"]) / "Desktop"
LNK = DESKTOP / "启动网站.lnk"
LAUNCH = BASE / "launch.pyw"

# 优先用当前解释器同目录的 pythonw；找不到再退回固定安装路径
PYW = Path(sys.executable).with_name("pythonw.exe")
if not PYW.exists():
    PYW = Path(r"C:\Users\LEOVO\AppData\Local\Programs\Python\Python312\pythonw.exe")

shell = Dispatch("WScript.Shell")
lnk = shell.CreateShortCut(str(LNK))
lnk.TargetPath = str(PYW)
lnk.Arguments = '"%s"' % LAUNCH
lnk.WorkingDirectory = str(BASE)
lnk.IconLocation = r"C:\Windows\System32\shell32.dll,13"  # 网页图标
lnk.Description = "启动个人网站后端并打开页面"
lnk.Save()
print("created:", LNK, LNK.exists())
