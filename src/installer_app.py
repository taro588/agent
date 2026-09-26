"""Standalone one-click Windows installer UI."""
from __future__ import annotations
import os, shutil, sys, threading, tkinter as tk
import tempfile, time, importlib, json, urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from src.core.installer import ToolkitInstaller
from src.core.plugin_installer import PluginInstaller
from src.core.host_integration import HostIntegrator
from src.dcc.detector import detect_dcc, compatibility

APP_VERSION="2.1.14"
UPDATE_URL="https://api.github.com/repos/taro588/agent/releases/latest"

PLUGINS=[("texture-importer","Maya"),("totex","3ds Max"),("MayaToPainter","Maya"),("SubstancePainterToMaya","Maya"),("rename-lowhigh-proximity","3ds Max"),("fal-texture-pbr-generator","Shared"),("Procedural-PBR","Shared"),("SubstanceDesignerTools","Shared")]

def bundled_root():
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))

def bundled_payload():
    root = bundled_root()
    payload = {}
    for name in ("src", "dcc"):
        path = root / name
        if not path.is_dir():
            raise FileNotFoundError(f"Installer payload is missing: {name}")
        payload[name] = path
    return payload
def detect_hosts():
    return {"maya":bool(os.environ.get("MAYA_LOCATION") or os.environ.get("MAYA_APP_DIR")),
            "3ds_max":bool(os.environ.get("ADSK_3DSMAX_USER_PATH") or os.environ.get("3DSMAX_ROOT"))}

