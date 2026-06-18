#!/usr/bin/env python3
"""回目 items[] 对齐：合并 frontmatter 已有项 + 正文扫描已知名物 id。

用法:
  python scripts/align_chapter_items.py 红楼梦
  python scripts/align_chapter_items.py 西游记
  python scripts/align_chapter_items.py --all [--dry-run]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CHAPTER_DIR
from lint_modules import list_known_item_ids
from tag_chapter_meta import (
    find_ids,
    format_list,
    load_item_pairs,
    load_location_pairs,
    parse_list_field,
    split_body,
    strip_html,
)


def iter_chapter_files(book: str) -> list[Path]:
    base = CHAPTER_DIR / book
    if not base.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(base.rglob("*.md")):
        if re.search(r"\d+\.md$", p.name):
            out.append(p)
    return out


def write_items(raw: str, merged: list[str]) -> str:
    new_fm = format_list("items", merged)
    if re.search(r"^items:\s*\[", raw, re.M):
        return re.sub(r"^items:\s*\[[^\]]*\]", new_fm.strip(), raw, count=1, flags=re.M)
    if re.search(r"^items:\s*\n", raw, re.M):
        return re.sub(
            r"^items:\s*\n(?:[ \t]*-[ \t].+\n?)+",
            new_fm + "\n",
            raw,
            count=1,
            flags=re.M,
        )
    if re.search(r"^summary:", raw, re.M):
        return re.sub(r"(^summary:.*\n)", rf"\1{new_fm}\n", raw, count=1, flags=re.M)
    return re.sub(r"(^---\s*\n(?:.*?\n)*?)(?=---\n)", rf"\1{new_fm}\n", raw, count=1, flags=re.M)


def location_skip(book: str) -> set[str]:
    from tag_chapter_meta import load_location_ids

    skip = load_location_ids(book)
    for alias, lid in load_location_pairs(book):
        if alias:
            skip.add(alias)
        if lid:
            skip.add(lid)
    return skip


def align_book(book: str, *, dry_run: bool) -> int:
    pairs = load_item_pairs(book)
    known = list_known_item_ids(book)
    loc_skip = location_skip(book)
    changed = 0
    for p in iter_chapter_files(book):
        raw = p.read_text(encoding="utf-8-sig")
        cur = set(parse_list_field(raw, "items") or [])
        body = strip_html(split_body(raw))
        found = (set(find_ids(body, pairs, {})) & known) - loc_skip
        merged = sorted(cur | found)
        if merged == sorted(cur):
            continue
        changed += 1
        rel = p.relative_to(CHAPTER_DIR)
        print(f"  {rel}: +{len(merged) - len(cur)} → {len(merged)} 项")
        if not dry_run:
            p.write_text(write_items(raw, merged), encoding="utf-8")
    mode = "dry-run" if dry_run else "written"
    print(f"[{book}] items[] 对齐 {mode}: {changed} 回")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Align chapter items[] from body scan")
    parser.add_argument("book", nargs="?", help="书名")
    parser.add_argument("--all", action="store_true", help="红楼梦 + 西游记")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.all:
        books = ["红楼梦", "西游记"]
    elif args.book:
        books = [args.book]
    else:
        parser.error("请指定书名或 --all")

    total = 0
    for book in books:
        total += align_book(book, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
