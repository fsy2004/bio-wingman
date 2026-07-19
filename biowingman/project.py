# -*- coding: utf-8 -*-
"""项目文件 .bwproj —— 把当前分析(方法 + 数据 + 列映射 + 参数)存成一个可重开的 JSON。
数据内嵌(自包含,移动文件不失效)。加载时校验 app 戳与版本(学 MetaInsight 的做法)。"""
from __future__ import annotations
import json

from . import __version__


def save(state: dict, path: str):
    out = dict(state)
    out["app"] = "Bio Wingman"
    out["format"] = "bwproj"
    out["version"] = __version__
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("app") != "Bio Wingman" or d.get("format") != "bwproj":
        raise ValueError("不是 Bio Wingman 项目文件 / Not a Bio Wingman project file")
    return d


def version_note(saved_version: str) -> str:
    """存档版本与当前不同 → 返回提示(空串=一致)。"""
    if saved_version and saved_version != __version__:
        return "项目由版本 %s 保存,当前 %s;若行为异常请留意。 / saved by v%s, now v%s." % (
            saved_version, __version__, saved_version, __version__)
    return ""
