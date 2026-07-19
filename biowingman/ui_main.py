# -*- coding: utf-8 -*-
"""主窗口:左=分组方法树,右=方法详情。RevMan 式紧凑、克制,无营销文案。
性能:红绿灯去主线程(缓存+防抖+后台线程);参数表单按方法缓存不重建。"""
from __future__ import annotations
import csv
import os
import queue
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
        if self.data_source.get() in ("mine", "paste", "grid") and self.user_file and os.path.exists(self.user_file):
            st["data_name"] = os.path.basename(self.user_file)
            for enc in ("utf-8-sig", "gb18030", "latin-1"):
                try:
                    st["data_csv"] = open(self.user_file, encoding=enc).read()
                    break
                except Exception:
                    continue
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
            self._vpane.sashpos(0, 372)   # 固定分隔:控件区在上、结果区在下
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

    # ---------- 主体 ----------
    def _build_body(self):
        body = ttk.Frame(self.root)
        body.pack(side="top", fill="both", expand=True)

        left = ttk.Frame(body, padding=(6, 6))
        left.pack(side="left", fill="y")
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse")
        self.tree.column("#0", width=230, minwidth=190)
        self.tree.tag_configure("group", font=(theme.FONT, 9, "bold"))
        self.tree.pack(side="left", fill="y", expand=True)
        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        ttk.Separator(body, orient="vertical").pack(side="left", fill="y")

        right = ttk.Frame(body, padding=(14, 10))
        right.pack(side="left", fill="both", expand=True)
        # ★垂直 PanedWindow:控件区(top)与结果区(bottom)用固定 sash 隔开,
        #   改方法标题/参数不再牵动下方 Notebook 重排(实测省掉每次 ~60ms 卡顿)。
        vpane = ttk.PanedWindow(right, orient="vertical")
        vpane.pack(fill="both", expand=True)
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
        self.lbl_sub.pack(anchor="w", pady=(1, 8))

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

        # 日志 / 结果
        self.nb = ttk.Notebook(bottom)
        self.nb.pack(fill="both", expand=True)
        vpane.add(top_outer, weight=0)
        vpane.add(bottom, weight=1)
        self.root.after(80, lambda: self._init_sash())
        self.root.bind_all("<MouseWheel>", self._wheel)
        # 禁掉这些控件的类级默认滚轮:否则与统一 _wheel 双滚,且划过下拉框会误改选项
        for _cls in ("Treeview", "Text", "TCombobox"):
            try:
                self.root.unbind_class(_cls, "<MouseWheel>")
            except Exception:
                pass
        logf = ttk.Frame(self.nb)
        self.log = tk.Text(logf, height=7, wrap="word", font=(theme.MONO, 9),
                           background=theme.CANVAS, foreground=theme.TEXT,
                           relief="flat", borderwidth=0)
        lsb = ttk.Scrollbar(logf, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=lsb.set, state="disabled")
        self.log.pack(side="left", fill="both", expand=True)
        lsb.pack(side="right", fill="y")
        self.results = ResultsView(self.nb, on_open_folder=self._open_folder)
        self.nb.add(logf, text="Log")
        self.nb.add(self.results, text="Results")

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
        self.nb.tab(0, text=I18N.t("log"))
        self.nb.tab(1, text=I18N.t("results"))
        self.results.retitle()
        self._apply_r_status()
        self._rebuild_tree()
        if self.sel:
            self._render_header()
        else:
            self.lbl_method.config(text="Bio Wingman")
            self.lbl_sub.config(text=I18N.t("select_method"))
        self._update_run_button()

    def _apply_r_status(self):
        ok = bool(find_rscript())
        self.lbl_rstat.config(text=(I18N.t("r_ok") if ok else I18N.t("r_missing")),
                              foreground=theme.OK if ok else theme.SIG)

    # ---------- 方法树 ----------
    def _rebuild_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._node_to_mid = {}
        lang = I18N.lang
        for key, zh, en, items in engine.grouped_methods():
            parent = self.tree.insert("", "end", text=(zh if lang == "zh" else en), open=True, tags=("group",))
            for m in items:
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
        self.sel = engine.load_manifest(mid)
        self.data_source.set("example")
        self.user_file = None
        self.paste_frame.pack_forget()
        self._render_header()
        self._swap_form(mid)
        self._set_log("")
        self.results.clear()
        self._refresh_file_label()
        self._rebuild_map()
        self._schedule_redlight()
        self._update_run_button()

    def _render_header(self):
        m = self.sel
        self.lbl_method.config(text=I18N.title_of(m))
        other = m.get("title") if I18N.lang == "en" else m.get("title_en")
        self.lbl_sub.config(text=other or "")
        pin = engine.primary_input(m)
        spec = (pin or {}).get("spec", "")
        self.lbl_cols.config(text=(I18N.t("columns_needed") + ": " + spec) if spec else "")

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
        first_numeric = any(is_num(c) for c in rows[0])
        shape = engine.shape_of(self.sel) if self.sel else None
        if first_numeric:
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
        shape = engine.shape_of(self.sel) if self.sel else None
        if not shape or self.data_source.get() not in ("mine", "paste") or not self.user_file:
            return
        self._headers = self._read_headers(self.user_file)
        if not self._headers:
            return
        ttk.Label(self.map_frame, text=I18N.both("map_columns"), style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 3))
        opts = ["(无)"] + self._headers
        for i, col in enumerate(shape["columns"], start=1):
            req = "" if col.get("required") else " " + I18N.t("optional")
            ttk.Label(self.map_frame, text=f'{col.get("zh")} · {col.get("en")}{req}',
                      style="Muted.TLabel").grid(row=i, column=0, sticky="w", padx=(0, 10), pady=1)
            var = tk.StringVar(value=self._guess(col.get("aliases", [col["role"]]), self._headers) or "(无)")
            ttk.Combobox(self.map_frame, textvariable=var, values=opts, state="readonly", width=22).grid(
                row=i, column=1, sticky="w", pady=1)
            self._map_vars[col["role"]] = (var, col)

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
        dims = f'{r.get("n_rows", "?")}×{r.get("n_cols", "?")}'
        self.lbl_mem.config(
            text=f'{I18N.t("memory")}: {dims} · ' + I18N.t("peak_mem", gb=r["peak_gb"], avail=r["avail_gb"]),
            foreground=theme.LIGHT.get(r["level"], theme.OK))

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
                    self.nb.select(0)
                    return
                col_map = self._collect_map()
        if not self._data_ok(col_map):               # 数值级校验:有问题弹窗,用户可选仍继续
            return
        r = engine.Run(self.sel, input_path=input_path, params=params, col_map=col_map)
        self.run = r
        self._set_log("")
        self.results.clear()
        self.nb.select(0)
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
            self.nb.select(0)
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
        self.btn_cancel.pack_forget()
        self._update_run_button()
        imgs = [o for o in r.outputs if o.lower().endswith(".png")]
        tbls = [o for o in r.outputs if o.lower().endswith(".csv")]
        if rc == 0:
            self.results.show(r.outputs, r.outdir, r.m, r.params)
            self.nb.select(1)
            self._append_log("\n" + I18N.t("done_ok", rc=rc, nimg=len(imgs), ntbl=len(tbls)))
        else:
            self._append_log("\n" + I18N.t("done_fail", rc=rc))

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
