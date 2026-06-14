#!/usr/bin/env python3
"""Remove location ids duplicated in chapter items[] (frontmatter only).

Keeps customs/dishes/medicines; drops ids that are location entities or already
in the same chapter's locations[].

Usage:
  python scripts/clean_chapter_items.py 红楼梦
  python scripts/clean_chapter_items.py 红楼梦 --dry-run
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CHAPTER_DIR, parse_frontmatter
from tag_chapter_meta import load_location_ids, load_location_pairs, parse_list_field

# Not in locations collection but treated as place names in items[].
EXTRA_LOCATION_IDS = {
    "赖大家",
    "贾母套间",
}


def parse_list(raw: str, field: str) -> list[str]:
    val = parse_list_field(raw, field)
    return val if val is not None else []


def location_id_set(book: str) -> set[str]:
    ids = load_location_ids(book)
    ids.update(EXTRA_LOCATION_IDS)
    for alias, lid in load_location_pairs(book):
        ids.add(lid)
        if len(alias) >= 2:
            ids.add(alias)
    return ids


def clean_file(path: Path, loc_ids: set[str], *, dry_run: bool) -> tuple[bool, list[str], list[str]]:
    raw = path.read_text(encoding="utf-8-sig")
    fm, body = parse_frontmatter(path)
    if fm.get("type") != "chapter":
        return False, [], []

    locations = parse_list(raw, "locations")
    items = parse_list(raw, "items")
    if not items:
        return False, [], []

    drop_set = loc_ids | set(locations)
    cleaned = [i for i in items if i not in drop_set]
    if cleaned == items:
        return False, items, cleaned

    new_line = "items: [" + ", ".join(cleaned) + "]"
    new_raw = re.sub(r"^items:\s*\[.*\]\s*$", new_line, raw, count=1, flags=re.M)
    if not dry_run:
        path.write_text(new_raw, encoding="utf-8")
    return True, items, cleaned


def main() -> None:
    ap = argparse.ArgumentParser(description="Strip location ids from chapter items[]")
    ap.add_argument("book")
    ap.add_argument("--subdir", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = CHAPTER_DIR / args.book
    if args.subdir:
        base = base / args.subdir
    loc_ids = location_id_set(args.book)
    changed = 0
    for path in sorted(base.rglob("*.md")):
        ok, before, after = clean_file(path, loc_ids, dry_run=args.dry_run)
        if ok:
            changed += 1
            rel = path.relative_to(CHAPTER_DIR)
            print(f"[{'dry' if args.dry_run else 'ok'}] {rel}")
            print(f"  - {before}")
            print(f"  + {after}")
    print(f"{'Would update' if args.dry_run else 'Updated'} {changed} files")


if __name__ == "__main__":
    main()
