#!/usr/bin/env python3
"""Merge location entity appear_in into chapter frontmatter locations[].

Usage: python scripts/sync_chapter_locations.py 红楼梦 [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _common import CHAPTER_DIR, CONTENT, parse_frontmatter
from tag_chapter_meta import format_list, load_location_ids, parse_list_field

CHAPTER_RE = re.compile(r"第(\d+)回")


def chapter_path(book: str, num: int) -> Path | None:
    base = CHAPTER_DIR / book
    for fmt in (f"{num:03d}.md", f"{num}.md"):
        p = base / fmt
        if p.exists():
            return p
    return None


def sync_book(book: str, *, dry_run: bool) -> int:
    loc_dir = CONTENT / "locations" / book
    if not loc_dir.exists():
        print(f"no locations dir for {book}", file=sys.stderr)
        return 0

    valid = load_location_ids(book)
    by_chapter: dict[int, set[str]] = {}

    for p in loc_dir.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        lid = fm.get("id") or p.stem
        if lid not in valid:
            continue
        for ref in fm.get("appear_in") or []:
            m = CHAPTER_RE.search(str(ref))
            if not m:
                continue
            by_chapter.setdefault(int(m.group(1)), set()).add(lid)

    updated = 0
    for num, lids in sorted(by_chapter.items()):
        path = chapter_path(book, num)
        if not path:
            continue
        raw = path.read_text(encoding="utf-8-sig")
        if not raw.startswith("---"):
            continue
        parts = raw.split("---", 2)
        if len(parts) < 3:
            continue
        fm, body = parts[1], parts[2]
        current = parse_list_field(raw, "locations") or []
        merged = sorted(set(current) | lids)
        if set(merged) == set(current):
            continue
        new_fm = re.sub(
            r"^locations:\s*\[.*?\]",
            format_list("locations", merged),
            fm,
            count=1,
            flags=re.M,
        )
        if new_fm == fm:
            new_fm = fm.rstrip() + "\n" + format_list("locations", merged) + "\n"
        new_raw = f"---{new_fm}---{body}"
        if not dry_run:
            path.write_text(new_raw, encoding="utf-8")
        added = sorted(set(merged) - set(current))
        print(f"  {path.name}: +{added}")
        updated += 1

    return updated


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", default="红楼梦")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    n = sync_book(args.book, dry_run=args.dry_run)
    print(f"{'would update' if args.dry_run else 'updated'} {n} chapters")


if __name__ == "__main__":
    main()
