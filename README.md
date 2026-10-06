# AI 招聘工作台

本地化 AI 招聘管理工具，支持岗位管理、候选人录入、自动匹配、人才库筛选、话术生成和统计看板。

## 快速开始

### 方式一：有 Python 环境

1. 解压压缩包
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置 DeepSeek Key（可选，不配也能用规则引擎）：
   - Windows（推荐）：双击 `setup-key.bat`
   - Windows（兼容）：双击 `配置 DeepSeek Key.bat`
   - 跨平台：运行 `python setup_env.py`
4. 启动服务：
   - Windows：双击 `start.bat`
   - 其他系统：运行 `uvicorn app.main:app --host 127.0.0.1 --port 8000`
5. 浏览器打开 http://127.0.0.1:8000

### 方式二：打包成 exe（推荐无 Python 环境）

1. 解压压缩包到本地目录（**不要直接在压缩包里双击**）
2. 配置 DeepSeek Key：
   - 首选：双击 `setup-key.vbs`（图形弹窗，最稳定）
   - 备选：双击 `setup-key.bat`
   - 再备选：双击 `配置 DeepSeek Key.bat`
3. 双击 `build.bat`，等待打包完成
4. 进入 `dist` 目录，双击 `AI招聘工作台.exe` 即可运行
5. 浏览器打开 http://127.0.0.1:8000

### 方式三：GitHub Actions 云端打包（本地不装 Python）

如果你的电脑无法安装/运行 Python，可以用 GitHub 免费提供的 Windows 服务器在云端打包 exe：

1. 把本项目文件夹上传到你新建的 GitHub 仓库（已包含 `.github/workflows/build.yml`）
2. 在 GitHub 页面点击 **Actions → Build Windows EXE → Run workflow**
3. 等待约 2-3 分钟
4. 进入 **Actions 运行记录 → Artifacts**，下载 `AI招聘工作台-windows-exe`
5. 解压后得到 `AI招聘工作台.exe`，双击即可运行

> 注意：
> - GitHub Actions 生成的 exe 中**不包含你的 DeepSeek Key**。下载 exe 后，在本机运行 `setup-key.vbs` 配置 Key。
> - 云端打包使用 **Python 3.8 + PyInstaller 5.x**，可兼容 Windows 7/10/11。如果你的系统较老，请优先使用这种方式。

## 浏览器插件安装

1. 打开 Edge 浏览器，进入 `edge://extensions/`
2. 开启「开发人员模式」
3. 点击「加载解压缩的扩展」
4. 选择本项目中的 `extension` 文件夹
5. 在 BOSS 直聘或前程无忧页面，点击插件图标即可抓取职位/简历并推送到本地

## DeepSeek Key 配置说明

- Key 仅保存在本地 `.env` 文件中，不会上传或泄露
- 不配置 Key 时，系统使用内置规则引擎完成解析和匹配
- 配置 Key 后，解析和匹配会自动优先调用 DeepSeek AI
- 如需更换 Key，重新运行配置工具即可覆盖 `.env`

## 项目结构

```
recruitment-assistant/
├── app/                    # FastAPI 后端
│   ├── main.py             # 入口
│   ├── db.py               # SQLite 数据库
│   ├── config.py           # 配置读取
│   ├── routers/            # API 路由
│   ├── services/           # 业务逻辑（解析、匹配、AI 调用）
│   ├── templates/          # Jinja2 页面
│   └── static/             # CSS/JS
├── .github/workflows/       # GitHub Actions 自动打包配置
├── .gitignore              # Git 忽略文件
├── extension/              # Edge 浏览器插件
├── start.bat               # 开发启动脚本
├── build.bat               # PyInstaller 打包脚本
├── check-env.bat           # 环境检测工具，生成 env-report.txt
├── setup-key.vbs           # Key 配置工具（VBS 弹窗版，推荐）
├── setup-key.bat           # Key 配置工具（无空格 bat 版）
├── setup-key-gui.py        # Key 配置工具（Python 图形界面版）
├── 配置 DeepSeek Key.bat    # Key 配置工具（中文名兼容版）
├── setup_env.py            # Key 配置脚本（跨平台命令行版）
├── test-window.bat         # 用于测试 bat 是否能正常显示窗口
├── requirements.txt        # Python 依赖
└── .env.example            # 环境变量示例
```

## 环境检测工具

如果你遇到 bat 闪退、乱码、找不到命令等问题，先双击运行 `check-env.bat`：

1. 它会自动收集你的 Windows 版本、当前代码页、Python 安装情况、PATH 等信息
2. 生成 `env-report.txt` 文件
3. 同时把内容复制到剪贴板

你可以直接把内容粘贴发给 AI，AI 就能根据你的真实运行环境给出针对性方案。

## 常见问题

**Q：没有 DeepSeek Key 能用吗？**
A：可以。系统内置规则引擎，无需 Key 也能完成岗位/候选人解析和人岗匹配。

**Q：为什么打包后的 exe 第一次启动较慢？**
A：PyInstaller 单文件 exe 启动时需要先解压资源到临时目录，属于正常现象。

**Q：数据库在哪里？**
A：默认在工作目录下的 `recruitment.db`，可直接复制备份或迁移。

**Q：双击 exe 提示丢失 `api-ms-win-core-path-l1-1-0.dll` 或 `Failed to load Python DLL`？**
A：说明当前 exe 是用 Python 3.10+ 打包的，不支持 Windows 7。请使用 GitHub Actions 云端打包（方式三），它会自动用 Python 3.8 打包，兼容 Windows 7。

**Q：`配置 DeepSeek Key.bat` 双击后窗口一闪而过？**
A：按以下顺序尝试：
1. 先双击 `test-window.bat`，如果也闪退，说明系统对 bat 执行有限制（如安全软件/组策略）
2. 使用 `setup-key.vbs`（图形弹窗，不需要命令行窗口）
3. 使用 `setup-key-gui.py`（需要 Python + tkinter）
4. 右键 `setup-key.bat` →「以管理员身份运行」
