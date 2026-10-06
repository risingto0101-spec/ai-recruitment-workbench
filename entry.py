import os
import sys

# PyInstaller 打包后运行时，entry.py 所在目录就是项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import run_server

if __name__ == "__main__":
    run_server()
