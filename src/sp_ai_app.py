"""Standalone Substance 3D Painter AI console.

The model can only call the allow-listed Painter tools exposed by
plugins.substance_painter.openai_tools. No arbitrary Python, shell commands,
mouse/keyboard automation, or private Painter APIs are exposed.
"""
from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from src.ai.provider import OpenAIResponsesProvider
from plugins.substance_painter.installer import PainterInstaller
from plugins.substance_painter.openai_tools import build_painter_tools
from plugins.substance_painter.remote_client import PainterRemote


SYSTEM_INSTRUCTIONS = """You are the GameArt AI Toolkit assistant controlling Adobe Substance 3D Painter.
Use only the provided Painter tools. Never invent tool results.
Before changing a project, inspect project/layers/texture sets when needed.
For destructive or export operations, follow the user's explicit request.
You are controlling Painter through Adobe's documented Python API and Remote
Scripting bridge; do not request or execute arbitrary Python or OS commands.
"""


class SubstancePainterAIApp:
    def __init__(self, parent=None) -> None:
        self._standalone = parent is None
        self.root = tk.Tk() if self._standalone else tk.Toplevel(parent)
        self.root.title("GameArt AI Toolkit · Substance 3D Painter")
        self.root.geometry("980x760")
        self.root.minsize(860, 650)
        self.api_key = tk.StringVar(value=os.getenv("OPENAI_API_KEY", ""))
        self.model = tk.StringVar(value=os.getenv("OPENAI_MODEL", "gpt-5.6"))
        self.status = tk.StringVar(value="未连接 Painter")
        self._build()

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="GameArt AI Toolkit", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Substance 3D Painter AI 控制台 · OpenAI Responses API + Adobe Painter Remote Scripting",
        ).pack(anchor="w", pady=(2, 12))

        config = ttk.LabelFrame(outer, text="连接")
        config.pack(fill="x", pady=(0, 10))
        ttk.Label(config, text="OpenAI API Key").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(config, textvariable=self.api_key, show="*", width=58).grid(
            row=0, column=1, padx=8, pady=8, sticky="ew"
        )
        ttk.Label(config, text="Model").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(config, textvariable=self.model, width=18).grid(
            row=0, column=3, padx=8, pady=8, sticky="ew"
        )
        config.columnconfigure(1, weight=1)

        buttons = ttk.Frame(config)
        buttons.grid(row=1, column=0, columnspan=4, padx=8, pady=(0, 8), sticky="w")
        ttk.Button(buttons, text="安装/修复 Painter 插件", command=self.install_plugin).pack(side="left")
        ttk.Button(buttons, text="启动 Painter（远程模式）", command=self.launch_painter).pack(
            side="left", padx=6
        )
        ttk.Button(buttons, text="测试连接", command=self.test_connection).pack(side="left")
        ttk.Label(buttons, textvariable=self.status).pack(side="left", padx=14)

        ttk.Label(outer, text="给 AI 的指令").pack(anchor="w")
        self.prompt = tk.Text(outer, height=7, wrap="word")
        self.prompt.pack(fill="x", pady=(4, 8))
        self.prompt.insert("1.0", "检查当前 Painter 项目，然后把当前选中的填充层 BaseColor 改成 #808080。")
        ttk.Button(outer, text="执行 AI 指令", command=self.run_prompt).pack(anchor="w", pady=(0, 8))

        ttk.Label(outer, text="执行日志").pack(anchor="w")
        self.log = tk.Text(outer, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)

    def _write(self, value) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", str(value) + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _source_root(self):
        import sys
        from pathlib import Path
        return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))

    def _painter_installer(self) -> PainterInstaller:
        return PainterInstaller(self._source_root())

    def install_plugin(self) -> None:
        try:
            result = self._painter_installer().install()
            self._write(result)
            self.status.set("Painter 插件已安装")
        except Exception as exc:
            self.status.set("安装失败")
            messagebox.showerror("Painter 插件", f"{type(exc).__name__}: {exc}")

    def launch_painter(self) -> None:
        try:
            process = self._painter_installer().launch_remote()
            self._write(f"Painter 已启动，PID={process.pid}，Remote Scripting 端口 60041")
            self.status.set("等待 Painter 就绪…")
        except Exception as exc:
            self.status.set("Painter 未启动")
            messagebox.showerror("Substance 3D Painter", f"{type(exc).__name__}: {exc}")

    def _remote(self) -> PainterRemote:
        return PainterRemote(host="127.0.0.1", port=60041, timeout=3600)

    def test_connection(self) -> None:
        def work():
            try:
                result = self._remote().dispatch("project.info", {})
                self.root.after(0, lambda: self._connection_done(True, result))
            except Exception as exc:
                self.root.after(0, lambda: self._connection_done(False, exc))
        threading.Thread(target=work, daemon=True).start()
        self.status.set("连接测试中…")

    def _connection_done(self, ok: bool, result) -> None:
        if ok:
            self.status.set("Painter 已连接")
            self._write({"connection": "ok", "project": result})
        else:
            self.status.set("Painter 未连接")
            self._write({"connection": "failed", "error": str(result)})

    def run_prompt(self) -> None:
        prompt = self.prompt.get("1.0", "end").strip()
        key = self.api_key.get().strip()
        model = self.model.get().strip()
        if not prompt:
            messagebox.showwarning("AI 指令", "请输入指令。")
            return
        if not key:
            messagebox.showwarning("OpenAI API", "请填写 OpenAI API Key。")
            return
        if not model:
            messagebox.showwarning("OpenAI Model", "请填写模型名称。")
            return

        self.status.set("AI 执行中…")
        self._write("USER > " + prompt)

        def work():
            try:
                remote = self._remote()
                registry = build_painter_tools(remote)
                provider = OpenAIResponsesProvider(api_key=key, model=model)
                result = provider.run(
                    SYSTEM_INSTRUCTIONS + "\n\nUser request:\n" + prompt,
                    registry.openai_tools(),
                    registry.handlers(),
                    max_tool_rounds=20,
                )
                self.root.after(0, lambda: self._ai_done(result))
            except Exception as exc:
                self.root.after(0, lambda: self._ai_done(
                    {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
                ))
        threading.Thread(target=work, daemon=True).start()

    def _ai_done(self, result) -> None:
        if getattr(result, "ok", False):
            response = getattr(result, "result", None)
            text = getattr(response, "output_text", None) or str(response)
            self._write("AI > " + text)
            self.status.set("执行完成")
        else:
            error = getattr(result, "error", None) or result
            self._write("ERROR > " + str(error))
            self.status.set("执行失败")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    SubstancePainterAIApp().run()
