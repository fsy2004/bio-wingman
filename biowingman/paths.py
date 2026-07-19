# -*- coding: utf-8 -*-
"""路径与运行目录。兼容 PyInstaller(_MEIPASS);运行/临时数据写 %LOCALAPPDATA%(短、ASCII、可写)。"""
from __future__ import annotations
import os
import sys
from pathlib import Path


def _base() -> Path:
    # PyInstaller 打包后资源在 _MEIPASS;源码运行时用仓库根(本文件上级的上级)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


ROOT = _base()
MANIFESTS = ROOT / "manifests"
ADAPTERS = ROOT / "adapters" / "meta"
CONFIG = ROOT / "config"
TOOLKIT = ROOT / "toolkit"
EXAMPLES = ADAPTERS / "example_data"

# env_check.py 在 setup/,加入 sys.path 供环境面板复用(doctor 已并入本包)
for _d in (ROOT / "setup",):
    if _d.is_dir() and str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


def run_root() -> Path:
    """运行产物根目录:%LOCALAPPDATA%\\BioWingman\\runs(绝不写 exe 同目录:Program Files 只读)。"""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or str(Path.home())
    p = Path(base) / "BioWingman" / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def config_dir() -> Path:
    """用户配置目录:%APPDATA%\\BioWingman(存语言选择等)。"""
    base = os.environ.get("APPDATA") or str(Path.home())
    p = Path(base) / "BioWingman"
    p.mkdir(parents=True, exist_ok=True)
    return p


def resource_path(rel: str) -> Path:
    return ROOT / rel
