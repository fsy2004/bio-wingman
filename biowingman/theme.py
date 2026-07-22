# -*- coding: utf-8 -*-
"""Apple-inspired desktop tokens layered on the sv-ttk widget theme.

sv-ttk supplies the mature control assets and interaction states.  This module
only maps Wingman's information hierarchy to macOS-like system materials,
spacing, typography, and semantic colours.
"""
from __future__ import annotations

FONT = "Segoe UI Variable Text"
DISPLAY = "Segoe UI Variable Display"
MONO = "Cascadia Mono"

# macOS light materials / semantic labels
BACKGROUND = "#F5F5F7"
CANVAS = "#FFFFFF"
TOOLBAR = "#F6F6F8"
SIDEBAR = "#ECECF1"
SURFACE = SIDEBAR
SURFACE_STRONG = "#E2E2E7"
FILL = "#E8E8ED"
BORDER = "#D2D2D7"
TEXT = "#1D1D1F"
MUTED = "#5F5F63"

# Apple system accent colours
PRIMARY = "#007AFF"
PRIMARY_HOVER = "#0066D6"
PRIMARY_SOFT = "#DCEBFF"
ON_PRIMARY = "#FFFFFF"
RING = "#0A84FF"
ACCENT = PRIMARY
ACCENT_SOFT = PRIMARY_SOFT

SIG = "#FF3B30"
WARN = "#C46A00"
OK = "#248A3D"
LIGHT = {"green": OK, "yellow": WARN, "red": SIG}


def apply(style):
    """Tune typography and information density without replacing sv-ttk assets."""
    style.configure("TFrame", background=CANVAS)
    style.configure("App.TFrame", background=BACKGROUND)
    style.configure("Workspace.TFrame", background=BACKGROUND)
    style.configure("Page.TFrame", background=BACKGROUND)
    style.configure("Panel.TFrame", background=CANVAS)
    style.configure("Hero.TFrame", background=BACKGROUND, relief="flat")
    style.configure("TLabel", background=CANVAS, foreground=TEXT, font=(FONT, 10))
    style.configure("TRadiobutton", background=CANVAS, foreground=TEXT, font=(FONT, 10))
    style.configure("TCheckbutton", background=CANVAS, foreground=TEXT, font=(FONT, 10))

    style.configure(
        "Treeview", font=(FONT, 9), rowheight=30, indent=16, borderwidth=0,
        background=CANVAS, fieldbackground=CANVAS, foreground=TEXT,
    )
    style.map(
        "Treeview", background=[("selected", PRIMARY_SOFT)],
        foreground=[("selected", TEXT)],
    )
    style.configure(
        "Sidebar.Treeview", font=(FONT, 9), rowheight=30, indent=17,
        borderwidth=0, relief="flat", background=SIDEBAR,
        fieldbackground=SIDEBAR, foreground=TEXT,
    )
    style.map(
        "Sidebar.Treeview", background=[("selected", PRIMARY_SOFT)],
        foreground=[("selected", TEXT)],
    )
    style.configure(
        "Treeview.Heading", font=(FONT, 9, "bold"), foreground=TEXT,
        background=BACKGROUND, relief="flat", padding=(8, 7),
    )

    style.configure("HeroTitle.TLabel", font=(DISPLAY, 15, "bold"), foreground=TEXT, background=BACKGROUND)
    style.configure("HeroSub.TLabel", font=(FONT, 9), foreground=MUTED, background=BACKGROUND)
    style.configure("HeroBody.TLabel", font=(FONT, 10), foreground=TEXT, background=BACKGROUND)
    style.configure("Method.TLabel", font=(DISPLAY, 15, "bold"), foreground=TEXT, background=BACKGROUND)
    style.configure("Section.TLabel", font=(FONT, 9, "bold"), foreground=MUTED, background=CANVAS)
    style.configure("Body.TLabel", font=(FONT, 10), foreground=TEXT, background=CANVAS)
    style.configure("Muted.TLabel", font=(FONT, 9), foreground=MUTED, background=CANVAS)
    style.configure("Mono.TLabel", font=(MONO, 9), foreground=TEXT, background=CANVAS)

    style.configure("TNotebook", background=CANVAS, borderwidth=0)
    style.configure("TNotebook.Tab", font=(FONT, 9), padding=(12, 7))
    style.map("TNotebook.Tab", font=[("selected", (FONT, 9, "bold"))])
    style.configure("Workspace.TNotebook", background=BACKGROUND, borderwidth=0, tabmargins=(0, 0, 0, 8))
    style.configure("Workspace.TNotebook.Tab", font=(FONT, 10), padding=(18, 8))
    style.map(
        "Workspace.TNotebook.Tab",
        font=[("selected", (FONT, 10, "bold"))],
        foreground=[("selected", TEXT), ("!selected", MUTED)],
    )
    style.configure("TSeparator", background=BORDER)

    # Accent.TButton is implemented by sv-ttk; keep its rounded image assets.
    style.configure("TButton", font=(FONT, 10), padding=(12, 7))
    style.configure("Accent.TButton", font=(FONT, 10, "bold"), padding=(18, 9))
    style.configure("Toolbutton", font=(FONT, 9), padding=(9, 6))
    style.configure("Sidebar.TEntry", font=(FONT, 10), padding=(10, 8))
    style.configure("Card.TLabelframe", background=CANVAS, borderwidth=1, relief="solid")
    style.configure(
        "Card.TLabelframe.Label", font=(FONT, 9, "bold"), foreground=MUTED,
        background=CANVAS,
    )
