"""
PythonAnywhere WSGI 入口文件
PythonAnywhere 的 Web 设置里，WSGI 配置文件可以指向本文件：
    /home/<你的用户名>/wcl-compare/wsgi.py
"""
import os
import sys

# 将项目目录加入 Python 路径
project_home = os.path.expanduser("~/wcl-compare")
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 设置环境变量
os.environ.setdefault("PYTHONUNBUFFERED", "1")

# 导出 WSGI application
from web_app import app as application
