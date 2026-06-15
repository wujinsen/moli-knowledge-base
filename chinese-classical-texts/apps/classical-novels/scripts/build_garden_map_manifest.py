#!/usr/bin/env python3
"""从 locations（garden_zone + coord）生成 ECharts 大观园地图快照。

与 /honglou/map 同源；dev 下 content store 为空时作回退，与 scene 页 JSON 策略一致。

用法:
  python scripts/build_garden_map_manifest.py [--write]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _common import DATA_DIR, parse_frontmatter

LOC_DIR = Path(__file__).resolve().parents[1] / "src" / "content" / "locations" / "红楼梦"
OUT = DATA_DIR / "红楼梦.garden_map.json"


def chapter_nums(appear_in: list) -> list[int]:
    out: list[int] = []
    for s in appear_in or []:
        m = re.search(r"第(\d+)回", str(s))
        if m:
            out.append(int(m.group(1)))
    return sorted(set(out))


def load_nodes() -> list[dict]:
    nodes: list[dict] = []
    for p in sorted(LOC_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != "红楼梦":
            continue
        zone = fm.get("garden_zone")
        coord = fm.get("coord")
        if not zone or not coord or not isinstance(coord, dict):
            continue
        couplet = fm.get("couplet")
        nodes.append(
            {
                "id": fm.get("id") or p.stem,
                "name": fm.get("name") or p.stem,
                "zone": zone,
                "category": fm.get("category"),
                "x": int(coord["x"]),
                "y": int(coord["y"]),
                "tourOrder": fm.get("tour_order"),
                "summary": fm.get("summary") or "",
                "chapters": chapter_nums(fm.get("appear_in") or []),
                "occupants": fm.get("occupants") or [],
                "plants": fm.get("plants") or [],
                "plaque": fm.get("plaque"),
                "couplet": couplet if isinstance(couplet, dict) else None,
                "nearby": fm.get("nearby") or [],
                "events": [],
            }
        )
    nodes.sort(key=lambda n: (n["y"], n["x"]))
    return nodes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    nodes = load_nodes()
    data = {
        "book": "红楼梦",
        "slug": "honglou",
        "coord_basis": "seed_garden_coords",
        "node_count": len(nodes),
        "nodes": nodes,
    }
    print(f"garden_map nodes: {len(nodes)} → {OUT.name}")
    if args.write:
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("written")
    else:
        print("(dry-run, add --write)")


if __name__ == "__main__":
    main()
