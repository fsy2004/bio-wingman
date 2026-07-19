# -*- coding: utf-8 -*-
"""定位 python.exe(供 Python 类分析用):当前解释器 → PATH → py 启动器 → 常见安装位置。
优先用运行本程序的同一解释器(sys.executable),这样它装了 scanpy 等就能直接跑。结果缓存。"""
from __future__ import annotations
import os
import shutil
import sys
from pathlib import Path

_cache: str | None = None
_probed = False


def _from_launcher():
    """Windows py 启动器:py -3 -c 'import sys;print(sys.executable)'。"""
    py = shutil.which("py")
    if not py:
        return None
    try:
        import subprocess
        out = subprocess.run([py, "-3", "-c", "import sys;print(sys.executable)"],
                             capture_output=True, text=True, timeout=8,
                             creationflags=0x08000000 if os.name == "nt" else 0)
        cand = out.stdout.strip()
        if cand and Path(cand).exists():
            return cand
    except Exception:
        pass
    return None


def _from_glob():
    bases = [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python"),
             os.environ.get("ProgramFiles", ""), r"C:\Python312", r"C:\Python311"]
    for b in bases:
        d = Path(b)
        if d.is_dir():
            cands = sorted(d.glob("**/python.exe"), reverse=True)
            if cands:
                return str(cands[0])
    return None


def find_python(force: bool = False) -> str | None:
    global _cache, _probed
    if _probed and not force:
        return _cache
    # 冻结(PyInstaller)时 sys.executable 是本 exe 自身,不能拿来跑脚本 → 跳过
    frozen = getattr(sys, "frozen", False)
    _cache = ((sys.executable if not frozen else None)
              or shutil.which("python") or shutil.which("python3")
              or _from_launcher() or _from_glob())
    _probed = True
    return _cache


def set_python(path: str):
    """用户在设置里手动指定 python.exe 时调用。"""
    global _cache, _probed
    _cache = path
    _probed = True
