# -*- coding: utf-8 -*-
"""入口:DPI 感知 → tkinter 自检 → 原生 Windows 主题 + 微软雅黑字体 → 建主窗 → mainloop。"""
from __future__ import annotations
import sys


def _set_dpi():
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)      # per-monitor(建 Tk 之前)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _no_tkinter():
    msg = ("This Python has no tkinter. Reinstall Python from python.org (with Tcl/Tk).\n"
           "此 Python 缺少 tkinter,请从 python.org 重装 Python(含 Tcl/Tk)。")
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "Bio Wingman", 0x10)
    except Exception:
        print(msg)
    sys.exit(1)


def main():
    _set_dpi()
    try:
        import tkinter as tk
        import tkinter.font as tkfont
    except Exception:
        _no_tkinter()

    root = tk.Tk()
    root.title("Bio Wingman")

    # 主题:用原生 Windows(vista)——干净、切换快。sv-ttk 自绘控件每次切换多耗约 125ms(实测
    # 200ms vs 76ms),且圆角现代感偏"AI 味";原生控件更简洁、更接近 RevMan,故弃用 sv-ttk。
    try:
        from tkinter import ttk
        style = ttk.Style(root)
        for _th in ("vista", "winnative", "clam"):
            if _th in style.theme_names():
                style.theme_use(_th)
                break
        from . import theme
        theme.apply(style)               # 紧凑行高/字号/配色
    except Exception:
        pass

    # 全局字体:微软雅黑(Win8+ 自带,中英同族清晰)
    try:
        for fn in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(fn).configure(family="Microsoft YaHei UI", size=10)
    except Exception:
        pass

    # HiDPI:DPI 感知后 Tk 不自动缩放,按屏幕 DPI 设 scaling
    try:
        root.tk.call("tk", "scaling", root.winfo_fpixels("1i") / 72.0)
    except Exception:
        pass

    from .ui_main import MainWindow
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
