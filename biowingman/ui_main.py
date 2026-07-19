# -*- coding: utf-8 -*-
"""主窗口:左=分组方法树,右=方法详情。RevMan 式紧凑、克制,无营销文案。
性能:红绿灯去主线程(缓存+防抖+后台线程);参数表单按方法缓存不重建。"""
from __future__ import annotations
import csv
import os
import queue
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog

from . import engine
from . import theme
from . import validate as mw_validate
from .i18n import I18N

try:
    import tksheet
    _HAS_TKSHEET = True
except Exception:
    _HAS_TKSHEET = False
from .form import ParamForm
from .results import ResultsView
from .redlight import estimate as mem_estimate
from .rlocate import find_rscript, set_rscript


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.sel = None
        self.data_source = tk.StringVar(value="example")
        self.user_file = None
        self.run = None
        self._forms = {}          # method_id -> ParamForm(缓存,避免重建)
        self._cur_form = None     # 当前显示的表单(切换时只忘它,不遍历全部)
        self._rl_job = None
        self._rl_tok = 0
        self._rl_q = queue.Queue()
        self._map_vars = {}       # role -> StringVar(用户列名映射)
        self._headers = []

        root.geometry("1120x720")
        root.minsize(900, 600)
        self._build_menu()
        self._build_top()
        self._build_status()     # 底部状态栏:接管运行反馈(须早于 body 的 pack 以占住底部)
        self._build_body()
        I18N.bind(self._on_lang)
        self._select_first()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)   # 关窗前杀掉在跑的 R,避免孤儿进程

    def _on_close(self):
        try:
            if self.run and not self.run.done:
                self.run.cancel()
        except Exception:
            pass
        self.root.destroy()

    def _build_menu(self):
        self._menubar = tk.Menu(self.root)
        self._filemenu = tk.Menu(self._menubar, tearoff=0)
        self._menubar.add_cascade(menu=self._filemenu)   # 文案在 _on_lang 里贴
        self.root.config(menu=self._menubar)

    def _relabel_menu(self):
        try:
            self._menubar.entryconfig(1, label=I18N.t("menu_file"))
            self._filemenu.delete(0, "end")
            self._filemenu.add_command(label=I18N.t("proj_open"), command=self._open_project)
            self._filemenu.add_command(label=I18N.t("proj_save"), command=self._save_project)
            self._filemenu.add_separator()
            self._filemenu.add_command(label=I18N.t("menu_exit"), command=self.root.destroy)
        except Exception:
            pass

    # ---------- 项目 .bwproj ----------
    def get_project_state(self):
        if not self.sel:
            return None
        form = self._cur_form
        st = {
            "method_id": self.sel["id"],
            "data_source": self.data_source.get(),
            "params": (form.values() if form else {}),
            "mapping": self._collect_map(),
        }
        ds = self.data_source.get()
        if ds in ("mine", "paste", "grid") and self.user_file and os.path.exists(self.user_file):
            st["data_name"] = os.path.basename(self.user_file)
            fmt = (engine.primary_input(self.sel) or {}).get("format")
            # 文本输入(粘贴/表格/csv)才内嵌工程便于携带;二进制(h5ad/rds/maf)或目录只存路径引用,
            # 否则 latin-1 硬解二进制塞进 JSON → 重开损坏 + 工程体积爆炸。
            text_ok = ds in ("paste", "grid") or fmt in (None, "csv", "tsv", "txt")
            if text_ok and os.path.isfile(self.user_file):
                for enc in ("utf-8-sig", "gb18030", "latin-1"):
                    try:
                        st["data_csv"] = open(self.user_file, encoding=enc).read()
                        break
                    except Exception:
                        continue
            else:
                st["data_path"] = os.path.abspath(self.user_file)
        return st

    def apply_project_state(self, st):
        mid = st.get("method_id")
        if not mid:
            return
        self.pick(mid)                                   # 载方法 + 建表单(会重置为示例)
        ds = st.get("data_source", "example")
        if ds in ("mine", "paste", "grid") and st.get("data_csv"):
            from .paths import run_root
            d = run_root() / "_project"
            d.mkdir(parents=True, exist_ok=True)
            safe = os.path.basename(st.get("data_name") or "data.csv")   # ★防路径穿越:恶意 .bwproj 可能给 ..\ 或绝对路径
            if not safe or safe in (".", "..") or "/" in safe or "\\" in safe:
                safe = "data.csv"
            f = d / safe
            try:
                f.write_text(st["data_csv"], encoding="utf-8")
                self.user_file = str(f)
                self.data_source.set(ds)
                self._on_source()                        # 触发体检 + 重建映射
            except Exception:
                pass
        elif ds == "mine" and st.get("data_path"):        # 二进制/目录:按路径引用还原(文件须仍在原处)
            p = st["data_path"]
            if os.path.exists(p):
                self.user_file = p
                self.data_source.set("mine")
                self._on_source()
        for r, col in (st.get("mapping") or {}).items():  # 映射在 _rebuild_map 之后设
            if r in self._map_vars:
                self._map_vars[r][0].set(col)
        form = self._cur_form
        if form:
            for k, v in (st.get("params") or {}).items():
                if k in form.vars:
                    var, typ = form.vars[k]
                    if typ == "boolean":
                        var.set(str(v).lower() in ("true", "1", "yes", "t"))
                    else:
                        var.set(v)
        self._refresh_file_label()
        self._update_run_button()

    def _save_project(self):
        from tkinter import filedialog, messagebox
        st = self.get_project_state()
        if not st:
            messagebox.showinfo("Bio Wingman", I18N.t("proj_none"))
            return
        dst = filedialog.asksaveasfilename(defaultextension=".bwproj",
                                           initialfile=(self.sel["id"] + ".bwproj"),
                                           filetypes=[("Bio Wingman project", "*.bwproj")])
        if not dst:
            return
        try:
            from . import project
            project.save(st, dst)
            messagebox.showinfo("Bio Wingman", I18N.t("proj_saved", d=dst))
        except Exception as e:
            messagebox.showerror("Bio Wingman", str(e))

    def _open_project(self):
        from tkinter import filedialog, messagebox
        src = filedialog.askopenfilename(filetypes=[("Bio Wingman project", "*.bwproj"), ("All", "*.*")])
        if not src:
            return
        try:
            from . import project
            st = project.load(src)
            note = project.version_note(st.get("version", ""))
            self.apply_project_state(st)
            if note:
                messagebox.showwarning("Bio Wingman", note)
        except Exception as e:
            messagebox.showerror("Bio Wingman", str(e))

    def _init_sash(self):
        try:
            self._vpane.update_idletasks()
            h = self._vpane.winfo_height()
            if h < 80:                       # 尚未 realize,稍后重试(sashpos 过早会被忽略)
                self.root.after(60, self._init_sash)
                return
            self._vpane.sashpos(0, int(h * 0.42))   # 控件区上占 ~42%,结果区下占多数
        except Exception:
            pass

    def _wheel(self, event):
        # 滚轮:滚动指针所在的可滚区(控件画布 / 方法树 / 结果表 / 日志),互不抢占
        step = int(-event.delta / 120) or (-1 if event.delta > 0 else 1)
        try:
            w = self.root.winfo_containing(event.x_root, event.y_root)
        except Exception:
            return
        while w is not None:
            if w is self._top_canvas:
                self._top_canvas.yview_scroll(step, "units")
                return
            if isinstance(w, (ttk.Treeview, tk.Text, tk.Canvas)):
                try:
                    w.yview_scroll(step, "units")
                except Exception:
                    pass
                return
            w = getattr(w, "master", None)

    def _select_first(self):
        n2m = getattr(self, "_node_to_mid", {})
        target = "meta_pw_forest" if "meta_pw_forest" in n2m.values() else None
        for node, mid in n2m.items():
            if target is None or mid == target:
                self.tree.selection_set(node)
                self.tree.see(node)
                self.pick(mid)
                return

    # ---------- 顶栏(极简) ----------
    def _build_top(self):
        top = ttk.Frame(self.root, padding=(12, 6))
        top.pack(side="top", fill="x")
        self.lbl_rstat = ttk.Label(top, style="Muted.TLabel")
        self.lbl_rstat.pack(side="left")
        self.btn_lang = ttk.Button(top, width=6, style="Toolbutton", command=I18N.toggle)
        self.btn_lang.pack(side="right")
        ttk.Separator(self.root, orient="horizontal").pack(side="top", fill="x")

    # ---------- 底部状态栏 ----------
    def _build_status(self):
        bar = tk.Frame(self.root, bg=theme.SURFACE)
        bar.pack(side="bottom", fill="x")           # ★须早于 body.pack 以占住底部
        ttk.Separator(bar, orient="horizontal").pack(side="top", fill="x")
        inner = tk.Frame(bar, bg=theme.SURFACE)
        inner.pack(fill="x", padx=8, pady=2)
        self.lbl_status = tk.Label(inner, bg=theme.SURFACE, fg=theme.MUTED, font=(theme.FONT, 9), anchor="w")
        self.lbl_status.pack(side="left")
        ttk.Sizegrip(inner).pack(side="right")
        self.lbl_ctx = tk.Label(inner, bg=theme.SURFACE, fg=theme.MUTED, font=(theme.FONT, 9), anchor="e")
        self.lbl_ctx.pack(side="right", padx=8)
        self.pbar = ttk.Progressbar(inner, mode="indeterminate", length=120)   # 仅运行时 pack

    def _set_status(self, text):
        try:
            self.lbl_status.config(text=text)
        except Exception:
            pass

    # ---------- 主体 ----------
    def _build_body(self):
        body = ttk.Frame(self.root)
        body.pack(side="top", fill="both", expand=True)

        left = ttk.Frame(body, padding=(6, 6))
        left.pack(side="left", fill="y")
        # 方法即时搜索框(带占位提示,免额外标签占行;中英双标题不分大小写子串匹配)
        self.q_var = tk.StringVar()
        self.ent_search = ttk.Entry(left, textvariable=self.q_var, foreground=theme.MUTED)
        self.ent_search.pack(side="top", fill="x", pady=(0, 5))
        self._search_ph = True
        self.ent_search.bind("<FocusIn>", self._search_focus_in)
        self.ent_search.bind("<FocusOut>", self._search_focus_out)
        self.ent_search.bind("<KeyRelease>", self._search_key)
        treewrap = ttk.Frame(left)
        treewrap.pack(side="top", fill="both", expand=True)
        self.tree = ttk.Treeview(treewrap, show="tree", selectmode="browse")
        self.tree.column("#0", width=230, minwidth=190)
        self.tree.tag_configure("group", font=(theme.FONT, 9, "bold"), background=theme.SURFACE)
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(treewrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        ttk.Separator(body, orient="vertical").pack(side="left", fill="y")

        right = ttk.Frame(body, padding=(14, 10))
        right.pack(side="left", fill="both", expand=True)
        # 日志抽屉:先建先 pack(side=bottom),让下面 expand 的 vpane 不吃掉它。
        # 默认收起(仅 26px 标题带:状态点 + 折叠钮 + 最新一行);出错自动展开。
        self._build_log_drawer(right)
        # ★垂直 PanedWindow:控件区(top,weight0)在上、结果区(bottom,weight1)在下,固定 sash。
        #   延后到构建完成再 pack(side=top),确保日志抽屉先占住底部。
        vpane = ttk.PanedWindow(right, orient="vertical")
        self._vpane = vpane
        # 控件区:可滚动画布(内容多时上下滚、不裁切;滚轮由 _wheel 统一处理)
        top_outer = ttk.Frame(vpane)
        self._top_canvas = tk.Canvas(top_outer, highlightthickness=0, borderwidth=0, background=theme.CANVAS)
        top_vsb = ttk.Scrollbar(top_outer, orient="vertical", command=self._top_canvas.yview)
        self._top_canvas.configure(yscrollcommand=top_vsb.set)
        top_vsb.pack(side="right", fill="y")
        self._top_canvas.pack(side="left", fill="both", expand=True)
        top = ttk.Frame(self._top_canvas)
        self._top_win = self._top_canvas.create_window((0, 0), window=top, anchor="nw")
        top.bind("<Configure>", lambda e: self._top_canvas.configure(scrollregion=self._top_canvas.bbox("all")))
        self._top_canvas.bind("<Configure>", lambda e: self._top_canvas.itemconfig(self._top_win, width=e.width))
        bottom = ttk.Frame(vpane)

        # 方法标题 + 次级(另一语言)
        self.lbl_method = ttk.Label(top, style="Method.TLabel", wraplength=720)
        self.lbl_method.pack(anchor="w")
        self.lbl_sub = ttk.Label(top, style="Muted.TLabel", wraplength=720)
        self.lbl_sub.pack(anchor="w", pady=(1, 2))
        self.lbl_desc = ttk.Label(top, style="Body.TLabel", wraplength=720, justify="left")   # 方法说明
        self.lbl_desc.pack(anchor="w", pady=(0, 8))

        # 数据段
        self.hdr_data = ttk.Label(top, style="Section.TLabel")
        self.hdr_data.pack(anchor="w", pady=(4, 2))
        ttk.Separator(top, orient="horizontal").pack(fill="x", pady=(0, 6))
        ds = ttk.Frame(top)
        ds.pack(fill="x")
        self.rb_ex = ttk.Radiobutton(ds, variable=self.data_source, value="example", command=self._on_source)
        self.rb_ex.grid(row=0, column=0, sticky="w", padx=(0, 16))
        self.rb_mine = ttk.Radiobutton(ds, variable=self.data_source, value="mine", command=self._on_source)
        self.rb_mine.grid(row=0, column=1, sticky="w")
        self.rb_paste = ttk.Radiobutton(ds, variable=self.data_source, value="paste", command=self._on_source)
        self.rb_paste.grid(row=0, column=2, sticky="w", padx=(0, 16))
        if _HAS_TKSHEET:
            self.rb_grid = ttk.Radiobutton(ds, variable=self.data_source, value="grid", command=self._on_source)
            self.rb_grid.grid(row=0, column=3, sticky="w", padx=(0, 16))
        self.btn_file = ttk.Button(ds, style="Toolbutton", command=self._choose_file)
        self.btn_file.grid(row=0, column=4, sticky="w", padx=16)
        self.lbl_file = ttk.Label(ds, style="Muted.TLabel")
        self.lbl_file.grid(row=1, column=0, columnspan=5, sticky="w", pady=(4, 0))
        self.lbl_cols = ttk.Label(ds, style="Muted.TLabel", wraplength=680, justify="left")
        self.lbl_cols.grid(row=2, column=0, columnspan=5, sticky="w", pady=(2, 0))
        self.lbl_mem = ttk.Label(ds, style="Muted.TLabel")
        self.lbl_mem.grid(row=3, column=0, columnspan=5, sticky="w", pady=(4, 0))

        # 粘贴/录入面板(选"粘贴数据"时显示)
        self.paste_frame = ttk.Frame(top)
        self.lbl_paste_hint = ttk.Label(self.paste_frame, style="Muted.TLabel", wraplength=680, justify="left")
        self.lbl_paste_hint.pack(anchor="w", pady=(4, 2))
        self.paste_text = tk.Text(self.paste_frame, height=5, wrap="none", font=(theme.MONO, 9),
                                  background=theme.CANVAS, foreground=theme.TEXT, relief="solid", borderwidth=1)
        self.paste_text.pack(fill="x")
        self.btn_paste_use = ttk.Button(self.paste_frame, style="Toolbutton", command=self._use_pasted)
        self.btn_paste_use.pack(anchor="w", pady=(4, 0))

        # 录入表格(选"录入表格"时显示;列 = 分析所需角色,可编辑/粘贴/右键加删行 → 免映射)
        if _HAS_TKSHEET:
            self.grid_frame = ttk.Frame(top)
            self.lbl_grid_hint = ttk.Label(self.grid_frame, style="Muted.TLabel", wraplength=680, justify="left")
            self.lbl_grid_hint.pack(anchor="w", pady=(4, 2))
            self.sheet = tksheet.Sheet(self.grid_frame, height=180)
            self.sheet.enable_bindings(("single_select", "drag_select", "row_select", "column_select",
                                        "edit_cell", "paste", "copy", "cut", "delete",
                                        "rc_insert_row", "rc_delete_row", "arrowkeys"))
            self.sheet.pack(fill="x")
            self.btn_grid_use = ttk.Button(self.grid_frame, style="Toolbutton", command=self._use_grid)
            self.btn_grid_use.pack(anchor="w", pady=(4, 0))
            self._grid_roles = []

        # 输入格式卡(选方法即出:所需列规格 + 示例前几行 + 下载模板/填示例)——只创建,由 _refresh_input_card 定位显隐
        self._build_input_card(top)

        # 列映射面板(上传/粘贴 + 该方法有列形状时显示)
        self.map_frame = ttk.Frame(top)
        self.map_frame.pack(fill="x", pady=(2, 0))

        # 参数段
        self.hdr_params = ttk.Label(top, style="Section.TLabel")
        self.hdr_params.pack(anchor="w", pady=(12, 2))
        ttk.Separator(top, orient="horizontal").pack(fill="x", pady=(0, 6))
        self.params_host = ttk.Frame(top)   # 缓存的表单挂这里
        self.params_host.pack(fill="x")

        # 运行行
        rowb = ttk.Frame(top)
        rowb.pack(fill="x", pady=(10, 4))
        self.btn_run = ttk.Button(rowb, style="Accent.TButton", command=self._run)
        self.btn_run.pack(side="left")
        self.btn_cancel = ttk.Button(rowb, style="Toolbutton", command=self._cancel)

        # 结果区直接作为下 pane 主体(不再与日志平权塞进 Notebook)→ 结果常驻为主
        self.results = ResultsView(bottom, on_open_folder=self._open_folder)
        self.results.pack(fill="both", expand=True)
        vpane.add(top_outer, weight=0)
        vpane.add(bottom, weight=1)
        vpane.pack(side="top", fill="both", expand=True)      # ★在日志抽屉 pack(bottom)之后
        self.root.after(80, lambda: self._init_sash())
        self.root.bind_all("<MouseWheel>", self._wheel)
        # 禁掉这些控件的类级默认滚轮:否则与统一 _wheel 双滚,且划过下拉框会误改选项
        for _cls in ("Treeview", "Text", "TCombobox"):
            try:
                self.root.unbind_class(_cls, "<MouseWheel>")
            except Exception:
                pass

    # ---------- 日志抽屉 ----------
    def _build_log_drawer(self, parent):
        self._log_open = False
        drawer = ttk.Frame(parent)
        drawer.pack(side="bottom", fill="x")          # ★先于 vpane.pack(side=top,expand)
        ttk.Separator(drawer, orient="horizontal").pack(side="top", fill="x")
        hdr = tk.Frame(drawer, bg=theme.SURFACE)
        hdr.pack(side="top", fill="x")
        self._dot = tk.Canvas(hdr, width=10, height=10, highlightthickness=0, bg=theme.SURFACE)
        self._dot.pack(side="left", padx=(8, 6), pady=4)
        self._dot_id = self._dot.create_oval(2, 2, 9, 9, fill=theme.MUTED, outline="")
        self.btn_log = ttk.Button(hdr, style="Toolbutton", command=self._toggle_log)
        self.btn_log.pack(side="left")
        self.lbl_logtail = tk.Label(hdr, bg=theme.SURFACE, fg=theme.MUTED, font=(theme.FONT, 9), anchor="w")
        self.lbl_logtail.pack(side="left", fill="x", expand=True, padx=8)
        self._log_body = ttk.Frame(drawer)            # 折叠体:默认不 pack
        self.log = tk.Text(self._log_body, height=8, wrap="word", font=(theme.MONO, 9),
                           background=theme.CANVAS, foreground=theme.TEXT, relief="flat", borderwidth=0)
        lsb = ttk.Scrollbar(self._log_body, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=lsb.set, state="disabled")
        self.log.pack(side="left", fill="both", expand=True)
        lsb.pack(side="right", fill="y")

    def _toggle_log(self, force=None):
        self._log_open = (not self._log_open) if force is None else bool(force)
        if self._log_open:
            self._log_body.pack(side="top", fill="both")
        else:
            self._log_body.pack_forget()
        self.btn_log.config(text=("▾ " if self._log_open else "▸ ") + I18N.t("log"))

    def _set_dot(self, color):
        try:
            self._dot.itemconfig(self._dot_id, fill=color)
        except Exception:
            pass

    # ---------- 搜索框占位提示 ----------
    def _search_focus_in(self, _evt=None):
        if self._search_ph:
            self.q_var.set("")
            self.ent_search.config(foreground=theme.TEXT)
            self._search_ph = False

    def _search_focus_out(self, _evt=None):
        if not self.q_var.get().strip():
            self._search_ph = True
            self.ent_search.config(foreground=theme.MUTED)
            self.q_var.set(I18N.t("search_hint"))

    def _search_key(self, _evt=None):
        if not self._search_ph:
            self._rebuild_tree(self.q_var.get().strip())

    def _reset_search_placeholder(self):
        """语言切换/初始:未聚焦且空时显示占位。"""
        if self._search_ph or not self.q_var.get().strip():
            self._search_ph = True
            self.ent_search.config(foreground=theme.MUTED)
            self.q_var.set(I18N.t("search_hint"))

    # ---------- 语言刷新 ----------
    def _on_lang(self):
        self._relabel_menu()
        self.btn_lang.config(text=I18N.t("lang_button"))
        self.rb_ex.config(text=I18N.both("use_example"))
        self.rb_mine.config(text=I18N.both("use_mine"))
        self.rb_paste.config(text=I18N.both("use_paste"))
        self.btn_file.config(text=I18N.t("choose_file"))
        self.btn_paste_use.config(text=I18N.t("paste_use"))
        self.lbl_paste_hint.config(text=I18N.t("paste_hint"))
        if _HAS_TKSHEET:
            self.rb_grid.config(text=I18N.both("use_grid"))
            self.btn_grid_use.config(text=I18N.t("grid_use"))
            self.lbl_grid_hint.config(text=I18N.t("grid_hint"))
        self.btn_cancel.config(text=I18N.t("cancel"))
        self.hdr_data.config(text=I18N.t("data"))
        self.hdr_params.config(text=I18N.t("parameters"))
        self._toggle_log(self._log_open)          # 重贴折叠钮文案(▸/▾ + 日志)
        self.results.retitle()
        self._apply_r_status()
        self._reset_search_placeholder()
        self._rebuild_tree('' if self._search_ph else self.q_var.get().strip())   # 保持当前搜索过滤
        if self.sel:
            self._render_header()
            self._refresh_input_card()
        else:
            self.lbl_method.config(text="Bio Wingman")
            self.lbl_sub.config(text=I18N.t("select_method"))
        self._update_run_button()

    def _apply_r_status(self):
        ok = bool(find_rscript())
        self.lbl_rstat.config(text=(I18N.t("r_ok") if ok else I18N.t("r_missing")),
                              foreground=theme.OK if ok else theme.SIG)

    # ---------- 方法树 ----------
    def _rebuild_tree(self, query=""):
        q = (query or "").lower()
        self.tree.delete(*self.tree.get_children())
        self._node_to_mid = {}
        lang = I18N.lang
        for key, zh, en, items in engine.grouped_methods():
            hits = [m for m in items if (not q)
                    or q in I18N.title_of(m).lower()
                    or q in (str(m.get("title", "")) + str(m.get("title_en", ""))).lower()]
            if not hits:
                continue
            parent = self.tree.insert("", "end", text=(zh if lang == "zh" else en), open=True, tags=("group",))
            for m in hits:
                node = self.tree.insert(parent, "end", text=I18N.title_of(m))
                self._node_to_mid[node] = m["id"]
        if self.sel:
            for node, mid in self._node_to_mid.items():
                if mid == self.sel["id"]:
                    self.tree.selection_set(node)
                    break

    def _on_select(self, _evt):
        node = (self.tree.selection() or [None])[0]
        mid = getattr(self, "_node_to_mid", {}).get(node)
        if mid and (not self.sel or mid != self.sel["id"]):
            self.pick(mid)

    # ---------- 选方法 ----------
    def pick(self, mid):
        if self.run and not self.run.done:   # 切方法前取消在跑的旧 run,避免重叠/结果串到别的方法
            self.run.cancel()
            self.run = None
            self._reset_run_ui()             # ★复位运行态 UI(否则进度条空转/取消键死/状态卡"运行中")
        self.sel = engine.load_manifest(mid)
        self.data_source.set("example")
        self.user_file = None
        self.paste_frame.pack_forget()
        self._render_header()
        self._refresh_input_card()
        self._swap_form(mid)
        self._set_log("")
        self.results.clear()
        self._refresh_file_label()
        self._rebuild_map()
        self._schedule_redlight()
        self._update_run_button()

    def _reset_run_ui(self):
        """复位运行态 UI(切方法取消旧 run、或 run 结束时统一收尾用)。"""
        try:
            self.btn_cancel.pack_forget()
        except Exception:
            pass
        try:
            self.pbar.stop()
            self.pbar.pack_forget()
        except Exception:
            pass
        self._set_dot(theme.MUTED)
        self._set_status("")

    def _render_header(self):
        m = self.sel
        self.lbl_method.config(text=I18N.title_of(m))
        other = m.get("title") if I18N.lang == "en" else m.get("title_en")
        self.lbl_sub.config(text=other or "")
        self.lbl_desc.config(text=m.get("description", ""))   # 方法说明(做什么/出什么图)——上手引导
        pin = engine.primary_input(m)
        spec = (pin or {}).get("spec", "")
        self.lbl_cols.config(text=(I18N.t("columns_needed") + ": " + spec) if spec else "")
        is_dir = bool(pin and pin.get("format") == "dir")   # 目录输入方法:按钮改「选择文件夹」
        self.btn_file.config(text=I18N.t("choose_dir") if is_dir else I18N.t("choose_file"))

    # ---------- 输入格式卡(选方法即出:所需列 + 示例前几行 + 下载模板/填示例)----------
    def _build_input_card(self, parent):
        self.card = ttk.Labelframe(parent, style="Card.TLabelframe")
        self.card.columnconfigure(0, weight=1)
        btns = ttk.Frame(self.card)
        btns.grid(row=0, column=0, sticky="w", padx=8, pady=(6, 2))
        self.btn_tmpl = ttk.Button(btns, style="Toolbutton", command=self._download_template)
        self.btn_tmpl.pack(side="left")
        self.btn_fill = ttk.Button(btns, style="Toolbutton", command=self._fill_example_grid)
        self.tv_schema = ttk.Treeview(self.card, show="headings", height=4, columns=("c", "d", "t", "r"))
        for c, w in (("c", 130), ("d", 230), ("t", 66), ("r", 60)):
            self.tv_schema.column(c, width=w, stretch=False, anchor="w")
        self.tv_schema.grid(row=1, column=0, sticky="ew", padx=8, pady=(2, 4))
        self.lbl_prev = ttk.Label(self.card, style="Muted.TLabel")
        self.lbl_prev.grid(row=2, column=0, sticky="w", padx=8)
        self.tv_prev = ttk.Treeview(self.card, show="headings", height=3)
        self.tv_prev.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))

    def _read_rows(self, path, n):
        if not path or not os.path.exists(path):
            return [], []
        for enc in ("utf-8-sig", "gb18030", "latin-1"):
            try:
                with open(path, encoding=enc, newline="") as f:
                    rows = [[c.strip() for c in r] for i, r in enumerate(csv.reader(f)) if i <= n]
                return (rows[0] if rows else []), rows[1:n + 1]
            except UnicodeDecodeError:
                continue
            except Exception:
                return [], []
        return [], []

    def _refresh_input_card(self):
        if not self.sel:
            self.card.pack_forget()
            return
        shape = engine.shape_of(self.sel)
        ex = engine.example_path(self.sel)
        pin = engine.primary_input(self.sel)
        is_text = (pin or {}).get("format") in (None, "csv", "tsv", "txt")   # 二进制(h5ad/rds/maf)/目录不预览
        if _HAS_TKSHEET:                          # 录入表格只对有列角色的方法有意义,否则隐藏(避免单列死表)
            (self.rb_grid.grid() if (shape and shape.get("columns")) else self.rb_grid.grid_remove())
        self.card.config(text=I18N.both("input_format"))
        # 列规格表(有形状才显示)
        if shape and shape.get("columns"):
            for cid, key in (("c", "hdr_column"), ("d", "hdr_meaning"), ("t", "hdr_type"), ("r", "hdr_required")):
                self.tv_schema.heading(cid, text=I18N.t(key))
            self.tv_schema.delete(*self.tv_schema.get_children())
            for col in shape["columns"]:
                self.tv_schema.insert("", "end", values=(
                    col.get("role"), f'{col.get("zh","")} · {col.get("en","")}',
                    col.get("type", "-"),
                    I18N.t("required") if col.get("required") else I18N.t("optional")))
            self.tv_schema.configure(height=min(max(len(shape["columns"]), 2), 6))
            self.tv_schema.grid()
        else:
            self.tv_schema.grid_remove()
        # 示例前 3 行(仅文本格式;二进制/目录不预览,避免 latin-1 硬解出乱码)——"你的文件应长这样"
        hdr, rows = (self._read_rows(ex, 3) if is_text else ([], []))
        if hdr:
            self.lbl_prev.config(text=I18N.t("example_preview"))
            self.tv_prev["columns"] = list(range(len(hdr)))
            self.tv_prev.delete(*self.tv_prev.get_children())
            for i, h in enumerate(hdr):
                self.tv_prev.heading(i, text=h)
                self.tv_prev.column(i, width=90, stretch=False, anchor="w")
            for r in rows:
                self.tv_prev.insert("", "end", values=r[:len(hdr)])
            self.lbl_prev.grid()
            self.tv_prev.grid()
        else:
            self.tv_prev.delete(*self.tv_prev.get_children())   # 清旧行,避免切到二进制方法时残留上个方法的预览
            self.lbl_prev.grid_remove()
            self.tv_prev.grid_remove()
        self.btn_tmpl.config(text=I18N.t("download_template"), state=("normal" if ex else "disabled"))
        self.btn_fill.config(text=I18N.t("fill_example"))
        if _HAS_TKSHEET and shape and shape.get("columns"):   # 填示例只对有列角色的方法有意义
            self.btn_fill.pack(side="left", padx=(8, 0))
        else:
            self.btn_fill.pack_forget()
        if (shape and shape.get("columns")) or hdr or ex:   # 二进制方法也显卡片(只留"下载示例"按钮)
            self.card.pack(fill="x", pady=(6, 4), before=self.map_frame)
        else:
            self.card.pack_forget()

    def _download_template(self):
        ex = engine.example_path(self.sel) if self.sel else None
        if not ex or not os.path.exists(ex):
            return
        base = os.path.basename(ex)                       # 保留真实文件名/扩展(.maf.gz/.h5ad/.rds/.csv)
        ext = os.path.splitext(base)[1] or ".csv"         # 二进制示例不会被存成损坏的 .csv
        dst = filedialog.asksaveasfilename(
            defaultextension=ext, initialfile=self.sel["id"] + "_example" + ext,
            filetypes=[("All files", "*.*")])
        if dst:
            try:
                shutil.copyfile(ex, dst)
            except Exception:
                pass

    def _fill_example_grid(self):
        """把示例前几行灌进录入表格并切到表格数据源,用户直接改成自己的数据。"""
        if not _HAS_TKSHEET or not self.sel:
            return
        _hdr, rows = self._read_rows(engine.example_path(self.sel), 8)
        if not rows:
            return
        self.data_source.set("grid")
        self._on_source()                        # 显示 grid_frame + 按角色建表头
        try:
            ncol = len(self._grid_roles)
            data = [(r[:ncol] + [""] * (ncol - len(r))) for r in rows]
            self.sheet.set_sheet_data(data, reset_col_positions=True)
            self.sheet.set_all_column_widths()
        except Exception:
            pass
        self._append_log("✓ " + I18N.t("grid_used"))

    def _swap_form(self, mid):
        if self._cur_form is not None:      # 只忘当前那个,不遍历全部 61 个
            self._cur_form.pack_forget()
        if mid not in self._forms:
            self._forms[mid] = ParamForm(self.params_host, self.sel.get("params_schema"))
        self._forms[mid].pack(fill="x")
        self._cur_form = self._forms[mid]

    @property
    def form(self):
        return self._forms.get(self.sel["id"]) if self.sel else None

    def _on_source(self):
        src = self.data_source.get()
        self.paste_frame.pack(fill="x", pady=(2, 0), before=self.map_frame) if src == "paste" else self.paste_frame.pack_forget()
        if _HAS_TKSHEET:
            if src == "grid":
                self.grid_frame.pack(fill="x", pady=(2, 0), before=self.map_frame)
                self._populate_grid()
            else:
                self.grid_frame.pack_forget()
        if src == "mine" and not self.user_file:
            self._choose_file()
            return
        self._refresh_file_label()
        self._rebuild_map()
        self._schedule_redlight()
        self._update_run_button()

    def _populate_grid(self):
        shape = engine.shape_of(self.sel) if self.sel else None
        headers, self._grid_roles = [], []
        if not any(c["role"] in ("study", "slab", "studlab") for c in (shape["columns"] if shape else [])):
            headers.append("Study"); self._grid_roles.append("studlab")
        for c in (shape["columns"] if shape else []):
            req = "" if c.get("required") else " (选填)"
            headers.append("%s·%s%s" % (c.get("zh", c["role"]), c.get("en", c["role"]), req))
            self._grid_roles.append(c["role"])
        if not headers:                       # 纯参数方法:无形状,不用表格
            headers, self._grid_roles = ["study"], ["studlab"]
        self.sheet.headers(headers)
        self.sheet.set_sheet_data([["" for _ in headers] for _ in range(8)], reset_col_positions=True)
        try:
            self.sheet.set_all_column_widths()
        except Exception:
            pass

    def _use_grid(self):
        try:
            data = self.sheet.get_sheet_data()
        except Exception:
            return
        rows = [r for r in data if any(str(x).strip() for x in r)]
        if not rows:
            self._append_log("! " + I18N.t("grid_empty"))
            return
        from .paths import run_root
        d = run_root() / "_grid"
        d.mkdir(parents=True, exist_ok=True)
        p = d / "grid.csv"
        import csv as _csv
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = _csv.writer(f)
            w.writerow(self._grid_roles)
            for r in rows:
                w.writerow([str(x).strip() for x in r][:len(self._grid_roles)])
        self.user_file = str(p)
        self._refresh_file_label()
        self._schedule_redlight()
        self._update_run_button()
        self._append_log("✓ " + I18N.t("grid_used"))

    def _use_pasted(self):
        raw = self.paste_text.get("1.0", "end").strip()
        if not raw:
            self._append_log("! " + I18N.t("paste_empty"))
            return
        rows = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            cells = line.split("\t") if "\t" in line else line.split(",")
            rows.append([c.strip() for c in cells])
        if not rows:
            return
        # 首行:全非数字 → 当表头;否则按形状角色名或 c1,c2… 生成表头
        def is_num(x):
            try:
                float(x); return True
            except ValueError:
                return False
        all_numeric = bool(rows[0]) and all(is_num(c) for c in rows[0])   # 全数值才判"无表头";含"gene"等非数字则首行是表头
        shape = engine.shape_of(self.sel) if self.sel else None
        if all_numeric:
            n = len(rows[0])
            if shape and len(shape["columns"]) >= n:
                header = [shape["columns"][i]["role"] for i in range(n)]
            else:
                header = [f"c{i+1}" for i in range(n)]
            data = rows
        else:
            header = rows[0]
            data = rows[1:]
        from .paths import run_root
        dest = run_root() / "_pasted"
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / "pasted.csv"
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(header)
            for r in data:
                wr.writerow(r)
        self.user_file = str(path)
        self._refresh_file_label()
        self._rebuild_map()
        self._schedule_redlight()
        self._update_run_button()

    def _choose_file(self):
        pin = engine.primary_input(self.sel) if self.sel else None
        if pin and pin.get("format") == "dir":          # 目录输入方法:选文件夹而非单文件
            path = filedialog.askdirectory(title=I18N.t("choose_dir"))
        else:
            path = filedialog.askopenfilename(
                title="CSV", filetypes=[("CSV", "*.csv"), ("Text", "*.txt *.tsv"), ("All", "*.*")])
        if path:
            self.user_file = os.path.normpath(path)
            self.data_source.set("mine")
        else:
            if not self.user_file:
                self.data_source.set("example")
        self._refresh_file_label()
        self._rebuild_map()
        self._schedule_redlight()
        self._update_run_button()

    def _refresh_file_label(self):
        if self.data_source.get() in ("mine", "paste", "grid") and self.user_file:
            ds = self.data_source.get()
            name = {"paste": "pasted data", "grid": "table data"}.get(ds, os.path.basename(self.user_file))
            self.lbl_file.config(text=I18N.t("loaded") + ": " + name)
        else:
            self.lbl_file.config(text="")

    def _cur_data_path(self):
        if self.data_source.get() in ("mine", "paste", "grid"):
            return self.user_file
        return engine.example_path(self.sel) if self.sel else None

    # ---------- 列映射 ----------
    def _read_headers(self, path):
        for enc in ("utf-8-sig", "gb18030", "latin-1"):
            try:
                with open(path, "r", encoding=enc, newline="") as f:
                    row = next(csv.reader(f), [])
                return [c.strip() for c in row if c.strip()]
            except UnicodeDecodeError:
                continue
            except Exception:
                return []
        return []

    @staticmethod
    def _guess(aliases, headers):
        low = {h.lower().strip(): h for h in headers}
        for a in aliases:                         # 精确别名(不分大小写)
            if a.lower() in low:
                return low[a.lower()]
        for a in aliases:                         # 子串包含
            for h in headers:
                if a.lower() in h.lower():
                    return h
        return ""

    def _rebuild_map(self):
        for w in self.map_frame.winfo_children():
            w.destroy()
        self._map_vars = {}
        self._map_labels = {}
        shape = engine.shape_of(self.sel) if self.sel else None
        if not shape or self.data_source.get() not in ("mine", "paste") or not self.user_file:
            return
        self._headers = self._read_headers(self.user_file)
        if not self._headers:
            return
        ttk.Label(self.map_frame, text=I18N.both("map_columns"), style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 3))
        opts = ["(无)"] + self._headers
        cols = shape["columns"]
        for i, col in enumerate(cols, start=1):
            req = "" if col.get("required") else " " + I18N.t("optional")
            lbl = ttk.Label(self.map_frame, text=f'{col.get("zh")} · {col.get("en")}{req}', style="Muted.TLabel")
            lbl.grid(row=i, column=0, sticky="w", padx=(0, 10), pady=1)
            self._map_labels[col["role"]] = lbl
            var = tk.StringVar(value=self._guess(col.get("aliases", [col["role"]]), self._headers) or "(无)")
            cb = ttk.Combobox(self.map_frame, textvariable=var, values=opts, state="readonly", width=22)
            cb.grid(row=i, column=1, sticky="w", pady=1)
            cb.bind("<<ComboboxSelected>>", lambda e: self._map_feedback())
            self._map_vars[col["role"]] = (var, col)
        # 汇总反馈行:必填列是否已全部对应(即时,不必等运行)
        self.lbl_mapfb = ttk.Label(self.map_frame, style="Muted.TLabel")
        self.lbl_mapfb.grid(row=len(cols) + 1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self._map_feedback()

    def _map_feedback(self):
        miss = self._missing_required()
        for role, (var, col) in self._map_vars.items():   # 必填未映射的列标红
            lbl = self._map_labels.get(role)
            if lbl is None:
                continue
            empty = (not var.get() or var.get() == "(无)")
            lbl.configure(foreground=(theme.SIG if (col.get("required") and empty) else theme.MUTED))
        if not hasattr(self, "lbl_mapfb") or not self.lbl_mapfb.winfo_exists():
            return
        if miss:
            self.lbl_mapfb.configure(foreground=theme.SIG,
                                     text="! " + I18N.t("map_missing_n", n=len(miss)) + ": " + "、".join(miss))
        else:
            self.lbl_mapfb.configure(foreground=theme.OK, text="✓ " + I18N.t("map_ok"))

    def _collect_map(self):
        cm = {}
        for role, (var, col) in self._map_vars.items():
            v = var.get()
            if v and v != "(无)":
                cm[role] = v
        return cm

    def _missing_required(self):
        miss = []
        for role, (var, col) in self._map_vars.items():
            if col.get("required") and (not var.get() or var.get() == "(无)"):
                miss.append(col.get("zh") or role)
        return miss

    # ---------- 红绿灯(防抖 + 后台线程) ----------
    def _schedule_redlight(self):
        if self._rl_job:
            self.root.after_cancel(self._rl_job)
        self.lbl_mem.config(text="")
        self._rl_job = self.root.after(150, self._run_redlight)

    def _run_redlight(self):
        self._rl_job = None
        m, path = self.sel, self._cur_data_path()
        if not m:
            return
        tok = self._rl_tok = self._rl_tok + 1
        # worker 只塞队列(Tkinter 非线程安全,worker 不碰 Tk);主线程 after 轮询回填
        threading.Thread(target=lambda: self._rl_q.put((tok, mem_estimate(m, path))), daemon=True).start()
        self.root.after(50, lambda: self._poll_redlight(tok))

    def _poll_redlight(self, tok):
        if tok != self._rl_tok:
            return                       # 已有更新请求,弃本轮
        match = None
        try:
            while True:                  # 扫描队列找令牌匹配项(线程入队顺序不定,不能只留最后一个)
                item = self._rl_q.get_nowait()
                if item[0] == self._rl_tok:
                    match = item
        except queue.Empty:
            pass
        if match is not None:
            self._apply_redlight(match[1])
        else:
            self.root.after(50, lambda: self._poll_redlight(tok))

    def _apply_redlight(self, r):
        if not r:
            self.lbl_mem.config(text="")
            return
        dims = f'{r.get("n_rows") or "?"}×{r.get("n_cols") or "?"}'   # 目录/无元数据格式 → 值为 None,回退 "?"
        note = "(维度未知,仅按文件大小粗估)" if r.get("dim_unknown") else ""
        self.lbl_mem.config(
            text=f'{I18N.t("memory")}: {dims} · ' + I18N.t("peak_mem", gb=r["peak_gb"], avail=r["avail_gb"]) + note,
            foreground=theme.LIGHT.get(r["level"], theme.OK))
        try:
            self.lbl_ctx.config(text=dims)      # 状态栏右侧显示数据维度
        except Exception:
            pass

    def _update_run_button(self):
        if not self.sel:
            return
        user = self.data_source.get() in ("mine", "paste", "grid")
        if user and not self.user_file:
            self.btn_run.config(text=I18N.t("pick_first"), state="disabled")
        else:
            self.btn_run.config(text=I18N.t("run_mine") if user else I18N.t("run_example"), state="normal")

    # ---------- 运行 ----------
    def _run(self):
        if not self.sel:
            return
        if not find_rscript():
            self._locate_r()
            return
        params = self.form.values() if self.form else {}
        input_path = None
        col_map = {}
        ds = self.data_source.get()
        if ds in ("mine", "paste", "grid"):
            input_path = self.user_file
            if ds != "grid" and self._map_vars:      # 上传/粘贴:校验必填列已对应(表格列即角色,免映射)
                miss = self._missing_required()
                if miss:
                    self._append_log("! " + I18N.t("map_missing") + ": " + "、".join(miss))
                    self._toggle_log(True)
                    return
                col_map = self._collect_map()
        if not self._data_ok(col_map):               # 数值级校验:有问题弹窗,用户可选仍继续
            return
        timeout = int(self.sel.get("timeout_hint", 1800))   # 重方法在 manifest 声明更大超时,避免真实大数据被强杀
        r = engine.Run(self.sel, input_path=input_path, params=params, col_map=col_map, timeout=timeout)
        self.run = r
        self._set_log("")
        self.results.clear()
        self._set_dot(theme.WARN)
        self._set_status(I18N.t("running"))
        self.pbar.pack(side="left", padx=8)
        self.pbar.start(12)
        self.btn_run.config(state="disabled")
        self.btn_cancel.pack(side="left", padx=8)
        r.start()
        self.root.after(120, lambda: self._poll(r))

    def _data_ok(self, col_map):
        """运行前数值级校验:有问题则弹窗列出,用户可选「仍继续」(覆盖)或返回修数据。"""
        try:
            shape = engine.shape_of(self.sel)
            dpath = self._cur_data_path()
            if not (shape and dpath):
                return True
            issues = mw_validate.validate(shape, dpath, col_map or None)
        except Exception:
            return True
        if not issues:
            return True
        from tkinter import messagebox
        for m in issues:
            self._append_log("! " + m)
        go = messagebox.askyesno(
            "Bio Wingman",
            I18N.t("validate_head") + "\n\n" + "\n".join(issues[:12]) + "\n\n" + I18N.t("validate_ask"))
        if not go:
            self._toggle_log(True)
        return go

    def _poll(self, run):
        if run is not self.run:          # 已切方法/重跑 → 这是旧 run 的轮询,停(避免串结果、避免僵尸定时器)
            return
        for kind, payload in run.poll():
            if kind == "log":
                self._append_log(payload)
            elif kind == "error":
                self._append_log("! " + str(payload))
            elif kind == "done":
                self._on_done(payload)
                return
        self.root.after(120, lambda: self._poll(run))

    def _on_done(self, rc):
        r = self.run
        self._reset_run_ui()          # 停进度条/收取消键/清状态点(随后按 rc 覆盖 dot/status)
        self._update_run_button()
        imgs = [o for o in r.outputs if o.lower().endswith(".png")]
        tbls = [o for o in r.outputs if o.lower().endswith(".csv")]
        if rc == 0:
            self.results.show(r.outputs, r.outdir, r.m, r.params)   # 结果为主区,直接呈现
            self._set_dot(theme.OK)
            self._set_status(I18N.t("done_ok", rc=rc, nimg=len(imgs), ntbl=len(tbls)))
            self._append_log("\n" + I18N.t("done_ok", rc=rc, nimg=len(imgs), ntbl=len(tbls)))
        else:
            self._set_dot(theme.SIG)
            self._set_status(I18N.t("done_fail", rc=rc))
            self._append_log("\n" + I18N.t("done_fail", rc=rc))
            self._toggle_log(True)                 # 失败自动展开日志,保证报错可见

    def _cancel(self):
        if self.run:
            self.run.cancel()

    def _open_folder(self):
        d = self.run.outdir if self.run else None
        if d and d.exists():
            try:
                os.startfile(str(d))
            except Exception:
                pass

    # ---------- R 定位 ----------
    def _locate_r(self):
        from tkinter import messagebox
        if messagebox.askokcancel(I18N.t("no_r_title"), I18N.t("no_r_body")):
            path = filedialog.askopenfilename(title="Rscript.exe", filetypes=[("Rscript", "Rscript.exe"), ("All", "*.*")])
            if path:
                set_rscript(os.path.normpath(path))
                self._apply_r_status()

    # ---------- 工具 ----------
    def _set_log(self, text):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("end", text)
        self.log.config(state="disabled")

    def _append_log(self, line):
        self.log.config(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.config(state="disabled")
        try:                                   # 抽屉收起时也能看到最新一行摘要
            if line.strip():
                self.lbl_logtail.config(text=line.strip()[:80])
        except Exception:
            pass
