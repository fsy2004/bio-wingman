# -*- coding: utf-8 -*-
"""极简中英双语:dict 字符串表 + 运行时切换(免重启)+ 持久化。不用 gettext。
key 用稳定标识符;缺译回落 EN 再回落 key。both() 给中英并列(用于关键选择)。"""
from __future__ import annotations
import json

from .paths import config_dir

STRINGS = {
    "en": {
        "app_title": "Bio Wingman",
        "lang_button": "中文",
        "save_as": "Save as…",
        "copy_table": "Copy table",
        "copy_image": "Copy figure",
        "results_empty": "Results (figures & tables) appear here after you run an analysis.",
        "save_table": "Save table (CSV)",
        "export_all": "Export all outputs",
        "export_all_done": "Exported {n} file(s) to:\n{d}",
        "reset_defaults": "Reset defaults",
        "rows_shown": "showing first {n} of {total} rows",
        "search_hint": "Search methods…",
        "input_format": "Input format",
        "hdr_column": "Column", "hdr_meaning": "Meaning", "hdr_type": "Type", "hdr_required": "Required",
        "required": "required",
        "example_preview": "Example (first rows) — your file should look like this:",
        "fill_example": "Fill table with example",
        "map_ok": "all required columns mapped",
        "map_missing_n": "still need {n} column(s)",
        "export_png": "PNG",
        "export_pdf": "PDF (vector)",
        "validate_head": "Possible data issues found:",
        "validate_ask": "Run anyway?",
        "menu_file": "File", "menu_exit": "Exit",
        "proj_open": "Open project…", "proj_save": "Save project…",
        "proj_none": "Select a method first", "proj_saved": "Project saved:\n{d}",
        "export_script": "Export R script",
        "export_report": "Export report (Word)",
        "report_done": "Report saved:\n{d}",
        "report_fail": "Report export failed (python-docx installed?)",
        "repro_done": "Saved reproduce.R + data.csv to:\n{d}",
        "repro_none": "Run an analysis first",
        "saved": "Saved",
        "outputs": "Outputs",
        "map_columns": "Map your columns",
        "optional": "(optional)",
        "map_missing": "Please map the required columns",
        "use_paste": "Paste / type data",
        "use_grid": "Data table",
        "grid_hint": "Type or paste into the columns this analysis needs (right-click to add/remove rows). No column mapping needed.",
        "grid_use": "Use this table",
        "grid_empty": "Enter some data first",
        "grid_used": "Using table data",
        "paste_use": "Use this data",
        "paste_hint": "Paste rows from Excel (tab- or comma-separated). The first row may be your column names.",
        "paste_empty": "Paste some data first",
        "r_ok": "R ready",
        "r_missing": "R not found",
        "r_locate": "Locate Rscript.exe…",
        "select_method": "Select a method on the left.",
        "data": "Data",
        "use_example": "Built-in example",
        "use_mine": "My CSV file",
        "choose_file": "Choose CSV…",
        "choose_dir": "Choose folder…",
        "loaded": "Loaded",
        "columns_needed": "Columns needed",
        "download_template": "Download the example as a template",
        "parameters": "Parameters",
        "run_example": "Run (example data)",
        "run_mine": "Run (my data)",
        "running": "Running…",
        "cancel": "Cancel",
        "pick_first": "Choose a CSV first",
        "log": "Log",
        "results": "Results",
        "figures": "Figures",
        "tables": "Tables",
        "memory": "Memory",
        "open_folder": "Open output folder",
        "done_ok": "Done — return code {rc} · {nimg} figures / {ntbl} tables",
        "done_fail": "Failed (return code {rc}). See the log above.",
        "no_r_title": "R not found",
        "no_r_body": "Bio Wingman needs R (Rscript). Install R 4.x, or click 'Locate Rscript.exe' to point to it.",
        "no_tk_body": "This Python has no tkinter. Reinstall Python from python.org (with Tcl/Tk).",
        "peak_mem": "est. peak {gb} GB / {avail} GB free",
    },
    "zh": {
        "app_title": "Bio Wingman",
        "lang_button": "EN",
        "save_as": "另存为…",
        "copy_table": "复制表格",
        "copy_image": "复制图",
        "results_empty": "运行分析后,图表与结果表会显示在这里。",
        "save_table": "另存表格(CSV)",
        "export_all": "导出全部产物",
        "export_all_done": "已导出 {n} 个文件到:\n{d}",
        "reset_defaults": "恢复默认",
        "rows_shown": "显示前 {n} 行 / 共 {total} 行",
        "search_hint": "搜索方法…",
        "input_format": "输入格式",
        "hdr_column": "列名", "hdr_meaning": "含义", "hdr_type": "类型", "hdr_required": "必填",
        "required": "必填",
        "example_preview": "示例(前几行)—— 你的文件应长这样:",
        "fill_example": "用示例填表格",
        "map_ok": "必填列已全部对应",
        "map_missing_n": "还差 {n} 列",
        "export_png": "PNG",
        "export_pdf": "PDF(矢量)",
        "validate_head": "数据可能有问题:",
        "validate_ask": "仍要运行吗?",
        "menu_file": "文件", "menu_exit": "退出",
        "proj_open": "打开项目…", "proj_save": "保存项目…",
        "proj_none": "请先选一个方法", "proj_saved": "项目已保存:\n{d}",
        "export_script": "导出可复现脚本",
        "export_report": "导出报告(Word)",
        "report_done": "报告已保存:\n{d}",
        "report_fail": "报告导出失败(是否已装 python-docx?)",
        "repro_done": "已保存 reproduce.R + data.csv 到:\n{d}",
        "repro_none": "请先运行一次分析",
        "saved": "已保存",
        "outputs": "产物",
        "map_columns": "把你的列对应上",
        "optional": "(选填)",
        "map_missing": "请对应好必需的列",
        "use_paste": "粘贴 / 录入",
        "use_grid": "录入表格",
        "grid_hint": "在这个分析所需的列里直接录入或粘贴数据(右键可加/删行);无需列映射。",
        "grid_use": "使用此表格",
        "grid_empty": "请先录入一些数据",
        "grid_used": "已使用表格数据",
        "paste_use": "使用这些数据",
        "paste_hint": "从 Excel 粘贴数据行(制表符或逗号分隔);第一行可以是你的列名。",
        "paste_empty": "请先粘贴一些数据",
        "r_ok": "R 就绪",
        "r_missing": "未找到 R",
        "r_locate": "指定 Rscript.exe…",
        "select_method": "在左侧选择一个方法。",
        "data": "数据",
        "use_example": "内置示例",
        "use_mine": "我的 CSV 文件",
        "choose_file": "选择 CSV…",
        "choose_dir": "选择文件夹…",
        "loaded": "已载入",
        "columns_needed": "所需列",
        "download_template": "下载示例作模板",
        "parameters": "参数",
        "run_example": "运行(示例数据)",
        "run_mine": "运行(我的数据)",
        "running": "运行中…",
        "cancel": "取消",
        "pick_first": "请先选择 CSV",
        "log": "日志",
        "results": "结果",
        "figures": "图",
        "tables": "表",
        "memory": "内存",
        "open_folder": "打开输出目录",
        "done_ok": "完成 —— 返回码 {rc} · {nimg} 图 / {ntbl} 表",
        "done_fail": "运行失败(返回码 {rc})。见上方日志。",
        "no_r_title": "未找到 R",
        "no_r_body": "Bio Wingman 需要 R(Rscript)。请安装 R 4.x,或点「指定 Rscript.exe」手动指定。",
        "no_tk_body": "此 Python 缺少 tkinter,请从 python.org 重装 Python(含 Tcl/Tk)。",
        "peak_mem": "预估峰值 {gb} GB / 可用 {avail} GB",
    },
}


