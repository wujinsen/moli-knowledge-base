#!/usr/bin/env python3
"""C4 guard: 物质百科 J2 — 金瓶梅物—人—地交叉索引。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import DATA_DIR

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []

    index_path = DATA_DIR / "items_cross_index.json"
    topics_path = DATA_DIR / "jinpingmei.items_topics.json"

    if not index_path.exists():
        print("FAIL: missing items_cross_index.json — run build_items_cross_index.py --write")
        return 1

    index = json.loads(index_path.read_text(encoding="utf-8"))
    jpm = (index.get("books") or {}).get("jinpingmei")
    if not jpm:
        errors.append("items_cross_index 缺 jinpingmei 段")
    else:
        if jpm.get("count", 0) < 20:
            errors.append(f"金瓶梅 items 过少: {jpm.get('count')}")
        by_loc = jpm.get("byLocation") or {}
        if len(by_loc) < 5:
            errors.append(f"byLocation 过少: {len(by_loc)}（期望 ≥5）")
        expected_locs = {"西门府", "清河县", "李瓶儿房", "西门庆生药铺"}
        missing = expected_locs - set(by_loc)
        if missing:
            errors.append(f"byLocation 缺关键地点: {sorted(missing)}")
        for loc in ("西门府", "清河县"):
            rows = by_loc.get(loc) or []
            if len(rows) < 2:
                errors.append(f"{loc} 名物过少: {len(rows)}")

    if not topics_path.exists():
        errors.append("missing jinpingmei.items_topics.json")
    else:
        topics = json.loads(topics_path.read_text(encoding="utf-8"))
        if topics.get("book") != "金瓶梅":
            errors.append("jinpingmei.items_topics book 字段错误")
        links = topics.get("links") or {}
        if len(links) < 1:
            errors.append("jinpingmei topic links 为空")

    if errors:
        print("guard_items_j2_jpm FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"guard_items_j2_jpm OK: {jpm['count']} items · "
        f"{len(jpm.get('byLocation') or {})} locations · "
        f"{len(links)} items with topic links"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
