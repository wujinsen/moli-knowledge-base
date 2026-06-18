#!/usr/bin/env python3
"""C1 guard: 白银流 J3–J4 — silver.json 与 financial.json 互证。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]


def load_tx_ids(book: str) -> set[str]:
    d = CONTENT / "transactions" / book
    ids: set[str] = set()
    for p in d.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") == book:
            ids.add(fm["id"])
    return ids


def main() -> int:
    silver_path = DATA_DIR / "jinpingmei.silver.json"
    fin_path = DATA_DIR / "jinpingmei.financial.json"
    errors: list[str] = []

    if not silver_path.exists():
        print(f"FAIL: missing {silver_path.name}")
        return 1

    silver = json.loads(silver_path.read_text(encoding="utf-8"))
    tx_ids = load_tx_ids("金瓶梅")

    for key in ("pools", "links", "timeline", "transactions", "hub"):
        if key not in silver:
            errors.append(f"silver.json 缺字段 {key}")

    silver_tx_ids = {t["id"] for t in silver.get("transactions", [])}
    if silver_tx_ids != tx_ids:
        missing = tx_ids - silver_tx_ids
        extra = silver_tx_ids - tx_ids
        if missing:
            errors.append(f"silver.json 缺交易: {sorted(missing)[:5]}")
        if extra:
            errors.append(f"silver.json 多余交易: {sorted(extra)[:5]}")

    if not silver.get("pools"):
        errors.append("pools 为空")
    if not silver.get("links"):
        errors.append("links 为空（桑基图无边）")
    if not silver.get("timeline"):
        errors.append("timeline 为空（累计曲线无数据）")

    hub = silver.get("hub", {}).get("name")
    if hub != "西门庆府":
        errors.append(f"hub 应为西门庆府，现为 {hub}")

    if fin_path.exists():
        fin = json.loads(fin_path.read_text(encoding="utf-8"))
        for track in fin.get("tracks", []):
            for ev in track.get("events", []):
                for tid in ev.get("transaction_refs") or []:
                    if tid not in silver_tx_ids:
                        errors.append(f"{track['id']}/{ev['id']}: ref {tid} 不在 silver.json")

    if errors:
        print("guard_silver_j34 FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    n_tx = silver["transaction_count"]
    n_pool = len(silver["pools"])
    n_ch = len(silver["timeline"])
    print(
        f"guard_silver_j34 OK: {n_tx} tx · {n_pool} pools · {n_ch} chapter points · "
        f"{silver['total_liang']} 两"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
