#!/usr/bin/env python3
"""crosslinks occupant_items → 人物 frontmatter 服饰/关键物品（补 drift 缺口）。

用法:
  python scripts/sync_character_items_from_crosslinks.py 红楼梦 [--dry-run]
  python scripts/sync_character_items_from_crosslinks.py --all
"""
from __future__ import annotations

import argparse
import json
import sys

import yaml

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter, resolve_books
from _item_wiki import item_target_field, list_item_catalog, merge_item_lists

CROSSLINKS_SLUG = {"红楼梦": "hongloumeng", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}
BOOKS = ("红楼梦", "金瓶梅", "西游记")


def load_occupant(book: str) -> dict[str, list[str]]:
    slug = CROSSLINKS_SLUG.get(book, book)
    p = DATA_DIR / f"{slug}.crosslinks.json"
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    return data.get("occupant_items") or {}


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def sync_book(book: str, *, dry_run: bool) -> int:
    occupant = load_occupant(book)
    catalog = list_item_catalog(book)
    char_dir = CHAR_DIR / book
    updated = 0

    for path in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        cid = fm.get("id") or path.stem
        occ = occupant.get(cid) or []
        if not occ:
            continue

        costumes: list[str] = list(fm.get("服饰") or [])
        keys: list[str] = list(fm.get("关键物品") or [])
        fabao: list[str] = list(fm.get("法宝") or [])

        for iid in occ:
            meta = catalog.get(iid, {})
            field = item_target_field(meta)
            if fm.get("type") == "monster" and field == "关键物品":
                fabao = merge_item_lists(fabao, [iid])
            elif field == "服饰":
                costumes = merge_item_lists(costumes, [iid])
            else:
                keys = merge_item_lists(keys, [iid])

        changed = False
        if costumes and costumes != list(fm.get("服饰") or []):
            fm["服饰"] = costumes
            changed = True
        if keys and keys != list(fm.get("关键物品") or []):
            fm["关键物品"] = keys
            changed = True
        elif not keys and fm.get("关键物品"):
            fm.pop("关键物品", None)
            changed = True
        if fabao and fabao != list(fm.get("法宝") or []):
            fm["法宝"] = fabao
            changed = True

        if not changed:
            continue
        updated += 1
        print(f"  {cid}: occ {len(occ)} → 服饰{len(costumes)} 关键{len(keys)} 法宝{len(fabao)}")
        if not dry_run:
            write_frontmatter(path, fm, body)

    print(f"[{book}] {'(dry-run) ' if dry_run else ''}crosslinks→frontmatter {updated} 人")
    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description="Sync occupant_items into character frontmatter")
    ap.add_argument("book", nargs="?", help="书名")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.all:
        books = list(BOOKS)
    elif args.book:
        books = resolve_books(args.book)
    else:
        ap.error("请指定书名或 --all")

    total = 0
    for book in books:
        total += sync_book(book, dry_run=args.dry_run)
    if total and not args.dry_run:
        print("提示: 运行 build_crosslinks.py 刷新 JSON", file=sys.stderr)


if __name__ == "__main__":
    main()
