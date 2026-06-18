#!/usr/bin/env python3
"""D6 P3：生成 xiyouji.shi-wuxing.json（五行生克 · 修心网络索引）。

把《西游记》丹道意象按五行（金木水火土）归类，汇总意象间的生克边
（相克 / 交并 / 调和 / 相济），供「修心网络」面板渲染与 quanshi 互链。
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = CONTENT / "imagery" / "西游记"

ELEMENTS = ["金", "木", "土", "水", "火"]
WUXING_PRED = ["相克", "交并", "调和", "相济"]


def element_of(tags: list) -> str | None:
    for t in tags or []:
        s = str(t)
        if s.startswith("五行-") and s[3:] in ELEMENTS:
            return s[3:]
    return None


def build() -> dict:
    items: dict[str, dict] = {}
    by_element: dict[str, list[dict]] = {e: [] for e in ELEMENTS}
    edges: list[dict] = []
    rel_counts: dict[str, int] = {p: 0 for p in WUXING_PRED}

    for p in sorted(IMG_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != "西游记":
            continue
        iid = fm["id"]
        items[iid] = {
            "id": iid,
            "title": fm.get("title", iid),
            "subtype": fm.get("subtype", ""),
            "element": element_of(fm.get("tags")),
            "characters": fm.get("characters") or [],
        }

    # 第二轮：解析生克边（仅 imagery↔imagery）
    seen_edge: set[tuple] = set()
    for p in sorted(IMG_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != "西游记":
            continue
        src = fm["id"]
        for link in fm.get("links") or []:
            pred = link.get("predicate")
            if pred not in WUXING_PRED:
                continue
            tgt = link.get("target", "")
            if link.get("target_kind") != "imagery" and tgt not in items:
                continue
            # 无向去重（相克/交并/相济 对称；调和有向，保留方向）
            if pred in ("相克", "交并", "相济"):
                key = (pred, tuple(sorted([src, tgt])))
            else:
                key = (pred, src, tgt)
            if key in seen_edge:
                continue
            seen_edge.add(key)
            rel_counts[pred] += 1
            edges.append(
                {
                    "source": src,
                    "target": tgt,
                    "sourceTitle": items.get(src, {}).get("title", src),
                    "targetTitle": items.get(tgt, {}).get("title", tgt),
                    "sourceElement": items.get(src, {}).get("element"),
                    "targetElement": items.get(tgt, {}).get("element"),
                    "predicate": pred,
                    "chapter": link.get("chapter"),
                    "note": link.get("note"),
                }
            )

    for it in items.values():
        if it["element"]:
            by_element[it["element"]].append(
                {"id": it["id"], "title": it["title"], "characters": it["characters"]}
            )

    chains_path = DATA_DIR / "西游记.imagery-chains.json"
    chains = []
    if chains_path.exists():
        chains = json.loads(chains_path.read_text(encoding="utf-8")).get("chains") or []

    return {
        "book": "西游记",
        "slug": "xiyouji",
        "generated_by": "build_shi_wuxing.py",
        "elements": ELEMENTS,
        "by_element": by_element,
        "element_counts": {e: len(by_element[e]) for e in ELEMENTS},
        "edges": edges,
        "relation_counts": rel_counts,
        "chains": chains,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    payload = build()

    if args.write:
        out = DATA_DIR / "xiyouji.shi-wuxing.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(
            f"  xiyouji wuxing: {sum(payload['element_counts'].values())} element-tagged · "
            f"{len(payload['edges'])} 生克边 · {len(payload['chains'])} chains"
        )
        for e in ELEMENTS:
            print(f"    {e}: {payload['element_counts'][e]}")
        for pred, n in payload["relation_counts"].items():
            print(f"    {pred}: {n}")
        print(f"written → {out.name}")
    else:
        print(json.dumps(payload["relation_counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