class InstallerApp:
    def __init__(self):
        self.root=tk.Tk(); self.root.title("GameArt AI Toolkit"); self.root.geometry("900x720"); self.root.minsize(820,640)
        self.install_root=Path(os.environ.get("GAMEART_TOOLKIT_HOME",Path.home()/"GameArtAI"/"Toolkit")).expanduser().resolve()
        self.status=tk.StringVar(value="Ready"); self.dcc_info=detect_dcc(); self._build()
    def _build(self):
        o=ttk.Frame(self.root,padding=22); o.pack(fill="both",expand=True)
        ttk.Label(o,text="GameArt AI Toolkit",font=("Segoe UI",22,"bold")).pack(anchor="w")
        ttk.Label(o,text="安装 / 修复 / 更新 / 卸载 · 无需 Python").pack(anchor="w",pady=(2,14))
        row=ttk.Frame(o); row.pack(fill="x"); ttk.Label(row,text="安装位置：").pack(side="left")
        self.path_var=tk.StringVar(value=str(self.install_root)); ttk.Entry(row,textvariable=self.path_var).pack(side="left",fill="x",expand=True,padx=8); ttk.Button(row,text="浏览…",command=self.choose_path).pack(side="right")
        hosts=detect_hosts(); self.host_vars={}
        hf=ttk.LabelFrame(o,text="主机集成"); hf.pack(fill="x",pady=12)
        for i,(h,label) in enumerate((("maya","Maya"),("3ds_max","3ds Max"))):
            detected=self.dcc_info.get(h,[])
            summary=", ".join(f"{x.version}（{'支持' if compatibility(h,x.version) else '不支持'}）" for x in detected) or ("已通过环境变量发现，版本未知" if hosts[h] else "未检测到；可点击“重新检测”")
            v=tk.BooleanVar(value=bool(detected) or hosts[h]); self.host_vars[h]=v; ttk.Checkbutton(hf,text=f"{label}：{summary}",variable=v).grid(row=0,column=i,sticky="w",padx=12,pady=8)
        ttk.Label(o,text="第三方插件（安装时可选）：").pack(anchor="w")
        self.vars={}; g=ttk.Frame(o); g.pack(fill="x")
        for i,(n,h) in enumerate(PLUGINS):
            v=tk.BooleanVar(); self.vars[n]=v; ttk.Checkbutton(g,text=f"{n}  [{h}]",variable=v).grid(row=i//2,column=i%2,sticky="w",padx=8,pady=3)
        b=ttk.Frame(o); b.pack(fill="x",pady=14)
        self.btn=ttk.Button(b,text="一键安装 / 更新",command=self.start_install); self.btn.pack(side="left"); ttk.Button(b,text="回滚上一版本",command=lambda:self._run(self.rollback)).pack(side="left",padx=6)
        ttk.Button(b,text="修复",command=lambda:self._run(self.repair)).pack(side="left",padx=6)
        ttk.Button(b,text="卸载",command=self.start_uninstall).pack(side="left")
        ttk.Button(b,text="重新检测 Max/Maya",command=lambda:self._run(self.redetect_hosts)).pack(side="left",padx=6); ttk.Button(b,text="检查环境",command=lambda:self._run(self.doctor)).pack(side="left",padx=6); ttk.Button(b,text="一键修复",command=lambda:self._run(self.auto_repair)).pack(side="left",padx=6); ttk.Button(b,text="检查更新",command=lambda:self._run(self.check_update)).pack(side="left")
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
        self.progress.stop(); self.write(r)
        if r.get("plugin_verify"):
            for item in r["plugin_verify"]:
                self.write(f"插件自检：{item.get('name')} -> {item.get('status')}")
        if r.get("doctor"):
            for name, value in r["doctor"].get("checks",{}).items():
                self.write(f"{'✓' if value else '✗'} {name}")
        if r.get("actions"):
            for action in r["actions"]:
                self.write(f"修复：{action}")
        ok=bool(r.get("ok",False)); self.status.set("完成" if ok else "需要处理"); self.btn.configure(state="normal")
        if ok and r.get("installed"):
            messagebox.showinfo("GameArt AI Toolkit","安装成功！\n\n核心组件、DCC 脚本目录和已选择插件均已写入并通过安装后自检。\n\n请重新启动 Maya / 3ds Max 后使用。")
        elif not ok and r.get("error"): messagebox.showerror("GameArt AI Toolkit",str(r["error"]))
    def redetect_hosts(self):
        self.dcc_info = detect_dcc()
        return {"ok": True, "dcc": self.dcc_info, "message": "已重新扫描 Maya / 3ds Max。"}

    def start_install(self):
        self.install_root=Path(self.path_var.get()).expanduser().resolve(); self._run(self.install_all)
    def install_all(self):
        root=self.install_root
        self.dcc_info=detect_dcc()
        for host, enabled in self.host_vars.items():
            if not enabled.get():
                continue
            installs=self.dcc_info.get(host, [])
            unsupported=[x.version for x in installs if not compatibility(host,x.version)]
            if unsupported:
                return {"ok":False,"error":f"{host} 检测到不支持的版本：{', '.join(unsupported)}。请取消该主机集成后再安装。"}
        root.mkdir(parents=True,exist_ok=True)
        installer=ToolkitInstaller(root)
        try:
            bundled = bundled_payload()
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        with tempfile.TemporaryDirectory(prefix="gameart-update-") as td:
            payload = Path(td) / "payload"
            payload.mkdir()
            for name, source in bundled.items():
                shutil.copytree(source, payload / name)
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
        plugin_check=pi.verify_all() if ok and check["ok"] else []
        smoke=self.startup_smoke_test() if ok and check["ok"] else {"ok":False,"error":"Skipped because preflight checks failed."}
        plugin_ok=all(x.get("status")=="ok" for x in plugin_check)
        if ok and check["ok"] and plugin_ok and smoke["ok"]: self._write_state(root)
        elif ok and (not check["ok"] or not plugin_ok or not smoke["ok"]):
            self.write("安装后自检失败，开始回滚…")
            rb=installer.rollback()
            return {"ok":False,"installed":False,"rolled_back":rb.ok,"rollback_error":rb.error,"checks":check,"plugin_verify":plugin_check,"smoke_test":smoke}
        return {"ok":ok,"installed":ok,"root":str(root),"plugins":results,"hosts":hosts,"checks":check,"plugin_verify":plugin_check,"smoke_test":smoke}
    def post_install_check(self, root):
        checks = {}
        try:
            checks["installer_core_import"] = importlib.import_module("src.core.installer") is not None
            checks["plugin_installer_import"] = importlib.import_module("src.core.plugin_installer") is not None
            checks["host_integration_import"] = importlib.import_module("src.core.host_integration") is not None
            checks["launcher_import"] = importlib.import_module("src.launcher") is not None
            checks["payload_present"] = (root / "current").exists()
            if self.host_vars["maya"].get():
                checks["maya_script_registration"] = any(Path(p).exists() for p in HostIntegrator(root)._maya_roots())
            if self.host_vars["3ds_max"].get():
                checks["max_script_registration"] = any((p / "GameArtToolkitStartup.ms").exists() for p in HostIntegrator(root)._max_startups())
        except Exception as exc:
            return {"ok":False,"checks":checks,"error":f"{type(exc).__name__}: {exc}"}
        return {"ok":all(checks.values()),"checks":checks}

    def auto_repair(self):
        root=self.install_root
        actions=[]
        if not self._path_writable(root):
            return {"ok":False,"actions":actions,"error":"安装目录不可写，请更换到用户可写目录。"}
        if (root/"installed.json").is_file():
            try:
                r=ToolkitInstaller(root).repair()
                actions.append({"action":"toolkit_repair","ok":r.ok,"error":r.error})
            except Exception as exc:
                actions.append({"action":"toolkit_repair","ok":False,"error":f"{type(exc).__name__}: {exc}"})
            try:
                pi=PluginInstaller(root)
                for item in pi.verify_all():
                    if item.get("status") != "ok":
                        actions.append({"action":"plugin_recheck","name":item.get("name"),"ok":False,"detail":item})
            except Exception as exc:
                actions.append({"action":"plugin_recheck","ok":False,"error":f"{type(exc).__name__}: {exc}"})
        else:
            actions.append({"action":"install_required","ok":False,"detail":"尚未安装 Toolkit，请执行一键安装。"})
        result=self.doctor()
        return {"ok":result["ok"],"actions":actions,"doctor":result}

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
        root=self.install_root
        checks={}
        checks["windows"] = sys.platform == "win32"
        checks["python_runtime"] = sys.version_info >= (3, 10)
        checks["install_root_writable"] = self._path_writable(root)
        checks["bundled_payload"] = all(p.exists() for p in bundled_payload().values())
        checks["github_https"] = self._https_check("https://api.github.com")
        dcc=detect_dcc()
        checks["maya_detected"] = bool(dcc.get("maya")) or bool(os.environ.get("MAYA_LOCATION") or os.environ.get("MAYA_APP_DIR"))
        checks["3ds_max_detected"] = bool(dcc.get("3ds_max")) or bool(os.environ.get("ADSK_3DSMAX_USER_PATH") or os.environ.get("3DSMAX_ROOT"))
        plugin_verify=[]
        if (root/"installed.json").is_file():
            try:
                plugin_verify=PluginInstaller(root).verify_all()
            except Exception as exc:
                checks["plugin_verify"] = False
                return {"ok":False,"checks":checks,"error":f"{type(exc).__name__}: {exc}"}
        checks["plugin_verify"] = all(x.get("status")=="ok" for x in plugin_verify) if plugin_verify else True
        return {"ok":all(checks.values()),"checks":checks,"root":str(root),"dcc":dcc,"plugin_verify":plugin_verify}

    @staticmethod
    def _path_writable(path):
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe=path/".gameart_write_test"
            probe.write_text("ok",encoding="utf-8"); probe.unlink()
            return True
        except OSError:
            return False

    @staticmethod
    def _https_check(url):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"GameArtToolkit"})
            with urllib.request.urlopen(req,timeout=6) as response:
                return 200 <= response.status < 500
        except Exception:
            return False
    def run(self): self.root.mainloop()
if __name__=="__main__": InstallerApp().run()
