@echo off
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ============================================
    echo  未检测到 Python
    echo ============================================
    echo.
    echo 本工具打包成 exe 需要 Python 环境。
    echo.
    echo 请按以下步骤操作：
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载并安装 Python 3.10 或更高版本
    echo   3. 安装时务必勾选 "Add Python to PATH"
    echo   4. 重新双击 build.bat
    echo.
    echo 如果已安装 Python，请检查是否勾选了 "Add Python to PATH"。
    echo.
    pause
    exit /b 1
)

where pip >nul 2>&1
if errorlevel 1 (
    echo 检测到 python，但未检测到 pip。
    echo 请重新安装 Python 并勾选 "Add Python to PATH"。
    pause
    exit /b 1
)

echo 正在安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 依赖安装失败，请检查网络连接。
    pause
    exit /b 1
)

echo 正在打包 exe...
pyinstaller --noconfirm --onefile --windowed --name "AI招聘工作台" --icon=extension/icons/icon48.png --add-data "app/templates;app/templates" --add-data "app/static;app/static" --add-data "extension;extension" entry.py
if errorlevel 1 (
    echo 打包失败，请查看上方错误信息。
    pause
    exit /b 1
)

echo 打包完成，产物位于 dist\AI招聘工作台.exe
pause
