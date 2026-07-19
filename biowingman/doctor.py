# -*- coding: utf-8 -*-
"""
内存 doctor —— 平台最差异化、竞品全空白的一层。全部靠现成库拼胶水:
  · 机器体检: psutil(内存/CPU) + platform
  · 数据规模不整载读取: 纯 Python 读 CSV 表头+行数;anndata backed='r' 读 h5ad 维度
  · 临跑前红绿灯: 理论内存模型 × 数据规模 vs 可用内存 → 绿/黄/红(诚实:带误差的估算)

诚实原则: 内存预估是"带误差的启发式",不承诺精确;经离线基准校准前一律标 calibrated=false。
"""
from __future__ import annotations
import csv
import os
import platform
from pathlib import Path

import psutil

GB = 1024 ** 3


# ---------------------------------------------------------------- 机器体检
def machine_profile() -> dict:
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu_name": platform.processor() or "unknown",
        "cpu_physical": psutil.cpu_count(logical=False),
        "cpu_logical": psutil.cpu_count(logical=True),
        "mem_total_gb": round(vm.total / GB, 1),
        "mem_available_gb": round(vm.available / GB, 1),
        "mem_used_pct": vm.percent,
        "swap_total_gb": round(sm.total / GB, 1),
        "gpu": None,  # 首版不检测; 后续可接 gpustat/官方 nvidia-ml-py, try/except 无卡优雅返回
    }


# ---------------------------------------------------------- 数据规模(不整载)
def data_profile(path: str) -> dict:
    """只读维度/大小, 绝不把整个文件载入内存。"""
    p = Path(path)
    if not p.exists():
        return {"error": f"文件不存在: {path}"}
    size = p.stat().st_size
    ext = p.suffix.lower()
    prof = {"path": str(p), "bytes": size, "size_mb": round(size / (1024 ** 2), 2),
            "kind": ext.lstrip("."), "n_rows": None, "n_cols": None}

    if ext in (".csv", ".tsv", ".txt"):
        delim = "\t" if ext == ".tsv" else ","
        # ★逐行流式(不整载文件,防大文件把体检器自己 OOM)+ 多编码兜底
        # (大陆 Excel 另存的 CSV 多为 GBK/CP936;utf-8 读失败会 500)
        for enc in ("utf-8-sig", "gb18030", "latin-1"):
            try:
                with open(p, "r", encoding=enc, newline="") as f:
                    reader = csv.reader(f, delimiter=delim)
                    header = next(reader, [])
                    prof["n_cols"] = max(len(header) - 1, 0)   # 减掉首列
                    prof["n_rows"] = sum(1 for _ in reader)    # 数据行数(不含表头)
                prof["encoding"] = enc
                break
            except UnicodeDecodeError:
                continue                                       # 换下一种编码重试
            except csv.Error as e:                             # 畸形 CSV(NUL/超长字段)不致 500
                prof["warn"] = f"CSV 解析失败(可能非标准表格): {e}"
                prof["encoding"] = enc
                break
        else:
            prof["warn"] = "编码无法识别,请将文件另存为 UTF-8 编码的 CSV。"
    elif ext in (".h5ad",):
        try:
            import anndata
            ad = anndata.read_h5ad(p, backed="r")         # 只映射, 不载表达矩阵
            prof["n_rows"], prof["n_cols"] = int(ad.n_vars), int(ad.n_obs)  # 基因, 细胞
            prof["n_obs"], prof["n_vars"] = int(ad.n_obs), int(ad.n_vars)
            ad.file.close()
        except Exception as e:
            prof["warn"] = f"h5ad 维度读取失败: {e}"
    elif ext in (".rds", ".rdata"):
        prof["warn"] = "rds/RData 无轻量元数据, 仅按文件大小粗估(膨胀系数 3-10x)。"
    else:
        prof["warn"] = "未知格式, 仅按文件大小估算。"
    return prof


# ------------------------------------------------- 内存峰值理论估算 + 红绿灯
def estimate_peak(mem_hint: dict, primary: dict) -> dict:
    """按 manifest 的内存模型 + 主输入维度, 估算峰值内存(字节)。物理动机式, 非拟合。"""
    model = mem_hint.get("model", "linear")
    bpc = mem_hint.get("bytes_per_cell", 8)
    copies = mem_hint.get("matrix_copies", 3)
    detail = ""
    peak = None
    # ★维度未知(.rds/.RData 无轻量元数据、或 h5ad 读维度失败):按维度的模型无法估内存,
    #   不能用 `or 0` 兜底成 0 从而误判绿灯。标 dim_unknown 让 redlight 转黄并诚实提示。
    dim_unknown = ((model in ("wgcna_quadratic", "bulk_dense") and primary.get("n_rows") is None)
                   or (model in ("scrna_dense", "bulk_dense") and primary.get("n_cols") is None))

    if model == "wgcna_quadratic":
        genes = primary.get("n_rows") or 0                # 表达矩阵: 行=基因
        peak = bpc * genes * genes * copies + (primary.get("bytes") or 0)
        detail = f"~{copies}×8字节×基因²  (基因数={genes})"
    elif model == "scrna_dense":
        cells = primary.get("n_cols") or 0                # counts: 列=细胞
        genes = primary.get("n_rows") or 0
        hvg = min(mem_hint.get("hvg", 2000), genes) if genes else mem_hint.get("hvg", 2000)
        peak = bpc * cells * hvg * copies + (primary.get("bytes") or 0)
        detail = f"~{copies}×8字节×细胞×HVG  (细胞={cells}, HVG={hvg})"
    elif model == "bulk_dense":
        genes = primary.get("n_rows") or 0                # bulk 表达矩阵: 行=基因, 列=样本
        samples = primary.get("n_cols") or 0
        peak = bpc * genes * max(samples, 1) * copies + (primary.get("bytes") or 0)
        detail = f"~{copies}×8字节×基因×样本  (基因={genes}, 样本={samples})"
    elif model == "mr_linear":
        peak = (primary.get("bytes") or 0) * copies       # MR: SNP 表很小, 随文件线性
        detail = f"~{copies}× 输入文件大小 (SNP 汇总表, 内存开销小)"
    else:  # linear 兜底
        peak = (primary.get("bytes") or 0) * copies
        detail = f"~{copies}× 输入文件大小"

    return {"predicted_peak_bytes": int(peak), "predicted_peak_gb": round(peak / GB, 2),
            "model": model, "detail": detail, "calibrated": mem_hint.get("calibrated", False),
            "killer_dim": mem_hint.get("killer_dim", ""), "dim_unknown": dim_unknown}


def redlight(predicted_peak_bytes: int, available_bytes: int | None = None) -> dict:
    if available_bytes is None:
        available_bytes = psutil.virtual_memory().available
    ratio = predicted_peak_bytes / available_bytes if available_bytes else 9999.0
    ratio = min(ratio, 9999.0)                            # 防 inf 序列化成非法 JSON
    if ratio < 0.5:
        level, advice = "green", "内存充足,可直接运行。"
    elif ratio < 0.8:
        level, advice = "yellow", "内存偏紧,建议关掉其它程序;大数据可考虑下采样/减少基因。"
    else:
        level, advice = "red", "内存很可能不足。建议:下采样样本/细胞、只保留高变基因、或换更大内存的机器。"
    return {
        "level": level, "ratio": round(ratio, 2),
        "predicted_peak_gb": round(predicted_peak_bytes / GB, 2),
        "available_gb": round(available_bytes / GB, 2),
        "advice": advice,
        "disclaimer": "此为带误差的理论估算(未校准),仅供参考,不代表精确峰值。",
    }
