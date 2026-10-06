#!/usr/bin/env python3
"""
DeepSeek Key 配置脚本（跨平台）
运行后会提示输入 DeepSeek API Key，并写入当前目录的 .env 文件。
"""
import os
import sys
from pathlib import Path


def main():
    print("=" * 50)
    print("  AI 招聘工作台 - DeepSeek Key 配置工具")
    print("=" * 50)
    print()
    print("说明：")
    print("  1. 本脚本会把你的 Key 写入当前目录的 .env 文件")
    print("  2. Key 仅保存在你的本地电脑，不会上传")
    print("  3. 如没有 Key，请直接回车，系统将使用规则引擎")
    print()
    print("DeepSeek API Key 获取地址：https://platform.deepseek.com/api_keys")
    print()

    key = input("请输入 DeepSeek API Key（粘贴后按回车）：").strip()

    env_path = Path(__file__).resolve().parent / ".env"
    lines = [
        "# DeepSeek AI 配置（留空则使用规则引擎）",
        f"DEEPSEEK_API_KEY={key}",
        "DEEPSEEK_BASE_URL=https://api.deepseek.com/v1",
        f"AI_ENABLED={'true' if key else 'false'}",
        "",
        "# 服务配置",
        "HOST=127.0.0.1",
        "PORT=8000",
        "",
        "# 数据库路径（默认当前目录下的 recruitment.db）",
        "DB_PATH=recruitment.db",
    ]
    env_path.write_text("\n".join(lines), encoding="utf-8")

    print()
    if key:
        print("Key 已保存，AI 已启用。")
    else:
        print("未输入 Key，已保持 AI_ENABLED=false，继续使用规则引擎。")
    print(f"配置文件位置：{env_path}")
    print("现在可以运行 start.bat / start.sh 启动服务，或 build.bat 打包 exe。")


if __name__ == "__main__":
    main()
