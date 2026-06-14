#!/usr/bin/env python3
"""Add reciprocal nearby[] entries on location pages (YAML only).

Usage: python scripts/reciprocate_location_nearby.py 红楼梦 [--dry-run]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CONTENT, parse_frontmatter
from tag_chapter_meta import load_location_ids

NEARBY_RE = re.compile(r"^(nearby:\s*\[)(.*?)(\])", re.M | re.S)
TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+")


def load_nearby(book: str) -> dict[str, list[str]]:
    loc_dir = CONTENT / "locations" / book
    valid = load_location_ids(book)
    out: dict[str, list[str]] = {}
    for p in loc_dir.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        lid = fm.get("id") or p.stem
        items: list[str] = []
        for n in fm.get("nearby") or []:
            if isinstance(n, str) and n in valid and n != lid:
                items.append(n)
        out[lid] = items
    return out


def set_nearby(raw: str, items: list[str]) -> str:
    body = format_nearby = format_list_yaml("nearby", items)
    if NEARBY_RE.search(raw):
        return NEARBY_RE.sub(format_nearby, raw, count=1)
    # insert before first_appear or summary
    for anchor in ("first_appear:", "summary:", "tags:", "---"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + format_nearby + "\n" + raw[idx:]
    return raw + "\n" + format_nearby + "\n"


def format_list_yaml(field: str, items: list[str]) -> str:
    if not items:
        return f"{field}: []"
    return f"{field}: [{', '.join(items)}]"


def reciprocate(book: str, *, dry_run: bool) -> int:
    loc_dir = CONTENT / "locations" / book
    nearby = load_nearby(book)
    changed = 0

    need: dict[str, set[str]] = {k: set(v) for k, v in nearby.items()}
    for src, targets in nearby.items():
        for tgt in targets:
            if src not in need.get(tgt, set()):
                need.setdefault(tgt, set()).add(src)

    for p in sorted(loc_dir.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        lid = fm.get("id") or p.stem
        new_list = sorted(need.get(lid, set()) or set(nearby.get(lid, [])))
        old_list = nearby.get(lid, [])
        if new_list == old_list:
            continue
        raw = p.read_text(encoding="utf-8")
        parts = raw.split("---", 2)
        if len(parts) < 3:
            continue
        new_fm = set_nearby(parts[1], new_list)
        if new_fm == parts[1]:
            continue
        if not dry_run:
            p.write_text(f"---{new_fm}---{parts[2]}", encoding="utf-8")
        added = sorted(set(new_list) - set(old_list))
        print(f"  {lid}: +{added}")
        changed += 1

    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", default="红楼梦")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    n = reciprocate(args.book, dry_run=args.dry_run)
    print(f"{'would update' if args.dry_run else 'updated'} {n} location pages")


if __name__ == "__main__":
    main()
