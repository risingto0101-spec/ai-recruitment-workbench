@echo off
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ============================================
    echo  未检测到 Python
    echo ============================================
    echo.
    echo 启动本工具需要 Python 环境。
    echo.
    echo 请按以下步骤操作：
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载并安装 Python 3.10 或更高版本
    echo   3. 安装时务必勾选 "Add Python to PATH"
    echo   4. 重新双击 start.bat
    echo.
    echo 如果已安装 Python，请检查是否勾选了 "Add Python to PATH"。
    echo.
    pause
    exit /b 1
)

where uvicorn >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

call uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
