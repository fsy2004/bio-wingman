# -*- coding: utf-8 -*-
"""manifest 的 params_schema → ttk 控件。enum→下拉、boolean→勾选、其余→输入框。"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk


class ParamForm(ttk.Frame):
    def __init__(self, master, schema):
        super().__init__(master)
        self.vars = {}
        props = (schema or {}).get("properties", {})
        row = 0
        for key, spec in props.items():
            title = spec.get("title", key)
            default = spec.get("default")
            ttk.Label(self, text=title).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
            typ = spec.get("type")
            if "enum" in spec:
                init = str(default) if default is not None else str(spec["enum"][0])
                var = tk.StringVar(value=init)
                w = ttk.Combobox(self, textvariable=var, values=[str(x) for x in spec["enum"]],
                                 state="readonly", width=22)
            elif typ == "boolean":
                var = tk.BooleanVar(value=bool(default))
                w = ttk.Checkbutton(self, variable=var)
            else:
                var = tk.StringVar(value="" if default is None else str(default))
                w = ttk.Entry(self, textvariable=var, width=24)
            w.grid(row=row, column=1, sticky="w", pady=5)
            self.vars[key] = (var, typ)
            row += 1
        self.columnconfigure(1, weight=1)

    def values(self) -> dict:
        out = {}
        for key, (var, typ) in self.vars.items():
            v = var.get()
            out[key] = ("true" if v else "false") if typ == "boolean" else str(v)
        return out
