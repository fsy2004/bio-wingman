# -*- coding: utf-8 -*-
"""内存红绿灯:复用 backend/doctor.py。按 (路径, mtime, 方法) 缓存,避免重复读 CSV。
可在工作线程里调(纯计算,不碰 Tk)。纯参数方法返回 None。"""
from __future__ import annotations
import os

_cache = {}


def estimate(manifest: dict, data_path):
    if not data_path:
        return None
    try:
        mt = os.path.getmtime(data_path)
    except OSError:
        mt = 0
    key = (data_path, mt, manifest.get("id"))
    if key in _cache:
        return _cache[key]
    r = None
    try:
        from . import doctor
        dp = doctor.data_profile(data_path)
        est = doctor.estimate_peak(manifest["mem_hint"], dp)
        rl = doctor.redlight(est["predicted_peak_bytes"])
        r = {
            "level": rl.get("level", "green"),
            "peak_gb": est.get("predicted_peak_gb", 0),
            "avail_gb": rl.get("available_gb", 0),
            "n_rows": dp.get("n_rows"), "n_cols": dp.get("n_cols"),
        }
    except Exception:
        r = None
    _cache[key] = r
    return r
