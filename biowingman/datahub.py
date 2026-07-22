# -*- coding: utf-8 -*-
"""Project-local data assets and lightweight preparation helpers.

The analysis modules remain the authority for scientific transformations.  This
module only connects their outputs to downstream inputs and creates the tiny
sample-group tables that are an explicit user decision, not an analysis.
"""
from __future__ import annotations

import csv
import time
from pathlib import Path

from .paths import run_root


def latest_asset(names: list[str] | tuple[str, ...]) -> str | None:
    """Return the newest existing run/preparation file whose basename matches."""
    wanted = {str(name).casefold() for name in names if name}
    if not wanted:
        return None
    matches: list[Path] = []
    try:
        for path in run_root().rglob("*"):
            if path.is_file() and path.name.casefold() in wanted:
                matches.append(path)
    except OSError:
        return None
    if not matches:
        return None
    return str(max(matches, key=lambda path: path.stat().st_mtime))


def resolve_inputs(manifest: dict) -> dict[str, str]:
    """Resolve manifest inputs from previous outputs using ``auto_from`` names."""
    resolved: dict[str, str] = {}
    for spec in manifest.get("inputs", []):
        path = latest_asset(spec.get("auto_from", []))
        if path:
            resolved[str(spec.get("name", "input"))] = path
    return resolved


def read_matrix_samples(path: str) -> list[str]:
    """Read sample names from the first row of a gene-by-sample CSV/TSV."""
    source = Path(path)
    delimiter = "\t" if source.suffix.lower() in {".txt", ".tsv"} else ","
    for encoding in ("utf-8-sig", "gb18030", "latin-1"):
        try:
            with source.open("r", encoding=encoding, newline="") as handle:
                header = next(csv.reader(handle, delimiter=delimiter), [])
            return [cell.strip() for cell in header[1:] if cell.strip()]
        except UnicodeDecodeError:
            continue
        except (OSError, csv.Error):
            return []
    return []


def write_sample_groups(assignments: list[tuple[str, str]]) -> tuple[str, str]:
    """Write grouping and numeric-trait assets for downstream GEO workflows."""
    prepared = run_root() / "_prepared"
    prepared.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    group_path = prepared / f"sample_group_{stamp}.csv"
    trait_path = prepared / f"sample_traits_{stamp}.csv"
    with group_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Sample", "Group"])
        writer.writerows(assignments)
    with trait_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Sample", "Group"])
        writer.writerows((sample, 0 if group == "con" else 1) for sample, group in assignments)
    # Stable aliases let manifest auto-wiring find the newest prepared assets.
    stable_group = prepared / "sample_group.csv"
    stable_trait = prepared / "sample_traits.csv"
    stable_group.write_bytes(group_path.read_bytes())
    stable_trait.write_bytes(trait_path.read_bytes())
    return str(stable_group), str(stable_trait)
