#!/usr/bin/env python3
"""B3 guard: 互文链路 path 节点须在图数据中存在。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "src" / "content" / "imagery"

SLUG_BOOK = {
    "honglou": "红楼梦",
    "jinpingmei": "金瓶梅",
    "xiyouji": "西游记",
}


def is_imagery_id(s: str) -> bool:
    return s.startswith(("hl-", "jpm-", "xyj-"))


def collect_node_ids(book: str) -> set[str]:
    ids: set[str] = set()
    d = IMG / book
    for p in d.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != book:
            continue
        ids.add(fm["id"])
        for c in fm.get("characters") or []:
            ids.add(c)
        for link in fm.get("links") or []:
            tgt = link.get("target", "")
            if tgt and not is_imagery_id(tgt):
                ids.add(tgt)
    links_path = DATA_DIR / f"{book}.imagery-links.json"
    if links_path.exists():
        for link in json.loads(links_path.read_text(encoding="utf-8")).get("links", []):
            ids.add(link["source"])
            ids.add(link["target"])
    return ids


def main() -> None:
    errors: list[str] = []
    for slug, book in SLUG_BOOK.items():
        chain_file = DATA_DIR / f"{book}.imagery-chains.json"
        if not chain_file.exists():
            errors.append(f"missing {chain_file.name}")
            continue
        nodes = collect_node_ids(book)
        data = json.loads(chain_file.read_text(encoding="utf-8"))
        for chain in data.get("chains", []):
            for nid in chain.get("path", []):
                if nid not in nodes:
                    errors.append(f"{slug}/{chain['id']}: unknown node {nid!r}")
    if errors:
        for e in errors:
            print(e)
        raise SystemExit(1)
    print(f"B3 guard OK ({sum(len(json.loads((DATA_DIR / f'{b}.imagery-chains.json').read_text(encoding='utf-8')).get('chains', [])) for b in SLUG_BOOK.values())} chains)")


if __name__ == "__main__":
    main()
