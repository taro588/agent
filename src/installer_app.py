"""Standalone one-click Windows installer UI."""
from __future__ import annotations
import os, shutil, sys, threading, tkinter as tk
import tempfile, time, importlib, json, urllib.request
import tempfile, time
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from src.core.installer import ToolkitInstaller
from src.core.plugin_installer import PluginInstaller
from src.core.host_integration import HostIntegrator

APP_VERSION="0.1.0-alpha"
UPDATE_URL="https://api.github.com/repos/taro588/taro588.gitthub.io/releases/latest"

APP_VERSION="0.1.0-alpha"

PLUGINS=[("texture-importer","Maya"),("totex","3ds Max"),("MayaToPainter","Maya"),("SubstancePainterToMaya","Maya"),("rename-lowhigh-proximity","3ds Max"),("fal-texture-pbr-generator","Shared"),("Procedural-PBR","Shared"),("SubstanceDesignerTools","Shared")]

def bundled_src(): return Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))/"src"
def detect_hosts():
    return {"maya":bool(os.environ.get("MAYA_LOCATION") or os.environ.get("MAYA_APP_DIR")),
            "3ds_max":bool(os.environ.get("ADSK_3DSMAX_USER_PATH") or os.environ.get("3DSMAX_ROOT"))}

class InstallerApp:
    def __init__(self):
        self.root=tk.Tk(); self.root.title("GameArt AI Toolkit"); self.root.geometry("900x720"); self.root.minsize(820,640)
        self.install_root=Path(os.environ.get("GAMEART_TOOLKIT_HOME",Path.home()/"GameArtAI"/"Toolkit")).expanduser().resolve()
        self.status=tk.StringVar(value="Ready"); self._build()
    def _build(self):
        o=ttk.Frame(self.root,padding=22); o.pack(fill="both",expand=True)
        ttk.Label(o,text="GameArt AI Toolkit",font=("Segoe UI",22,"bold")).pack(anchor="w")
        ttk.Label(o,text="安装 / 修复 / 更新 / 卸载 · 无需 Python").pack(anchor="w",pady=(2,14))
        row=ttk.Frame(o); row.pack(fill="x"); ttk.Label(row,text="安装位置：").pack(side="left")
        self.path_var=tk.StringVar(value=str(self.install_root)); ttk.Entry(row,textvariable=self.path_var).pack(side="left",fill="x",expand=True,padx=8); ttk.Button(row,text="浏览…",command=self.choose_path).pack(side="right")
        hosts=detect_hosts(); self.host_vars={}
        hf=ttk.LabelFrame(o,text="主机集成"); hf.pack(fill="x",pady=12)
        for i,(h,label) in enumerate((("maya","Maya"),("3ds_max","3ds Max"))):
            v=tk.BooleanVar(value=hosts[h]); self.host_vars[h]=v; ttk.Checkbutton(hf,text=f"{label}（{'已检测到' if hosts[h] else '未检测到'}）",variable=v).grid(row=0,column=i,sticky="w",padx=12,pady=8)
        ttk.Label(o,text="第三方插件（安装时可选）：").pack(anchor="w")
        self.vars={}; g=ttk.Frame(o); g.pack(fill="x")
        for i,(n,h) in enumerate(PLUGINS):
            v=tk.BooleanVar(); self.vars[n]=v; ttk.Checkbutton(g,text=f"{n}  [{h}]",variable=v).grid(row=i//2,column=i%2,sticky="w",padx=8,pady=3)
        b=ttk.Frame(o); b.pack(fill="x",pady=14)
        self.btn=ttk.Button(b,text="一键安装 / 更新",command=self.start_install); self.btn.pack(side="left"); ttk.Button(b,text="回滚上一版本",command=lambda:self._run(self.rollback)).pack(side="left",padx=6)
        ttk.Button(b,text="修复",command=lambda:self._run(self.repair)).pack(side="left",padx=6)
        ttk.Button(b,text="卸载",command=self.start_uninstall).pack(side="left")
        ttk.Button(b,text="检查环境",command=lambda:self._run(self.doctor)).pack(side="left",padx=6); ttk.Button(b,text="检查更新",command=lambda:self._run(self.check_update)).pack(side="left")
        ttk.Button(b,text="退出",command=self.root.destroy).pack(side="right")
        self.progress=ttk.Progressbar(o,mode="indeterminate"); self.progress.pack(fill="x"); ttk.Label(o,textvariable=self.status).pack(fill="x",pady=8)
        self.log=tk.Text(o,height=18); self.log.pack(fill="both",expand=True)
    def choose_path(self):
        p=filedialog.askdirectory(initialdir=str(self.install_root.parent))
        if p:self.path_var.set(str(Path(p)/"GameArtAI"/"Toolkit"))
    def write(self,s): self.log.insert("end",str(s)+"\n"); self.log.see("end")
    def _run(self,fn):
        self.status.set("处理中…"); self.progress.start(12); self.btn.configure(state="disabled"); threading.Thread(target=self._worker,args=(fn,),daemon=True).start()
    def _worker(self,fn):
        try:r=fn()
        except Exception as e:r={"ok":False,"error":f"{type(e).__name__}: {e}"}
        self.root.after(0,lambda:self.done(r))
    def done(self,r):
        self.progress.stop(); self.write(r); ok=bool(r.get("ok",False)); self.status.set("完成" if ok else "失败"); self.btn.configure(state="normal")
        if ok and r.get("installed"): messagebox.showinfo("GameArt AI Toolkit","操作完成。")
        elif not ok and r.get("error"): messagebox.showerror("GameArt AI Toolkit",str(r["error"]))
    def start_install(self):
        self.install_root=Path(self.path_var.get()).expanduser().resolve(); self._run(self.install_all)
    def install_all(self):
        root=self.install_root
        root.mkdir(parents=True,exist_ok=True)
        installer=ToolkitInstaller(root)
        src=bundled_src()
        if not src.is_dir():
            return {"ok":False,"error":"Installer payload is missing."}
        with tempfile.TemporaryDirectory(prefix="gameart-update-") as td:
            payload=Path(td)/"payload"
            shutil.copytree(src,payload)
            version=f"toolkit-{APP_VERSION}-{time.strftime('%Y%m%d%H%M%S')}"
            staged=installer.stage_update(payload,version)
            if not staged.ok:
                return {"ok":False,"error":staged.error}
            activated=installer.activate(version)
            if not activated.ok:
                return {"ok":False,"error":activated.error}
        results=[]; pi=PluginInstaller(root)
        for n,v in self.vars.items():
            if v.get(): self.write(f"安装插件：{n}"); results.append(pi.install(n).__dict__)
        hi=HostIntegrator(root); hosts={}
        if self.host_vars["maya"].get(): hosts["maya"]=hi.register_maya().__dict__
        if self.host_vars["3ds_max"].get(): hosts["3ds_max"]=hi.register_max().__dict__
        ok=all(x["ok"] for x in results) and all(x["ok"] for x in hosts.values())
        check=self.post_install_check(root) if ok else {"ok":False,"error":"Plugin or host installation failed."}
        smoke=self.startup_smoke_test() if ok and check["ok"] else {"ok":False,"error":"Skipped because preflight checks failed."}
        if ok and check["ok"] and smoke["ok"]: self._write_state(root)
        elif ok and (not check["ok"] or not smoke["ok"]):
            self.write("安装后自检失败，开始回滚…")
            rb=installer.rollback()
            return {"ok":False,"installed":False,"rolled_back":rb.ok,"rollback_error":rb.error,"checks":check,"smoke_test":smoke}
        return {"ok":ok,"installed":ok,"root":str(root),"plugins":results,"hosts":hosts,"checks":check}
    def post_install_check(self, root):
        checks = {}
        try:
            checks["installer_core_import"] = importlib.import_module("src.core.installer") is not None
            checks["plugin_installer_import"] = importlib.import_module("src.core.plugin_installer") is not None
            checks["host_integration_import"] = importlib.import_module("src.core.host_integration") is not None
            checks["launcher_import"] = importlib.import_module("src.launcher") is not None
            checks["payload_present"] = (root / "current").exists()
        except Exception as exc:
            return {"ok":False,"checks":checks,"error":f"{type(exc).__name__}: {exc}"}
        return {"ok":all(checks.values()),"checks":checks}

    def check_update(self):
        try:
            req=urllib.request.Request(UPDATE_URL,headers={"Accept":"application/vnd.github+json","User-Agent":"GameArtToolkit"})
            with urllib.request.urlopen(req,timeout=8) as response:
                data=json.load(response)
            latest=str(data.get("tag_name","")).lstrip("v")
            return {"ok":bool(latest),"current":APP_VERSION,"latest":latest,"update_available":latest!=APP_VERSION,"release_url":data.get("html_url")}
        except Exception as exc:
            return {"ok":False,"current":APP_VERSION,"error":f"{type(exc).__name__}: {exc}"}

    def startup_smoke_test(self):
        try:
            launcher_mod=importlib.import_module("src.launcher")
            launcher=launcher_mod.Launcher()
            result=launcher.start()
            return {"ok":result.get("status")=="ready","result":result}
        except Exception as exc:
            return {"ok":False,"error":f"{type(exc).__name__}: {exc}"}

    def _write_state(self,root):
        (root/"installed.json").write_text('{"product":"GameArt AI Toolkit","installed":true}\n',encoding="utf-8")
    def rollback(self):
        r=ToolkitInstaller(self.install_root).rollback()
        return {"ok":r.ok,"action":"rollback","version":r.version,"error":r.error}

    def repair(self):
        r=ToolkitInstaller(self.install_root).repair(); return {"ok":r.ok,"action":"repair","error":r.error}
    def start_uninstall(self):
        if messagebox.askyesno("确认卸载","将删除 Toolkit 自己的文件和注册项，不删除用户资产。确定继续？"): self._run(self.uninstall)
    def uninstall(self):
        hi=HostIntegrator(self.install_root); hosts={}
        if self.host_vars["maya"].get(): hosts["maya"]=hi.unregister_maya().__dict__
        if self.host_vars["3ds_max"].get(): hosts["3ds_max"]=hi.unregister_max().__dict__
        r=ToolkitInstaller(self.install_root).uninstall()
        return {"ok":r.ok and all(x["ok"] for x in hosts.values()),"action":"uninstall","hosts":hosts,"error":r.error}
    def doctor(self):
        root=self.install_root; return {"ok":True,"installed":(root/"installed.json").is_file(),"root":str(root),"hosts":detect_hosts()}
    def run(self): self.root.mainloop()
if __name__=="__main__": InstallerApp().run()
