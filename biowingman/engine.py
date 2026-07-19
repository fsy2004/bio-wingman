# -*- coding: utf-8 -*-
"""跑一个方法:构 argv、定位解释器(R 或 Python)、注入 BIOWINGMAN_TOOLKIT、子进程流式输出、
墙钟超时、收产物。UI 无关:后台线程读子进程,主线程(Tk)用 Run.poll() 非阻塞取行。"""
from __future__ import annotations
import json
import os
import queue
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

from .paths import ROOT, MANIFESTS, TOOLKIT, CONFIG, run_root
from .rlocate import find_rscript
from .pylocate import find_python

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0   # 不弹子进程黑窗


def list_methods() -> list[dict]:
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(MANIFESTS.glob("*.json"))]


# 生信流程阶段(有序,驱动左侧树)。(key, 中文, English)—— 按数据处理流程分类
STAGES = [
    ("S0", "数据获取 / 导入",     "Data Acquisition"),
    ("S1", "质控 / 预处理",       "QC & Preprocessing"),
    ("S2", "标准化 / 批次校正",   "Normalization & Batch"),
    ("S3", "差异分析",           "Differential Analysis"),
    ("S4", "功能富集",           "Functional Enrichment"),
    ("S5", "下游分析",           "Downstream Analysis"),
    ("S6", "因果推断 (MR)",      "Causal Inference (MR)"),
    ("S7", "建模 / 诊断 (ML)",   "Modeling & Diagnostics"),
    ("S8", "可视化 / 报告",       "Visualization & Report"),
]
_STAGE_KEYS = {k for k, _, _ in STAGES}


def grouped_methods():
    """返回 [(stage_key, 中文, English, [methods 按 item_order]) ...],按 STAGES 顺序。"""
    buckets = {}
    for m in list_methods():
        buckets.setdefault(m.get("stage", "S3"), []).append(m)
    out = []
    for k, zh, en in STAGES:
        items = sorted(buckets.get(k, []), key=lambda m: m.get("item_order", 999))
        if items:
            out.append((k, zh, en, items))
    for g, items in buckets.items():   # 兜底:不在 STAGES 里的阶段
        if g not in _STAGE_KEYS:
            out.append((g, g, g, sorted(items, key=lambda m: m.get("item_order", 999))))
    return out


def load_manifest(mid: str) -> dict:
    return json.loads((MANIFESTS / f"{mid}.json").read_text(encoding="utf-8"))


def primary_input(m: dict):
    ins = m.get("inputs", [])
    return next((s for s in ins if s.get("primary")), ins[0] if ins else None)


def example_path(m: dict):
    pin = primary_input(m)
    if pin and pin.get("example"):
        return str(ROOT / m["workdir"] / pin["example"])
    return None


def _load_shapes():
    try:
        return json.loads((CONFIG / "column_shapes.json").read_text(encoding="utf-8")).get("shapes", {})
    except Exception:
        return {}


_SHAPES = _load_shapes()


def shape_of(m: dict):
    """返回该方法的列规格 {label_zh,label_en,columns:[...]} 或 None(无形状=回退模板)。"""
    return _SHAPES.get(m.get("shape")) if m.get("shape") else None


def build_argv(m, exe, input_path, params, outdir, col_map=None):
    argv = [exe, str(ROOT / m["entry"])]
    for spec in m.get("inputs", []):
        path = input_path if spec.get("primary") else None
        if not path and spec.get("example"):
            path = str(ROOT / m["workdir"] / spec["example"])
        if path:
            argv += [spec["flag"], str(path)]
    argv += ["--outdir", str(outdir)]
    if m.get("analysis"):                       # 叶子固定标志:一个家族适配器靠 --analysis 选具体输出
        argv += ["--analysis", str(m["analysis"])]
    for role, col in (col_map or {}).items():   # 列映射:用户列名 → --<role>(col_of/getarg 覆盖默认列名)
        if col:
            argv += ["--" + role, str(col)]
    flags = m.get("param_flags", {})
    for k, v in (params or {}).items():
        if k in flags and v is not None and str(v) != "":
            argv += [flags[k], str(v)]
    return argv


