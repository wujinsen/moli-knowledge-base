#!/usr/bin/env python3
"""从名物百科反向补全人物 frontmatter 的 服饰 / 关键物品（与 FIELDS 合并，不删已有）。

用法:
  python scripts/sync_character_items_from_wiki.py 红楼梦 [--dry-run]
  python scripts/sync_character_items_from_wiki.py --all [--dry-run]

建议流水线（红楼梦）:
  python scripts/build_hlm_bestiary_json.py
  python scripts/seed_hlm_bestiary.py
  python scripts/sync_character_items_from_wiki.py 红楼梦
  python scripts/build_crosslinks.py 红楼梦
"""
from __future__ import annotations

import argparse
import sys

import yaml

from _common import CHAR_DIR, parse_frontmatter, resolve_books
from _item_wiki import (
    build_char_item_map,
    list_known_item_ids,
    merge_fields_with_wiki,
)

BOOKS_WITH_ITEMS = ("红楼梦", "金瓶梅", "西游记")


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def sync_book(book: str, *, dry_run: bool) -> int:
    if book not in BOOKS_WITH_ITEMS:
        print(f"[{book}] skip: 无名物模块", file=sys.stderr)
        return 0

    wiki_map = build_char_item_map(book)
    item_ids = list_known_item_ids(book)
    char_dir = CHAR_DIR / book
    updated = 0

    for path in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        cid = fm.get("id", path.stem)
        wiki = wiki_map.get(cid, {})
        merged = merge_fields_with_wiki(
            {"服饰": fm.get("服饰"), "关键物品": fm.get("关键物品")},
            wiki,
            item_ids,
        )
        new_costumes = merged.get("服饰") or []
        new_keys = merged.get("关键物品") or []
        old_costumes = list(fm.get("服饰") or [])
        old_keys = list(fm.get("关键物品") or [])
        if new_costumes == old_costumes and new_keys == old_keys:
            continue
        if new_costumes:
            fm["服饰"] = new_costumes
        else:
            fm.pop("服饰", None)
        if new_keys:
            fm["关键物品"] = new_keys
        else:
            fm.pop("关键物品", None)
        updated += 1
        print(
            f"  {cid}: 服饰 {len(old_costumes)}→{len(new_costumes)}"
            f" · 关键物品 {len(old_keys)}→{len(new_keys)}"
        )
        if not dry_run:
            write_frontmatter(path, fm, body)

    print(f"[{book}] {'(dry-run) ' if dry_run else ''}更新 {updated} 人 · wiki 映射 {len(wiki_map)} 人")
    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description="名物百科 → 人物 服饰/关键物品 反向同步")
    ap.add_argument("book", nargs="?", help="红楼梦 | 金瓶梅 | 西游记")
    ap.add_argument("--all", action="store_true", help="三书皆跑")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.all:
        books = list(BOOKS_WITH_ITEMS)
    elif args.book:
        books = resolve_books(args.book)
    else:
        ap.error("请指定书名或 --all")

    total = 0
    for book in books:
        total += sync_book(book, dry_run=args.dry_run)
    if total and not args.dry_run:
        print("提示: 运行 build_crosslinks.py 刷新 occupant_items")


if __name__ == "__main__":
    main()
