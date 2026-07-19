# -*- coding: utf-8 -*-
"""近单色 + 一个钢蓝强调色的紧凑主题(RevMan 观感)。在选定 ttk 原生主题后调 apply()。
颜色只在结果统计里用语义色,界面装饰一律克制。"""
from __future__ import annotations

FONT = "Microsoft YaHei UI"      # Win8+ 自带,中英同族清晰
MONO = "Consolas"

# 浅色(主)
CANVAS = "#FFFFFF"
SURFACE = "#F5F6F7"
BORDER = "#DADDE1"
TEXT = "#1B1E21"
MUTED = "#6B7178"
ACCENT = "#2A6F97"
ACCENT_SOFT = "#E1ECF2"
# 语义色(仅用于结果数值,不做界面装饰)
SIG = "#B23A3A"
WARN = "#C9922E"
OK = "#3F8F5B"

LIGHT = {"green": OK, "yellow": WARN, "red": SIG}


def apply(style):
    """在选定 ttk 主题后调:覆盖行高/字号/间距,让 RevMan 式紧凑生效。"""
    style.configure("Treeview", font=(FONT, 9), rowheight=22, indent=14,
                    borderwidth=0, background=CANVAS, fieldbackground=CANVAS)
    style.map("Treeview", background=[("selected", ACCENT_SOFT)], foreground=[("selected", TEXT)])
    style.configure("Group.Treeview", font=(FONT, 9, "bold"))

    style.configure("Method.TLabel", font=(FONT, 12, "bold"), foreground=TEXT)
    style.configure("Muted.TLabel", font=(FONT, 9), foreground=MUTED)
    style.configure("Section.TLabel", font=(FONT, 9, "bold"), foreground=MUTED)
    style.configure("Mono.TLabel", font=(MONO, 9), foreground=TEXT)
    style.configure("TButton", font=(FONT, 10), padding=(12, 4))
    style.configure("Accent.TButton", font=(FONT, 10, "bold"), padding=(14, 5))
    style.configure("Toolbutton", font=(FONT, 9), padding=(8, 3))
