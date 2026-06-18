#!/usr/bin/env python3
"""C6 P3：生成 jinpingmei.shi-karma.json（五阶段因果闭环索引）。"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
PHASES = ["欲起", "聚敛", "极盛", "反噬", "散尽"]
OMEN_SUBTYPES = {"name_omen", "object_omen", "tune_omen"}


def build_jpm() -> dict:
    img_dir = CONTENT / "imagery" / "金瓶梅"
    by_phase: dict[str, list[dict]] = {p: [] for p in PHASES}
    seen: dict[str, set[str]] = {p: set() for p in PHASES}

    for path in sorted(img_dir.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        if fm.get("book") != "金瓶梅":
            continue
        iid = fm["id"]
        for link in fm.get("links") or []:
            if not link.get("inference"):
                continue
            phase = link.get("phase")
            if phase not in PHASES:
                continue
            if iid in seen[phase]:
                continue
            seen[phase].add(iid)
            by_phase[phase].append(
                {
                    "id": iid,
                    "title": fm.get("title", iid),
                    "subtype": fm.get("subtype", ""),
                    "temperature": link.get("temperature"),
                    "chapter": link.get("chapter") or (fm.get("chapters") or [None])[0],
                    "predicate": link.get("predicate"),
                    "target": link.get("target"),
                }
            )

    chains_path = DATA_DIR / "金瓶梅.imagery-chains.json"
    chains = []
    if chains_path.exists():
        chains = json.loads(chains_path.read_text(encoding="utf-8")).get("chains") or []

    return {
        "book": "金瓶梅",
        "slug": "jinpingmei",
        "generated_by": "build_shi_karma.py",
        "phases": PHASES,
        "by_phase": by_phase,
        "counts": {p: len(by_phase[p]) for p in PHASES},
        "chains": chains,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    payload = build_jpm()

    if args.write:
        out = DATA_DIR / "jinpingmei.shi-karma.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  jinpingmei karma: {sum(payload['counts'].values())} phase slots · {len(payload['chains'])} chains")
        for p in PHASES:
            print(f"    {p}: {payload['counts'][p]}")
        print(f"written → {out.name}")
    else:
        print(json.dumps(payload["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
