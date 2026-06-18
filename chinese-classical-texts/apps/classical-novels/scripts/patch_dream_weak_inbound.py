#!/usr/bin/env python3
"""/dream — 弱入链 hub 回链（三书通用）。

用法:
  python scripts/patch_dream_weak_inbound.py 西游记 [--max-inbound 1] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import parse_frontmatter, resolve_books  # noqa: E402
from dream_patch_common import (  # noqa: E402
    add_hub_link,
    pick_hub_source,
    scan_pages,
    write_page,
)


def run(book: str, *, max_inbound: int, dry_run: bool, limit: int) -> list[str]:
    pages, inbound = scan_pages(book)
    chapter_cache: dict[int, str | None] = {}
    changes: list[str] = []

    targets = sorted(
        (cid for cid, info in pages.items() if info["inbound"] <= max_inbound),
        key=lambda c: (pages[c]["inbound"], -pages[c]["weight"], c),
    )
    if limit > 0:
        targets = targets[:limit]

    for cid in targets:
        hub = pick_hub_source(book, cid, pages, inbound, chapter_cache)
        if not hub:
            continue
        hub_path = pages[hub]["path"]
        hfm, hbody = parse_frontmatter(hub_path)
        new_body = add_hub_link(hbody, cid)
        if new_body == hbody:
            continue
        if not dry_run:
            hfm_text = yaml.dump(hfm, allow_unicode=True, default_flow_style=False, sort_keys=False)
            hub_path.write_text(f"---\n{hfm_text}---\n{new_body}", encoding="utf-8")
        inbound[cid].add(hub)
        pages[cid]["inbound"] = len(inbound[cid])
        changes.append(f"{hub}→{cid}: hub")

        # 薄页自身 ## 相关 也补 hub 指向（双向可读）
        info = pages[cid]
        own_body = add_hub_link(info["body"], hub)
        if own_body != info["body"]:
            write_page(info["path"], info["fm"], own_body, dry_run)
            changes.append(f"{cid}→{hub}: 相关")

    return changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", default=None)
    ap.add_argument("--max-inbound", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for book in resolve_books(args.book):
        changes = run(book, max_inbound=args.max_inbound, dry_run=args.dry_run, limit=args.limit)
        print(f"patched {len(changes)} items")
        for c in changes:
            print(" ", c)


if __name__ == "__main__":
    main()
