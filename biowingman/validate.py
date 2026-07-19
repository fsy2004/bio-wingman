# -*- coding: utf-8 -*-
"""数值级数据校验(结果可信度第一道防线):按 shape 检查各研究的值——
数值性 / 整数 / 计数非负 / 样本量·SD 为正 / 事件数≤样本量。返回带研究名的清晰消息(空=通过)。
适用所有数据源(示例/上传/粘贴);学 MetaInsight 的"逐研究命名消息"做法。"""
from __future__ import annotations
import csv

# 角色语义(按名判定,覆盖各 shape 常见列)
_COUNT = {"ai", "bi", "ci", "di", "tp", "fp", "fn", "tn", "events", "event", "x", "xi", "cases"}
_POSITIVE = {"n", "ni", "n1i", "n2i", "total", "nt", "nc", "sd1i", "sd2i", "sdi", "sd",
             "sei", "se", "time", "n_total"}
_STUDY_ROLES = ("slab", "study", "studlab", "author", "id")


def _rows_by_role(data_path, mapping, shape):
    """读 CSV → 每行一个 {role: value_str}。mapping(role→用户列名)优先;否则列名即角色。"""
    with open(data_path, encoding="utf-8-sig", newline="") as f:
        rd = list(csv.reader(f))
    if not rd:
        return [], []
    header = [h.strip() for h in rd[0]]
    hidx = {h: i for i, h in enumerate(header)}
    roles = [c["role"] for c in shape["columns"]]
    # role → 列索引
    col_of = {}
    for r in roles:
        name = (mapping or {}).get(r, r)
        if name in hidx:
            col_of[r] = hidx[name]
    # 研究名列
    slab_i = next((hidx[s] for s in _STUDY_ROLES if s in hidx), None)
    out = []
    for line in rd[1:]:
        if not any(x.strip() for x in line):
            continue
        row = {r: (line[i].strip() if i < len(line) else "") for r, i in col_of.items()}
        row["_slab"] = line[slab_i].strip() if (slab_i is not None and slab_i < len(line)) else ""
        out.append(row)
    return out, [c for c in shape["columns"] if c["role"] in col_of]


def validate(shape, data_path, mapping=None, max_msgs=15):
    """返回消息列表(空=通过)。"""
    try:
        rows, cols = _rows_by_role(data_path, mapping, shape)
    except Exception:
        return []
    if not rows:
        return []
    spec = {c["role"]: c for c in cols}
    msgs = []

    def label(i, row):
        return row.get("_slab") or ("第 %d 行 / row %d" % (i, i))

    for i, row in enumerate(rows, 1):
        val = {}
        for role, c in spec.items():
            raw = row.get(role, "")
            if raw == "":
                continue
            if c.get("type") in ("int", "num", "number", "float"):
                try:
                    x = float(raw)
                except ValueError:
                    msgs.append('%s:「%s / %s」非数值 (%s)' % (label(i, row), c.get("zh", role), c.get("en", role), raw))
                    continue
                val[role] = x
                if c.get("type") == "int" and x != int(x):
                    msgs.append('%s:「%s」应为整数 (%s)' % (label(i, row), c.get("en", role), raw))
                if role in _COUNT and x < 0:
                    msgs.append('%s:「%s」不应为负 / should be ≥ 0 (%s)' % (label(i, row), c.get("en", role), raw))
                if role in _POSITIVE and x <= 0:
                    msgs.append('%s:「%s」应为正数 / should be > 0 (%s)' % (label(i, row), c.get("en", role), raw))
        # 跨列:事件数不应超过样本量(角色名灵活:event(s)/xi/x/cases 对 n/ni/total)
        ev = next((r for r in ("events", "event", "xi", "x", "cases") if r in val), None)
        nn = next((r for r in ("n", "ni", "total", "n_total") if r in val), None)
        if ev and nn and val[ev] > val[nn]:
            msgs.append('%s: 事件数 > 样本量 / events (%g) > total (%g)' % (label(i, row), val[ev], val[nn]))
        if len(msgs) >= max_msgs:
            msgs.append("… 还有更多,先修上面这些 / more issues; fix the above first")
            break
    return msgs
