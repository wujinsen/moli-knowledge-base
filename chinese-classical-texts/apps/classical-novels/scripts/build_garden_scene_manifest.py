#!/usr/bin/env python3
"""从 locations（garden_zone + coord）生成大观园 Pixi 实景 manifest。

坐标以 seed_garden_coords.py / 知识库为准，不复用 raw/scan 图内方位。

用法:
  python scripts/build_garden_scene_manifest.py [--write]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
LOC_DIR = ROOT / "src" / "content" / "locations" / "红楼梦"
OUT = DATA_DIR / "红楼梦.garden_scene_full.json"
PILOT = DATA_DIR / "红楼梦.garden_scene.json"

# zone → (w, h) 等距占位尺寸
SIZE_BY_ZONE: dict[str, tuple[int, int]] = {
    "居所": (200, 150),
    "仪典": (240, 170),
    "水系": (130, 95),
    "亭榭": (150, 110),
    "寺观": (140, 105),
    "路径": (90, 70),
    "服务": (110, 80),
}

PRIORITY = ["仪典", "居所", "亭榭", "水系", "寺观", "路径", "服务"]

GARDEN_LAYOUT_DISCLAIMER = (
    "坐标属红学 inference（南北中轴说）；第17回游线顺序来自正文。"
    "院间「步数」为逻辑换算，非测绘尺度，不可与原文丈尺对勘。scan/复原园图不参与落位。"
)


def load_garden_nodes() -> list[dict]:
    nodes: list[dict] = []
    for p in sorted(LOC_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != "红楼梦":
            continue
        zone = fm.get("garden_zone")
        coord = fm.get("coord")
        if not zone or not coord or not isinstance(coord, dict):
            continue
        nodes.append(
            {
                "id": fm.get("id") or p.stem,
                "name": fm.get("name") or p.stem,
                "plaque": fm.get("plaque"),
                "zone": zone,
                "logical": {"x": int(coord["x"]), "y": int(coord["y"])},
                "summary": (fm.get("summary") or "")[:160],
            }
        )
    nodes.sort(
        key=lambda n: (
            PRIORITY.index(n["zone"]) if n["zone"] in PRIORITY else 99,
            n["logical"]["y"],
            n["logical"]["x"],
        )
    )
    return nodes


def build_manifest() -> dict:
    nodes = load_garden_nodes()
    pilot = json.loads(PILOT.read_text(encoding="utf-8")) if PILOT.exists() else {}

    buildings = []
    for n in nodes:
        w, h = SIZE_BY_ZONE.get(n["zone"], (120, 90))
        # note 直接用词条 summary（清洁版，不再前缀「匾…」——匾额在 plaque 字段单列）
        note = n["summary"]
        entry: dict = {
            "id": n["id"],
            "name": n["name"],
            "zone": n["zone"],
            "logical": n["logical"],
            "w": w,
            "h": h,
            "link": f"/honglou/l/{n['id']}",
        }
        if n.get("plaque"):
            entry["plaque"] = n["plaque"]
        if note:
            entry["note"] = note
        # 保留已有精修 sprite（pilot 三院）
        for pb in pilot.get("buildings") or []:
            if pb.get("id") == n["id"] and pb.get("sprite"):
                entry["sprite"] = pb["sprite"]
                entry["w"] = pb.get("w", w)
                entry["h"] = pb.get("h", h)
        buildings.append(entry)

    paths = pilot.get("paths") or [
        {"from": "潇湘馆", "to": "沁芳亭"},
        {"from": "沁芳亭", "to": "怡红院"},
    ]

    return {
        "book": "红楼梦",
        "slug": "honglou",
        "title": "大观园·等距全园",
        "subtitle": f"共 {len(buildings)} 处 · 坐标同源 /honglou/map · 非 scan 图方位",
        "width": 2400,
        "height": 1500,
        "gallery": "/honglou/scene/daguanyuan-archviz-project-layout.png",
        "gallery_blueprint": "/honglou/scene/layout-blueprint-project.png",
        "scan_reference": "/honglou/scene/scan-reference.png",
        "px_per_step": 6,
        "coord_basis": "seed_garden_coords",
        "scale_note": GARDEN_LAYOUT_DISCLAIMER,
        "buildings": buildings,
        "npcs": pilot.get("npcs") or [],
        "paths": paths,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    data = build_manifest()
    print(f"nodes: {len(data['buildings'])} → {OUT.name}")
    if args.write:
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("written")
    else:
        print("(dry-run, add --write)")


if __name__ == "__main__":
    main()
