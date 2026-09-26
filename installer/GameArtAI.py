"""Windows GUI installer/launcher for GameArt AI Toolkit.

This executable is the user-facing bootstrapper. It locates Substance Painter,
installs the official Python plugin into the documented user plugin directory,
and can launch Painter with --enable-remote-scripting.
"""
from __future__ import annotations
import json
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from plugins.substance_painter.installer import PainterInstaller

def main():
    root=tk.Tk()
    root.title("GameArt AI Toolkit")
    root.geometry("560x330")
    root.resizable(False,False)
    label=tk.Label(root,text="GameArt AI Toolkit",font=("Segoe UI",18,"bold"))
    label.pack(pady=(24,8))
    status=tk.Label(root,text="检测 Substance 3D Painter...",justify="left",anchor="w")
    status.pack(fill="x",padx=32,pady=12)

    installer=PainterInstaller(Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[2])))

    def refresh():
        info=installer.verify()
        exes=info["painter_executables"]
        if info["ok"]:
            status.config(text=f"插件已安装\n{info['plugin']}\n\nPainter: {exes[0] if exes else '未检测到'}")
        else:
            status.config(text=f"插件未安装\nPainter: {exes[0] if exes else '未检测到'}")

    def install():
        try:
            result=installer.install()
            refresh()
            messagebox.showinfo("安装成功",f"GameArt AI Toolkit 已安装。\n\n{result['target']}")
        except Exception as exc:
            messagebox.showerror("安装失败",str(exc))

    def launch():
        try:
            installer.launch_remote()
            messagebox.showinfo("启动成功","Substance 3D Painter 已按 Remote Scripting 模式启动。")
        except Exception as exc:
            messagebox.showerror("启动失败",str(exc))

    buttons=tk.Frame(root); buttons.pack(pady=16)
    tk.Button(buttons,text="安装 / 修复",width=16,command=install).grid(row=0,column=0,padx=6)
    tk.Button(buttons,text="启动 Painter",width=16,command=launch).grid(row=0,column=1,padx=6)
    tk.Button(buttons,text="重新检测",width=16,command=refresh).grid(row=0,column=2,padx=6)
    refresh()
    root.mainloop()

if __name__=="__main__":
    main()