class Run:
    """一次方法运行。start() 起后台线程;UI 反复 poll() 取 (kind, payload):
    kind ∈ {'log','error','done'};done 的 payload 是 returncode。结束后读 .outputs / .returncode。"""

    def __init__(self, m: dict, input_path: str | None = None, params: dict | None = None,
                 timeout: int = 1800, col_map: dict | None = None):
        self.m = m
        self.input_path = input_path
        self.params = params or {}
        self.col_map = col_map or {}
        self.timeout = timeout
        self.q: queue.Queue = queue.Queue()
        self.outdir = run_root() / f'{m["id"]}_{time.strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:6]}'
        self.proc = None
        self.returncode = None
        self.outputs: list[str] = []
        self._cancelled = False
        self.done = False

    def start(self):
        threading.Thread(target=self._worker, daemon=True).start()

    def cancel(self):
        self._cancelled = True
        if self.proc and self.proc.poll() is None:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                               creationflags=CREATE_NO_WINDOW, capture_output=True)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass

    def _worker(self):
        interp = self.m.get("interp", "Rscript")          # 每个 manifest 声明用 R 还是 Python
        if interp == "Rscript":
            exe = find_rscript()
            if not exe:
                self.q.put(("error", "R (Rscript) not found / 未找到 R。请安装 R,或在设置中指定 Rscript.exe。"))
                self._finish(127)
                return
        else:
            exe = find_python()
            if not exe:
                self.q.put(("error", "Python not found / 未找到 Python。请安装 Python 3.x,或在设置中指定 python.exe。"))
                self._finish(127)
                return
        try:
            self.outdir.mkdir(parents=True, exist_ok=True)
            argv = build_argv(self.m, exe, self.input_path, self.params, self.outdir, self.col_map)
            env = os.environ.copy()
            env["BIOWINGMAN_TOOLKIT"] = str(TOOLKIT)
            env["PATH"] = str(Path(exe).parent) + os.pathsep + env.get("PATH", "")
            if self._cancelled:                 # Popen 之前已被取消 → 不启动进程
                self._finish(130)
                return
            self.q.put(("log", "$ " + subprocess.list2cmdline(argv)))
            self.proc = subprocess.Popen(
                argv, cwd=str(ROOT / self.m["workdir"]),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace", bufsize=1,
                creationflags=CREATE_NO_WINDOW, env=env,
            )
        except Exception as e:
            self.q.put(("error", f"launch failed / 启动失败: {e}"))
            self._finish(127)
            return

        start = time.monotonic()
        self._start_wall = time.time()      # 墙钟:用于判定 assets 里哪些图是本次生成

        def watchdog():
            while self.proc and self.proc.poll() is None:
                if not self._cancelled and time.monotonic() - start > self.timeout:
                    self.q.put(("error", f"运行超过 {self.timeout}s 已终止 / timed out after {self.timeout}s。"
                                        "若数据规模较大属正常,可换更小数据或联系作者调高超时上限(非软件故障)。"))
                    self.cancel()
                    return
                time.sleep(1)

        threading.Thread(target=watchdog, daemon=True).start()
        try:
            for line in self.proc.stdout:
                self.q.put(("log", line.rstrip("\r\n")))
        except Exception:
            pass
        self.proc.wait()
        rc = self.proc.returncode
        self._harvest_assets()      # 有些模块把展示图写进自身 assets/ 而非 --outdir → 搬进 outdir
        for o in self.m.get("outputs", []):
            self.outputs += sorted(str(p) for p in self.outdir.glob(o["glob"]))
        self._finish(rc)

    def _harvest_assets(self):
        """部分复用模块把 png/pdf 写进 <workdir>/assets(README 展示图)而非 --outdir。
        把本次运行(mtime 新于开始)生成的图搬进 run 目录,让结果区能展示;
        用 mtime 门槛避免搬到上一次运行的旧图(失败的运行不会误显示陈图)。"""
        try:
            assets = ROOT / self.m["workdir"] / "assets"
            if not assets.is_dir():
                return
            cutoff = getattr(self, "_start_wall", 0) - 1
            for p in sorted(assets.glob("*.png")) + sorted(assets.glob("*.pdf")):
                try:
                    if p.stat().st_mtime < cutoff:
                        continue
                    dst = self.outdir / p.name
                    if not dst.exists():
                        shutil.copyfile(p, dst)
                except Exception:
                    continue
        except Exception:
            pass

    def _finish(self, rc):
        self.returncode = rc
        self.done = True
        self.q.put(("done", rc))

    def poll(self):
        """非阻塞返回积累的 (kind, payload) 列表。"""
        items = []
        try:
            while True:
                items.append(self.q.get_nowait())
        except queue.Empty:
            pass
        return items
