"""Toolkit command-line entry point for Painter installation diagnostics."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from plugins.substance_painter.installer import PainterInstaller

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["detect","install","verify","uninstall","command"])
    parser.add_argument("--root",default=".")
    parser.add_argument("--exe",default=None)
    args=parser.parse_args()
    installer=PainterInstaller(Path(args.root))
    if args.action=="detect": result={"executables":[str(x) for x in installer.detect_executables()]}
    elif args.action=="install": result=installer.install()
    elif args.action=="verify": result=installer.verify()
    elif args.action=="uninstall": result=installer.uninstall()
    else: result={"command":installer.command_line(args.exe)}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
