#!/usr/bin/env python3
"""/dream — 低密度页补 relation + hub（三书通用）。

用法:
  python scripts/patch_dream_low_score.py 金瓶梅 --thin-max 16 [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import parse_frontmatter, resolve_books  # noqa: E402
from dream_patch_common import (  # noqa: E402
    add_hub_link,
    add_relations,
    page_score,
    pick_hub_source,
    pick_relation,
    scan_pages,
    write_page,
)


def patch_rel_backlinks(
    cid: str,
    info: dict,
    pages: dict[str, dict],
    inbound: dict[str, set[str]],
    *,
    dry_run: bool,
    changes: list[str],
) -> None:
    """已有 relation 目标页补 ## 相关 hub（无需共现检索）。"""
    for rel in info["fm"].get("relations") or []:
        tid = rel.get("target")
        if not tid or tid not in pages or tid == cid:
            continue
        hub_path = pages[tid]["path"]
        hfm, hbody = parse_frontmatter(hub_path)
        new_body = add_hub_link(hbody, cid)
        if new_body == hbody:
            continue
        if not dry_run:
            write_page(hub_path, hfm, new_body, False)
        inbound[cid].add(tid)
        info["inbound"] = len(inbound[cid])
        changes.append(f"{tid}→{cid}: rel-hub")


def run(book: str, *, thin_max: int, dry_run: bool, limit: int) -> list[str]:
    pages, inbound = scan_pages(book)
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}
    changes: list[str] = []

    targets = sorted(
        (cid for cid, info in pages.items() if page_score(info) <= thin_max),
        key=lambda c: (page_score(pages[c]), pages[c]["inbound"], c),
    )
    if limit > 0:
        targets = targets[:limit]

    for cid in targets:
        info = pages[cid]
        if info["inbound"] <= 5:
            hub = pick_hub_source(book, cid, pages, inbound, chapter_cache)
            if hub:
                hub_path = pages[hub]["path"]
                hfm, hbody = parse_frontmatter(hub_path)
                new_body = add_hub_link(hbody, cid)
                if new_body != hbody:
                    if not dry_run:
                        write_page(hub_path, hfm, new_body, False)
                    inbound[cid].add(hub)
                    info["inbound"] = len(inbound[cid])
                    changes.append(f"{hub}→{cid}: hub")

        if info["rel"] <= 8:
            rel = pick_relation(book, cid, pages, all_fms, chapter_cache)
            if rel:
                fm = dict(info["fm"])
                if add_relations(fm, rel):
                    write_page(info["path"], fm, info["body"], dry_run)
                    info["fm"] = fm
                    info["rel"] = len(fm.get("relations") or [])
                    all_fms[cid] = (info["path"], fm, info["body"])
                    changes.append(f"{cid}: +rel→{rel['target']}")

        if page_score(info) <= thin_max:
            patch_rel_backlinks(cid, info, pages, inbound, dry_run=dry_run, changes=changes)

    return changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", default=None)
    ap.add_argument("--thin-max", type=int, default=16)
    ap.add_argument("--limit", type=int, default=80)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for book in resolve_books(args.book):
        changes = run(book, thin_max=args.thin_max, dry_run=args.dry_run, limit=args.limit)
        print(f"patched {len(changes)} items")
        for c in changes:
            print(" ", c)
        remaining = sum(1 for _, info in scan_pages(book)[0].items() if page_score(info) <= args.thin_max)
        print(f"remaining score<={args.thin_max}: {remaining}")


if __name__ == "__main__":
    main()
