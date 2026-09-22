"""Optional Tk launcher UI.

Tkinter is imported lazily so CLI diagnostics and DCC adapters remain usable
when the Python runtime has no GUI support or the host is headless.
"""
from __future__ import annotations

import json
from .launcher import Launcher


class LauncherApp:
    def __init__(self, launcher: Launcher | None = None) -> None:
        try:
            import tkinter as tk
            from tkinter import messagebox
        except Exception as exc:
            raise RuntimeError(
                "Tkinter is unavailable; use the CLI commands "
                "'doctor', 'detect', or 'repair'."
            ) from exc

        self.tk = tk
        self.messagebox = messagebox
        self.launcher = launcher or Launcher()
        try:
            self.root = tk.Tk()
        except Exception as exc:
            raise RuntimeError(
                "The launcher UI could not start in this environment."
            ) from exc

        self.root.title("GameArt AI Toolkit")
        self.root.geometry("760x520")
        self.root.minsize(680, 460)
        self.status = tk.StringVar(value="Ready")
        self.output = tk.Text(self.root, height=20, wrap="word")
        self._build()

    def _build(self) -> None:
        tk = self.tk
        frame = tk.Frame(self.root, padx=18, pady=18)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="GameArt AI Toolkit", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(frame, text="Maya / 3ds Max / Pipeline / AI Automation").pack(anchor="w", pady=(2, 16))

        buttons = tk.Frame(frame)
        buttons.pack(fill="x")
        tk.Button(buttons, text="Detect DCC", command=self.detect, width=16).pack(side="left", padx=(0, 8))
        tk.Button(buttons, text="Doctor", command=self.doctor, width=16).pack(side="left", padx=8)
        tk.Button(buttons, text="Exit", command=self.root.destroy, width=16).pack(side="right")

        tk.Label(frame, textvariable=self.status, anchor="w").pack(fill="x", pady=12)
        self.output.pack(fill="both", expand=True)

    def _show(self, payload: object) -> None:
        self.output.delete("1.0", self.tk.END)
        self.output.insert(self.tk.END, json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        self.status.set("Completed")

    def detect(self) -> None:
        try:
            result = [d.__dict__ for d in self.launcher.detect_dcc()]
            self._show(result)
        except Exception as exc:
            self.status.set("Error")
            self.messagebox.showerror("Detection error", str(exc))

    def doctor(self) -> None:
        try:
            self._show(self.launcher.doctor())
        except Exception as exc:
            self.status.set("Error")
            self.messagebox.showerror("Doctor error", str(exc))

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    LauncherApp().run()


if __name__ == "__main__":
    main()
