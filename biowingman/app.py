# -*- coding: utf-8 -*-
"""入口:DPI 感知 → tkinter 自检 → sv-ttk 轻色主题 → 建主窗 → mainloop。"""
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

    # 成熟控件底座:sv-ttk 提供一致的圆角、焦点、禁用与交互状态;不可用时回退原生主题。
    try:
        from tkinter import ttk
        style = ttk.Style(root)
        try:
            import sv_ttk
            sv_ttk.set_theme("light", root)
        except Exception:
            for _th in ("vista", "winnative", "clam"):
                if _th in style.theme_names():
                    style.theme_use(_th)
                    break
        from . import theme
        theme.apply(style)
    except Exception:
        pass

    # 全局字体:微软雅黑(Win8+ 自带,中英同族清晰)
    try:
        for fn in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(fn).configure(family=theme.FONT, size=10)
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
