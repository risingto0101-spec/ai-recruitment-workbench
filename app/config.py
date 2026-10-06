import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def get_base_dir() -> Path:
    """获取项目根目录：源码模式为当前文件上级，exe 模式为临时解压目录。"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后运行时
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_work_dir() -> Path:
    """获取工作目录：exe 模式为 exe 所在目录，源码模式为项目根目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return get_base_dir()


_BASE_DIR = get_base_dir()
_WORK_DIR = get_work_dir()

# 加载 .env（工作目录优先）
load_dotenv(_WORK_DIR / ".env", override=True)


def env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# 数据库路径：默认工作目录下的 recruitment.db
DB_PATH = env("DB_PATH", str(_WORK_DIR / "recruitment.db"))
HOST = env("HOST", "127.0.0.1")
PORT = int(env("PORT", "8000"))

# AI 配置
DEEPSEEK_API_KEY = env("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = env("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
AI_ENABLED = env("AI_ENABLED", "false").lower() in ("true", "1", "yes", "on")


def is_ai_enabled() -> bool:
    return AI_ENABLED and bool(DEEPSEEK_API_KEY.strip())
