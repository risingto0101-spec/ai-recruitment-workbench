@echo off
setlocal EnableDelayedExpansion

:: 防止中文路径/空格路径导致异常
cd /d "%~dp0"

:: 捕获任何错误并暂停，避免窗口一闪而过
if not "%~1"=="" goto :retry_input

cls
echo ============================================
echo   AI 招聘工作台 - DeepSeek Key 配置工具
echo ============================================
echo.
echo 说明：
echo   1. 本脚本会把你的 Key 写入当前目录的 .env 文件
echo   2. Key 仅保存在你的本地电脑，不会上传
echo   3. 如没有 Key，请直接按回车，系统将使用规则引擎
echo.
echo DeepSeek API Key 获取地址：https://platform.deepseek.com/api_keys
echo.

set /p KEY="请输入 DeepSeek API Key（粘贴后按回车）："

if not defined KEY set KEY=
if "%KEY%"=="" (
    echo.
    echo 未输入 Key，已保持 AI_ENABLED=false，系统将继续使用规则引擎。
    (
        echo # DeepSeek AI 配置（留空则使用规则引擎）
        echo DEEPSEEK_API_KEY=
        echo DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
        echo AI_ENABLED=false
        echo.
        echo # 服务配置
        echo HOST=127.0.0.1
        echo PORT=8000
        echo.
        echo # 数据库路径（默认当前目录下的 recruitment.db）
        echo DB_PATH=recruitment.db
    ) > .env
    echo.
    echo 配置完成，按任意键退出。
    pause >nul
    exit /b 0
)

(
    echo # DeepSeek AI 配置（留空则使用规则引擎）
    echo DEEPSEEK_API_KEY=%KEY%
    echo DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
    echo AI_ENABLED=true
    echo.
    echo # 服务配置
    echo HOST=127.0.0.1
    echo PORT=8000
    echo.
    echo # 数据库路径（默认当前目录下的 recruitment.db）
    echo DB_PATH=recruitment.db
) > .env

echo.
echo Key 已保存到 .env 文件，AI 已启用。
echo 现在可以双击 start.bat 运行，或运行 build.bat 打包成 exe。
echo 按任意键退出。
pause >nul
exit /b 0

:retry_input
echo.
echo 请直接双击运行本脚本，不要在命令行中传参。
pause >nul
exit /b 1
