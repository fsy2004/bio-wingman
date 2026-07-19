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
    """在选定 ttk 主题后调:覆盖行高/字号/间距,让紧凑而有层次的观感生效。
    四级字阶(Method 13 / Section 9粗灰 / Body 9正文 / Muted 9灰) + 启用 SURFACE 分区带 +
    配 Treeview.Heading / Notebook.Tab / Separator,消除"满屏纯白 9pt 灰字"的单调感。"""
    style.configure("Treeview", font=(FONT, 9), rowheight=24, indent=14,
                    borderwidth=0, background=CANVAS, fieldbackground=CANVAS)
    style.map("Treeview", background=[("selected", ACCENT_SOFT)], foreground=[("selected", TEXT)])
    style.configure("Group.Treeview", font=(FONT, 9, "bold"))
    # 表头(结果表 / 输入格式卡):浅灰底拉层次(vista 可控)
    style.configure("Treeview.Heading", font=(FONT, 9, "bold"), foreground=TEXT,
                    background=SURFACE, relief="flat")
    style.map("Treeview.Heading", background=[("active", ACCENT_SOFT)])

    # 四级文字层级(新增 Body 中间层级,填补 13→9 的断层)
    style.configure("Method.TLabel", font=(FONT, 13, "bold"), foreground=TEXT)
    style.configure("Section.TLabel", font=(FONT, 9, "bold"), foreground=MUTED)
    style.configure("Body.TLabel", font=(FONT, 9), foreground=TEXT)
    style.configure("Muted.TLabel", font=(FONT, 9), foreground=MUTED)
    style.configure("Mono.TLabel", font=(MONO, 9), foreground=TEXT)

    # Notebook 活动页加粗(结果区内部 Notebook 同惠);分隔线用 BORDER
    style.configure("TNotebook", background=CANVAS, borderwidth=0)
    style.configure("TNotebook.Tab", font=(FONT, 9), padding=(10, 4))
    style.map("TNotebook.Tab", font=[("selected", (FONT, 9, "bold"))])
    style.configure("TSeparator", background=BORDER)

    style.configure("TButton", font=(FONT, 10), padding=(12, 4))
    style.configure("Accent.TButton", font=(FONT, 10, "bold"), padding=(14, 5))
    style.configure("Toolbutton", font=(FONT, 9), padding=(8, 3))
    style.configure("Card.TLabelframe", background=CANVAS, borderwidth=1, relief="solid")
    style.configure("Card.TLabelframe.Label", font=(FONT, 9, "bold"), foreground=MUTED, background=CANVAS)
