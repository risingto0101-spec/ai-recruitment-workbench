#!/usr/bin/env python3
"""
DeepSeek Key 配置工具（图形界面版）
需要 Python 和 tkinter 支持。
"""
import os
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("错误：当前 Python 未安装 tkinter，请使用 setup-key.vbs 或 setup_env.py")
    input("按回车退出...")
    sys.exit(1)


def save():
    key = entry.get().strip()
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
    if key:
        messagebox.showinfo("完成", "Key 已保存，AI 已启用。")
    else:
        messagebox.showinfo("完成", "未输入 Key，已使用规则引擎。")
    root.destroy()


root = tk.Tk()
root.title("AI 招聘工作台 - DeepSeek Key 配置")
root.geometry("500x180")
root.resizable(False, False)

tk.Label(root, text="DeepSeek API Key：").pack(pady=(15, 5))
entry = tk.Entry(root, width=50, show="*")
entry.pack(pady=5)
entry.focus()

tk.Label(root, text="没有 Key 可直接留空，系统会使用规则引擎。", fg="gray").pack(pady=5)

btn = tk.Button(root, text="保存配置", command=save, width=15)
btn.pack(pady=15)

root.mainloop()
