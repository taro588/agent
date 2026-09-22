"""Toolkit CLI with safe diagnostics and lifecycle controls."""
from __future__ import annotations
import argparse
import json
from .launcher import Launcher

def _json_default(value): return str(value)

def main() -> None:
    parser=argparse.ArgumentParser(prog="gameart")
    parser.add_argument("command",choices=["doctor","detect","start","install","repair","update","activate","rollback","uninstall","plugin-install","plugin-uninstall","plugin-list","host-register","host-unregister"],nargs="?",default="start")
    parser.add_argument("path",nargs="?",help="Update source directory for 'update'.")
    parser.add_argument("--version",dest="version",help="Version for update/activate/rollback.")
    args=parser.parse_args()
    launcher=Launcher()

    if args.command=="start":
        try:
            from .launcher_gui import LauncherApp
            LauncherApp(launcher).run()
        except Exception as exc:
            print(json.dumps({"status":"degraded","error":f"{type(exc).__name__}: {exc}"},ensure_ascii=False))
        return
    if args.command=="detect":
        payload=[{"name":d.name,"version":d.version,"path":str(d.path)} for d in launcher.detect_dcc()]
    elif args.command=="doctor":
        payload=launcher.doctor()
    elif args.command=="install":
        payload=launcher.installer.install().__dict__
    elif args.command=="repair":
        payload=launcher.installer.repair().__dict__
    elif args.command=="update":
        if not args.path: parser.error("update requires an update source directory")
        payload=launcher.installer.stage_update(args.path,args.version).__dict__
    elif args.command=="activate":
        if not args.version: parser.error("activate requires --version")
        payload=launcher.installer.activate(args.version).__dict__
    elif args.command=="rollback":
        payload=launcher.installer.rollback(args.version).__dict__
    elif args.command=="plugin-install":
        if not args.version:
            parser.error("plugin-install requires --version with the plugin name")
        payload=launcher.plugin_installer.install(args.version).__dict__
    elif args.command=="plugin-uninstall":
        if not args.version:
            parser.error("plugin-uninstall requires --version with the plugin name")
        payload=launcher.plugin_installer.uninstall(args.version).__dict__
    elif args.command=="plugin-list":
        payload=launcher.plugin_installer.installed()
    elif args.command=="host-register":
        from .core.host_integration import HostIntegrator
        integrator=HostIntegrator(launcher.config.install_root)
        host=(args.version or "maya").lower()
        payload=(integrator.register_maya() if host=="maya" else integrator.register_max()).__dict__
    elif args.command=="host-unregister":
        from .core.host_integration import HostIntegrator
        integrator=HostIntegrator(launcher.config.install_root)
        host=(args.version or "maya").lower()
        payload=(integrator.unregister_maya() if host=="maya" else integrator.unregister_max()).__dict__
    elif args.command=="uninstall":
        payload=launcher.installer.uninstall().__dict__
    print(json.dumps(payload,indent=2,ensure_ascii=False,default=_json_default))

if __name__=="__main__":
    main()
