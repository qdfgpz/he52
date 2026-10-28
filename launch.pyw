# -*- coding: utf-8 -*-
"""无窗口启动器（供桌面快捷方式调用，也可直接双击）：
端口已在监听 → 直接开浏览器；否则后台拉起 main.py（日志写入 server.log），
等端口就绪后再开浏览器。"""
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PORT = 8898
URL = "http://127.0.0.1:%d/" % PORT
HERE = Path(__file__).resolve().parent


def alive() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


if not alive():
    # pythonw 无控制台，子进程输出重定向到 server.log，排障有据可查
    log = open(HERE / "server.log", "ab")
    subprocess.Popen(
        [sys.executable, str(HERE / "main.py")],
        stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
        cwd=str(HERE), close_fds=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    for _ in range(40):  # 最多等 20 秒让后端就绪
        if alive():
            break
        time.sleep(0.5)
webbrowser.open(URL)
