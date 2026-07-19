# -*- coding: utf-8 -*-
"""
Bio Wingman 环境体检 —— 检测 Python / R 及各自所需的包是否就绪。
既可命令行直接跑(python setup/env_check.py),也被后端 /api/envcheck 调用喂给界面环境面板。
只检测、不安装;安装交给 setup/install.ps1 或界面「一键装」按钮。
"""
from __future__ import annotations
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

def _load_req() -> dict:
    try:
        p = Path(__file__).resolve().parent.parent / "config" / "requirements.json"
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _minver(s: str, fallback: tuple) -> tuple:
    try:
        parts = [int(x) for x in str(s).split(".")[:2]]
        return tuple(parts) if len(parts) == 2 else fallback
    except Exception:
        return fallback


_REQ = _load_req()
# 依赖清单与版本门槛的单一权威来源 = config/requirements.json(读不到则用兜底)
PY_PKGS = _REQ.get("python_packages") or ["psutil", "sv-ttk", "Pillow"]
# pip 发行名 → import 名(不同才需列;如 sv-ttk→sv_ttk、Pillow→PIL)。修:原先按发行名 find_spec 永远报缺。
PY_IMPORTS = _REQ.get("python_import_names") or {}
R_PKGS = (_REQ.get("r_packages") or ["ggplot2", "ggrepel", "circlize", "dplyr", "reshape2",
                                     "glmnet", "pROC", "rms", "rmda", "ggpubr", "WGCNA", "BiocManager"]) \
    + (_REQ.get("r_bioc_packages") or ["limma", "ComplexHeatmap", "clusterProfiler", "org.Hs.eg.db"])
PY_MIN = _minver(_REQ.get("python_min", "3.9"), (3, 9))
R_MIN = _minver(_REQ.get("r_min", "4.0"), (4, 0))


def _find_r() -> str | None:
    for exe in ("Rscript", "Rscript.exe"):
        p = shutil.which(exe)
        if p:
            return p
    # PATH 里没有时再扫常见安装位置(含 winget 用户级、非 C 盘)
    bases = [r"C:\Program Files\R", r"C:\Program Files (x86)\R", r"D:\R", r"D:\Program Files\R"]
    la = os.environ.get("LOCALAPPDATA")
    if la:
        bases.append(str(Path(la) / "Programs" / "R"))
    for base in bases:
        bp = Path(base)
        if bp.exists():
            cands = sorted(bp.glob("**/bin/Rscript.exe"), reverse=True)   # 多版本取最新
            if cands:
                return str(cands[0])
    return None


def _has(pkg: str) -> bool:
    name = PY_IMPORTS.get(pkg, pkg)          # 用 import 名而非 pip 发行名
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def check_python() -> dict:
    v = sys.version_info
    pkgs = {p: _has(p) for p in PY_PKGS}
    return {
        "present": True,
        "version": f"{v.major}.{v.minor}.{v.micro}",
        "version_ok": (v.major, v.minor) >= PY_MIN,
        "packages": pkgs,
        "tkinter": _has("tkinter"),          # 原生界面必需(stdlib;精简版 Python 可能缺)
        "missing": [p for p, ok in pkgs.items() if not ok],
    }


def check_r() -> dict:
    rscript = _find_r()
    if not rscript:
        return {"present": False, "rscript": None, "version": None, "version_num": None,
                "version_ok": False, "packages": {p: False for p in R_PKGS}, "missing": R_PKGS[:]}
    try:
        ver = subprocess.run([rscript, "--version"], capture_output=True, text=True, timeout=30)
        vtxt = (ver.stdout or ver.stderr or "").splitlines()[0].strip()
    except Exception:
        vtxt = "unknown"
    # 一次性问 R:哪些包缺
    rcode = ("ip<-rownames(installed.packages()); "
             "need<-c(%s); cat(paste(need[!need %%in%% ip], collapse=','))"
             % ",".join(f'\"{p}\"' for p in R_PKGS))
    try:
        out = subprocess.run([rscript, "-e", rcode], capture_output=True, text=True, timeout=120)
        missing = [m for m in (out.stdout.strip().split(",") if out.stdout.strip() else []) if m]
    except Exception:
        missing = R_PKGS[:]
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", vtxt or "")   # R 版本门槛:metafor 5.x/新包需 R ≥ 4.0
    vnum = "{}.{}.{}".format(m.group(1), m.group(2), m.group(3) or "0") if m else None
    version_ok = (int(m.group(1)), int(m.group(2))) >= R_MIN if m else True
    return {
        "present": True, "rscript": rscript, "version": vtxt, "version_num": vnum,
        "version_ok": version_ok,
        "packages": {p: (p not in missing) for p in R_PKGS},
        "missing": missing,
    }


def check() -> dict:
    py = check_python()
    r = check_r()
    ready = (py["version_ok"] and not py["missing"]
             and r["present"] and r.get("version_ok", True) and not r["missing"])
    return {"ready": ready, "python": py, "r": r}


def _print(rep: dict):
    def line(name, ok, extra=""):
        print(f"  {'✅' if ok else '❌'} {name:22} {extra}")
    print("=" * 58 + "\nBio Wingman 环境体检\n" + "=" * 58)
    py, r = rep["python"], rep["r"]
    line("Python", py["version_ok"], py["version"] + ("" if py["version_ok"] else "  ⚠️ 需 ≥ 3.9"))
    for p, ok in py["packages"].items():
        line(f"  py: {p}", ok)
    r_ok = r["present"] and r.get("version_ok", True)
    line("R (Rscript)", r_ok, (r["version"] or "未找到") + ("" if r.get("version_ok", True) else "  ⚠️ 建议 ≥ 4.0"))
    for p, ok in r["packages"].items():
        line(f"  R: {p}", ok)
    print("-" * 58)
    print("  " + ("🟢 全部就绪,可直接运行 Bio Wingman。"
                  if rep["ready"] else
                  "🟡 有缺失。运行 setup/install.ps1 或界面「一键装」补齐(见下)。"))
    if py["missing"]:
        print("  缺 Python 包:", ", ".join(py["missing"]))
    if not r["present"]:
        print("  ❗ 未检测到 R,请先安装 R 4.x(https://cran.r-project.org 或 winget install RProject.R)")
    elif r["missing"]:
        print("  缺 R 包:", ", ".join(r["missing"]))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rep = check()
    _print(rep)
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False))
