#!/usr/bin/env python3
"""D3–D4 守卫：校验《西游记》取经路线 location 双层数据。

- 凡间站 route_order 连续（1..N 无缺无重）且带 geo
- 神话异界站带 coord、无 route_order
- 每个凡间站 appear_in 至少 1 个回目
- 事件—地点绑定覆盖：≥N 难能按章回落到某凡间站
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import CONTENT, parse_frontmatter

LOC_DIR = CONTENT / "locations" / "西游记"
EVENT_DIR = CONTENT / "events" / "西游记"

MIN_REAL = 22
MIN_BOUND_TRIB = 50


def main() -> int:
    errors: list[str] = []
    warns: list[str] = []

    real_orders: list[int] = []
    real_chapters: set[int] = set()
    myth = 0
    for p in sorted(LOC_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != "西游记":
            continue
        layer = fm.get("layer")
        order = fm.get("route_order")
        geo = fm.get("geo")
        coord = fm.get("coord")
        appear = fm.get("appear_in") or []
        if layer == "real":
            if order is None:
                errors.append(f"{fm['id']} 凡间站缺 route_order")
            else:
                real_orders.append(int(order))
            if not geo:
                errors.append(f"{fm['id']} 凡间站缺 geo")
            if not appear:
                warns.append(f"{fm['id']} 缺 appear_in")
            for s in appear:
                m = re.search(r"第(\d+)回", str(s))
                if m:
                    real_chapters.add(int(m[1]))
        elif layer == "myth":
            myth += 1
            if not coord:
                errors.append(f"{fm['id']} 异界站缺 coord")
            if order is not None:
                warns.append(f"{fm['id']} 异界站不应有 route_order")

    real_orders.sort()
    if len(real_orders) < MIN_REAL:
        errors.append(f"凡间站 {len(real_orders)} < {MIN_REAL}")
    if real_orders:
        expected = list(range(1, len(real_orders) + 1))
        if real_orders != expected:
            dups = {o for o in real_orders if real_orders.count(o) > 1}
            missing = [i for i in expected if i not in set(real_orders)]
            errors.append(f"route_order 非连续：缺{missing} 重{sorted(dups)}")

    # 事件—地点绑定覆盖
    bound = 0
    total_trib = 0
    for p in sorted(EVENT_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("subtype") != "tribulation":
            continue
        total_trib += 1
        chs = fm.get("chapters") or []
        if any(c in real_chapters for c in chs):
            bound += 1
    if bound < MIN_BOUND_TRIB:
        warns.append(f"按章回落到凡间站的难 {bound}/{total_trib} < {MIN_BOUND_TRIB}")

    for w in warns:
        print(f"  [warn] {w}")
    if errors:
        print("guard_route_xyj 失败：")
        for e in errors:
            print(f"  [err] {e}")
        return 1
    print(
        f"guard_route_xyj 通过：凡间 {len(real_orders)} 站连续 · 异界 {myth} 站 · "
        f"事件绑定 {bound}/{total_trib} 难"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
