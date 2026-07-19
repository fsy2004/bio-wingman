# -*- coding: utf-8 -*-
"""结果区:工具栏(复制图/另存 PNG·矢量PDF、复制/另存表、可复现脚本、Word报告、打开目录)
+ 每个产物一个 tab(图=Pillow,表=Treeview,超 300 行给提示)。空状态有占位。"""
from __future__ import annotations
import csv
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog

from PIL import Image, ImageTk

from .i18n import I18N


class ResultsView(ttk.Frame):
    def __init__(self, master, on_open_folder=None):
        super().__init__(master)
        self._imgs = []
        self._tab_path = {}
        self.outdir = None
        self._on_open_folder = on_open_folder
        self._manifest = None
        self._params = None
        self._outputs = []

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(2, 4))
        # 簇 A:当前产物
        self.btn_png = ttk.Button(bar, style="Toolbutton", command=self._save_png)
        self.btn_pdf = ttk.Button(bar, style="Toolbutton", command=self._save_pdf)
        self.btn_copyimg = ttk.Button(bar, style="Toolbutton", command=self._copy_image)
        self.btn_copy = ttk.Button(bar, style="Toolbutton", command=self._copy_table)
        self.btn_savetbl = ttk.Button(bar, style="Toolbutton", command=self._save_table)
        for b in (self.btn_png, self.btn_pdf, self.btn_copyimg, self.btn_copy, self.btn_savetbl):
            b.pack(side="left", padx=(0, 4))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        # 簇 B:整体
        self.btn_repro = ttk.Button(bar, style="Toolbutton", command=self._save_repro)
        self.btn_report = ttk.Button(bar, style="Toolbutton", command=self._save_report)
        self.btn_open = ttk.Button(bar, style="Toolbutton", command=self._open)
        for b in (self.btn_repro, self.btn_report, self.btn_open):
            b.pack(side="left", padx=(0, 4))

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self._sync())
        self._ph = ttk.Label(self, style="Muted.TLabel", anchor="center")   # 空状态占位
        self.retitle()
        self._sync()
        self._show_placeholder()

    def retitle(self):
        self.btn_png.config(text=I18N.t("save_as") + " " + I18N.t("export_png"))
        self.btn_pdf.config(text=I18N.t("save_as") + " " + I18N.t("export_pdf"))
        self.btn_copyimg.config(text=I18N.t("copy_image"))
        self.btn_copy.config(text=I18N.t("copy_table"))
        self.btn_savetbl.config(text=I18N.t("save_table"))
        self.btn_repro.config(text=I18N.t("export_script"))
        self.btn_report.config(text=I18N.t("export_report"))
        self.btn_open.config(text=I18N.t("open_folder"))
        self._ph.config(text=I18N.t("results_empty"))

    def _show_placeholder(self):
        if not self.nb.tabs():
            self.nb.pack_forget()
            self._ph.pack(fill="both", expand=True, pady=40)
        else:
            self._ph.pack_forget()
            self.nb.pack(fill="both", expand=True)

    def clear(self):
        for t in list(self.nb.tabs()):
            self.nb.forget(t)
        self._imgs.clear()
        self._tab_path.clear()
        self._sync()
        self._show_placeholder()

    def show(self, outputs, outdir=None, manifest=None, params=None):
        self.clear()
        self.outdir = outdir
        self._manifest = manifest
        self._params = params or {}
        self._outputs = list(outputs)
        for o in outputs:
            if o.lower().endswith(".png"):
                self._image_tab(o)
        for o in outputs:
            if o.lower().endswith(".csv") and os.path.basename(o) != "data.csv":
                self._table_tab(o)
        self._sync()
        self._show_placeholder()

    # ---- 工具栏 ----
    def _cur_path(self):
        return self._tab_path.get(self.nb.select())

    def _pdf_for(self, png):
        if not png:
            return None
        pdf = png[:-4] + ".pdf"
        return pdf if os.path.exists(pdf) else None

    def _sync(self):
        p = self._cur_path()
        is_img = bool(p and p.lower().endswith(".png"))
        is_tbl = bool(p and p.lower().endswith(".csv"))
        self.btn_png.config(state="normal" if is_img else "disabled")
        self.btn_pdf.config(state="normal" if (is_img and self._pdf_for(p)) else "disabled")
        self.btn_copyimg.config(state="normal" if is_img else "disabled")
        self.btn_copy.config(state="normal" if is_tbl else "disabled")
        self.btn_savetbl.config(state="normal" if is_tbl else "disabled")
        has_repro = bool(self.outdir and os.path.exists(os.path.join(self.outdir, "reproduce.R")))
        self.btn_repro.config(state="normal" if has_repro else "disabled")
        self.btn_report.config(state="normal" if (self._outputs and self._manifest) else "disabled")
        self.btn_open.config(state="normal" if self.outdir else "disabled")

    def _save_png(self):
        p = self._cur_path()
        if not p:
            return
        dst = filedialog.asksaveasfilename(defaultextension=".png",
                                           initialfile=os.path.basename(p), filetypes=[("PNG", "*.png")])
        if dst:
            shutil.copyfile(p, dst)

    def _save_pdf(self):
        p = self._pdf_for(self._cur_path())
        if not p:
            return
        dst = filedialog.asksaveasfilename(defaultextension=".pdf",
                                           initialfile=os.path.basename(p), filetypes=[("PDF", "*.pdf")])
        if dst:
            shutil.copyfile(p, dst)

    def _copy_image(self):
        p = self._cur_path()
        if not p or not p.lower().endswith(".png"):
            return
        try:
            import io
            import ctypes
            from ctypes import wintypes
            img = Image.open(p).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, "BMP")
            data = buf.getvalue()[14:]     # 去 14 字节 BMP 文件头 → DIB(CF_DIB)
            buf.close()
            u, k = ctypes.windll.user32, ctypes.windll.kernel32
            # ★必须设 argtypes/restype:否则 64 位句柄被 ctypes 当 c_int 截断 → SetClipboardData 失败
            k.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
            k.GlobalAlloc.restype = wintypes.HGLOBAL
            k.GlobalLock.argtypes = [wintypes.HGLOBAL]
            k.GlobalLock.restype = ctypes.c_void_p
            k.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
            u.OpenClipboard.argtypes = [wintypes.HWND]
            u.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
            u.SetClipboardData.restype = wintypes.HANDLE
            hg = k.GlobalAlloc(0x0002, len(data))     # GMEM_MOVEABLE
            ptr = k.GlobalLock(hg)
            ctypes.memmove(ptr, data, len(data))
            k.GlobalUnlock(hg)
            if u.OpenClipboard(None):
                u.EmptyClipboard()
                u.SetClipboardData(8, hg)             # CF_DIB
                u.CloseClipboard()
        except Exception:
            pass

    def _copy_table(self):
        p = self._cur_path()
        if not p or not p.lower().endswith(".csv"):
            return
        try:
            with open(p, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            self.clipboard_clear()
            self.clipboard_append("\n".join("\t".join(r) for r in rows))
        except Exception:
            pass

    def _save_table(self):
        p = self._cur_path()
        if not p or not p.lower().endswith(".csv"):
            return
        dst = filedialog.asksaveasfilename(defaultextension=".csv",
                                           initialfile=os.path.basename(p), filetypes=[("CSV", "*.csv")])
        if dst:
            shutil.copyfile(p, dst)

    def _save_repro(self):
        from tkinter import messagebox
        if not self.outdir:
            return
        src_r = os.path.join(self.outdir, "reproduce.R")
        if not os.path.exists(src_r):
            return
        dst = filedialog.askdirectory(title=I18N.t("export_script"))
        if not dst:
            return
        try:
            shutil.copyfile(src_r, os.path.join(dst, "reproduce.R"))
            src_d = os.path.join(self.outdir, "data.csv")
            if os.path.exists(src_d):
                shutil.copyfile(src_d, os.path.join(dst, "data.csv"))
            messagebox.showinfo("Bio Wingman", I18N.t("repro_done", d=dst))
        except Exception:
            pass

    def _save_report(self):
        from tkinter import messagebox
        if not (self._outputs and self._manifest):
            return
        dst = filedialog.asksaveasfilename(
            defaultextension=".docx", initialfile=(self._manifest.get("id", "report") + ".docx"),
            filetypes=[("Word", "*.docx")])
        if not dst:
            return
        import threading
        m, p, o, od = self._manifest, self._params, list(self._outputs), self.outdir
        self.btn_report.config(state="disabled")

        def work():
            try:
                from . import report
                report.build_report(m, p, o, od, dst)
                self.after(0, lambda: messagebox.showinfo("Bio Wingman", I18N.t("report_done", d=dst)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Bio Wingman", I18N.t("report_fail") + "\n" + str(e)))
            finally:
                self.after(0, self._sync)
        threading.Thread(target=work, daemon=True).start()

    def _open(self):
        if self._on_open_folder:
            self._on_open_folder()

    # ---- tabs ----
    def _image_tab(self, path):
        frame = ttk.Frame(self.nb)
        try:
            im = Image.open(path)
            im.thumbnail((960, 660))
            ph = ImageTk.PhotoImage(im)
            self._imgs.append(ph)
            ttk.Label(frame, image=ph).pack(padx=8, pady=8)
        except Exception as e:
            ttk.Label(frame, text=f"(cannot display {os.path.basename(path)}: {e})").pack(padx=8, pady=8)
        self.nb.add(frame, text=os.path.basename(path))
        self._tab_path[str(frame)] = path

    def _table_tab(self, path):
        frame = ttk.Frame(self.nb)
        tree = ttk.Treeview(frame, show="headings", height=13)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        total = 0
        try:
            with open(path, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            if rows:
                cols = rows[0]
                total = len(rows) - 1
                tree["columns"] = list(range(len(cols)))
                for i, c in enumerate(cols):
                    tree.heading(i, text=c)
                    tree.column(i, width=120, anchor="w", stretch=False)
                for r in rows[1:301]:
                    tree.insert("", "end", values=r)
        except Exception as e:
            ttk.Label(frame, text=f"(cannot read: {e})").pack(padx=8, pady=8)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        if total > 300:      # ★行数截断提示(原先静默只显前 300)
            ttk.Label(frame, style="Muted.TLabel",
                      text=I18N.t("rows_shown", n=300, total=total)).grid(row=2, column=0, sticky="w", pady=(2, 0))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.nb.add(frame, text=os.path.basename(path))
        self._tab_path[str(frame)] = path
