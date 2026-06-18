#!/usr/bin/env python3
"""D6 守卫：校验《西游记》丹道意象与五行修心网络。

- imagery 数量下限
- 五行五众核心符号（心猿金/木母木/黄婆土/意马水/婴儿火）齐备且带 五行-X 标签
- 五行生克 predicate（相克/交并/调和/相济）边数量下限
- xiyouji.shi-wuxing.json 存在且每个五行至少 1 节点、生克边充足
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

IMG_DIR = CONTENT / "imagery" / "西游记"
ELEMENTS = ["金", "木", "土", "水", "火"]
WUXING_PRED = {"相克", "交并", "调和", "相济"}
CORE = {
    "xyj-dan-xinyuan": "金",
    "xyj-dan-mumu": "木",
    "xyj-dan-huangpo": "土",
    "xyj-dan-yima": "水",
    "xyj-dan-yinger": "火",
}

MIN_IMAGERY = 35
MIN_EDGES = 10


def main() -> int:
    errors: list[str] = []
    warns: list[str] = []

    md = sorted(IMG_DIR.glob("*.md"))
    if len(md) < MIN_IMAGERY:
        errors.append(f"imagery 数量 {len(md)} < {MIN_IMAGERY}")

    elem_by_id: dict[str, str | None] = {}
    edge_count = 0
    for p in md:
        fm, _ = parse_frontmatter(p)
        tags = fm.get("tags") or []
        el = next((str(t)[3:] for t in tags if str(t).startswith("五行-")), None)
        elem_by_id[fm["id"]] = el
        for link in fm.get("links") or []:
            if link.get("predicate") in WUXING_PRED:
                edge_count += 1

    for cid, want in CORE.items():
        if cid not in elem_by_id:
            errors.append(f"缺核心五行符号：{cid}")
        elif elem_by_id[cid] != want:
            errors.append(f"{cid} 五行标签应为「五行-{want}」，实为「{elem_by_id[cid]}」")

    if edge_count < MIN_EDGES:
        errors.append(f"五行生克边 {edge_count} < {MIN_EDGES}")

    wx_path = DATA_DIR / "xiyouji.shi-wuxing.json"
    if not wx_path.exists():
        errors.append("缺 xiyouji.shi-wuxing.json（先跑 build_shi_wuxing.py --write）")
    else:
        data = json.loads(wx_path.read_text(encoding="utf-8"))
        for e in ELEMENTS:
            if data.get("element_counts", {}).get(e, 0) < 1:
                errors.append(f"shi-wuxing.json 五行「{e}」无节点")
        if len(data.get("edges") or []) < MIN_EDGES:
            errors.append(f"shi-wuxing.json 生克边 {len(data.get('edges') or [])} < {MIN_EDGES}")
        if len(data.get("chains") or []) < 5:
            warns.append(f"修心链路仅 {len(data.get('chains') or [])} 条（建议 ≥5）")

    for w in warns:
        print(f"  [warn] {w}")
    if errors:
        print("guard_shi_xyj 失败：")
        for e in errors:
            print(f"  [err] {e}")
        return 1
    print(f"guard_shi_xyj 通过：{len(md)} imagery · {edge_count} 生克边 · 五行五众齐备")
    return 0


if __name__ == "__main__":
    sys.exit(main())
