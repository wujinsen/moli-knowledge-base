#!/usr/bin/env python3
"""C3 guard: SNA J2–J3 — sna.json 指标与 ranks 完整性。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import DATA_DIR

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    path = DATA_DIR / "jinpingmei.sna.json"
    errors: list[str] = []

    if not path.exists():
        print("FAIL: missing jinpingmei.sna.json — run build_sna.py")
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    metrics = data.get("metrics") or []

    if len(metrics) < 50:
        errors.append(f"metrics 过少: {len(metrics)}")

    for key in ("hubs", "degree_hubs", "bangxian_hubs", "factions", "silver_links"):
        if key not in data:
            errors.append(f"缺字段 {key}")

    for m in metrics:
        for field in ("degree", "betweenness", "degree_rank", "betweenness_rank"):
            if field not in m:
                errors.append(f"{m.get('id')}: 缺 {field}")
        if m.get("betweenness", 0) < 0:
            errors.append(f"{m.get('id')}: 负介数")

    ranks = [m.get("betweenness_rank") for m in metrics if m.get("betweenness_rank")]
    if len(set(ranks)) != len(ranks):
        errors.append("betweenness_rank 重复")

    if data.get("hubs") and data["hubs"][0] != metrics[0]["id"]:
        errors.append("hubs[0] 应与介数第一一致")

    if errors:
        print("guard_sna_j23 FAILED:")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1

    print(
        f"guard_sna_j23 OK: {len(metrics)} metrics · "
        f"Top {data['hubs'][:3]} · 度Top {data.get('degree_hubs', [])[:3]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
