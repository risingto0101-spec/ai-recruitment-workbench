@echo off
cd /d "%~dp0"
set OUT=env-report.txt

if exist %OUT% del /f /q %OUT%

echo ============================ >> %OUT%
echo    运行环境检测报告 >> %OUT%
echo ============================ >> %OUT%
echo. >> %OUT%
echo 生成时间：%date% %time% >> %OUT%
echo 计算机名：%computername% >> %OUT%
echo 用户名：%username% >> %OUT%
echo 当前目录：%cd% >> %OUT%
echo. >> %OUT%

echo [Windows 版本] >> %OUT%
ver >> %OUT%
echo. >> %OUT%

echo [当前活动代码页] >> %OUT%
chcp >> %OUT%
echo. >> %OUT%

echo [系统基本信息] >> %OUT%
systeminfo 2>nul | findstr /B /C:"OS 名称" /C:"OS 版本" /C:"系统类型" /C:"处理器" >> %OUT%
if errorlevel 1 (
    echo 无法获取 systeminfo（可能被权限限制） >> %OUT%
)
echo. >> %OUT%

echo [Python 环境检测] >> %OUT%
where python >nul 2>&1
if errorlevel 1 (
    echo Python：未安装或未加入 PATH >> %OUT%
) else (
    echo Python：已安装 >> %OUT%
    python --version >> %OUT% 2>&1
)

where py >nul 2>&1
if errorlevel 1 (
    echo py 启动器：未安装 >> %OUT%
) else (
    echo py 启动器：已安装 >> %OUT%
)

where pip >nul 2>&1
if errorlevel 1 (
    echo pip：未安装或未加入 PATH >> %OUT%
) else (
    echo pip：已安装 >> %OUT%
    pip --version >> %OUT% 2>&1
)

where uvicorn >nul 2>&1
if errorlevel 1 (
    echo uvicorn：未安装 >> %OUT%
) else (
    echo uvicorn：已安装 >> %OUT%
    uvicorn --version >> %OUT% 2>&1
)

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo pyinstaller：未安装 >> %OUT%
) else (
    echo pyinstaller：已安装 >> %OUT%
    pyinstaller --version >> %OUT% 2>&1
)
echo. >> %OUT%

echo [PATH 环境变量（节选）] >> %OUT%
echo %path% >> %OUT%
echo. >> %OUT%

echo [用户权限] >> %OUT%
net session >nul 2>&1
if errorlevel 1 (
    echo 当前不是管理员权限 >> %OUT%
) else (
    echo 当前是管理员权限 >> %OUT%
)
echo. >> %OUT%

echo [bat 文件编码测试] >> %OUT%
echo 如果本行中文显示正常，说明 bat 编码与系统代码页匹配。 >> %OUT%
echo. >> %OUT%

echo ============================ >> %OUT%
echo 检测完成，请把 env-report.txt 发送给 AI。 >> %OUT%
echo ============================ >> %OUT%

if exist %OUT% (
    clip < %OUT%
    echo.
    echo 环境信息已收集完成，并复制到剪贴板。
    echo 请直接粘贴到 AI 对话框，或发送 env-report.txt 文件。
    echo.
    echo 同时已生成 env-report.txt 文件。
) else (
    echo 报告生成失败。
)

pause
