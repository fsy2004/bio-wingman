# -*- coding: utf-8 -*-
"""定位 Rscript.exe:PATH → 注册表(R-core InstallPath,64/32 视图)→ 文件 glob。
R 的 Windows 安装器默认不加 PATH,所以三级探测必不可少。结果缓存。"""
from __future__ import annotations
import os
import shutil
from pathlib import Path

_cache: str | None = None
_probed = False


def _from_registry():
    try:
        import winreg
    except Exception:
        return None
    subkeys = [r"SOFTWARE\R-core\R64", r"SOFTWARE\R-core\R"]
    for root in (getattr(__import__("winreg"), "HKEY_LOCAL_MACHINE"),
                 getattr(__import__("winreg"), "HKEY_CURRENT_USER")):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            for sub in subkeys:
                try:
                    with winreg.OpenKey(root, sub, 0, winreg.KEY_READ | view) as k:
                        path, _ = winreg.QueryValueEx(k, "InstallPath")
                except OSError:
                    continue
                for rs in (Path(path) / "bin" / "x64" / "Rscript.exe", Path(path) / "bin" / "Rscript.exe"):
                    if rs.exists():
                        return str(rs)
    return None


def _from_glob():
    bases = [os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", ""),
             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"), r"D:\R"]
    for b in bases:
        rdir = Path(b) / "R" if b else None
        if rdir and rdir.is_dir():
            cands = sorted(rdir.glob("**/bin/**/Rscript.exe"), reverse=True)
            if cands:
                return str(cands[0])
    return None


def find_rscript(force: bool = False) -> str | None:
    global _cache, _probed
    if _probed and not force:
        return _cache
    _cache = shutil.which("Rscript") or _from_registry() or _from_glob()
    _probed = True
    return _cache


def set_rscript(path: str):
    """用户在设置里手动指定 Rscript.exe 时调用。"""
    global _cache, _probed
    _cache = path
    _probed = True