def _detect_default() -> str:
    try:
        import ctypes
        # 0x0409=en, 0x0804=zh-CN;取主语言 ID 低字节 0x04 = 中文
        if (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0xFF) == 0x04:
            return "zh"
    except Exception:
        pass
    return "en"


class _I18N:
    def __init__(self):
        self.lang = self._load()
        self._binds = []

    def _cfg_path(self):
        return config_dir() / "config.json"

    def _load(self):
        try:
            cfg = json.loads(self._cfg_path().read_text(encoding="utf-8"))
            if cfg.get("lang") in STRINGS:
                return cfg["lang"]
        except Exception:
            pass
        return _detect_default()

    def save(self):
        try:
            p = self._cfg_path()
            cfg = {}
            if p.exists():
                cfg = json.loads(p.read_text(encoding="utf-8"))
            cfg["lang"] = self.lang
            p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def t(self, key, **kw):
        s = STRINGS.get(self.lang, {}).get(key) or STRINGS["en"].get(key) or key
        return s.format(**kw) if kw else s

    def both(self, key):
        return f'{STRINGS["en"].get(key, key)} / {STRINGS["zh"].get(key, key)}'

    def title_of(self, manifest):
        """方法标题按当前语言取:英文用 title_en,中文用 title。"""
        if self.lang == "en":
            return manifest.get("title_en") or manifest.get("title") or manifest.get("id")
        return manifest.get("title") or manifest.get("title_en") or manifest.get("id")

    def bind(self, fn):
        """注册"重贴文案"回调,并立即执行一次。"""
        self._binds.append(fn)
        fn()

    def toggle(self):
        self.set_language("zh" if self.lang == "en" else "en")

    def set_language(self, lang):
        if lang in STRINGS and lang != self.lang:
            self.lang = lang
            self.save()
            for fn in list(self._binds):
                try:
                    fn()
                except Exception:
                    pass


I18N = _I18N()
