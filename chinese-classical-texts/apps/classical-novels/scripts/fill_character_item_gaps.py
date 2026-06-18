#!/usr/bin/env python3
"""补全人物名物链：共现回目 items[] · 喜好/图鉴 · crosslinks drift。

用法:
  python scripts/fill_character_item_gaps.py 红楼梦 [--dry-run]
  python scripts/fill_character_item_gaps.py --all
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict

import yaml

from _common import CHAPTER_DIR, CHAR_DIR, DATA_DIR, parse_frontmatter
from _item_wiki import (
    build_char_item_map,
    item_target_field,
    list_item_catalog,
    list_known_item_ids,
    merge_fields_with_wiki,
    merge_item_lists,
)
from lint_modules import CHARACTER_ITEM_IMPORTANT_STATUS, CHARACTER_ITEM_WEIGHT_MIN, _char_item_ids
from tag_chapter_meta import parse_list_field

try:
    from xyj_bestiary_fields import FIELDS as XYJ_FIELDS
except ImportError:
    XYJ_FIELDS = {}

CROSSLINKS_SLUG = {"红楼梦": "hongloumeng", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}


def load_occupant(book: str) -> dict[str, list[str]]:
    slug = CROSSLINKS_SLUG.get(book, book)
    p = DATA_DIR / f"{slug}.crosslinks.json"
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8-sig")).get("occupant_items") or {}


def coappear_items(book: str) -> dict[str, Counter]:
    """人物 id → 同回 items[] 共现计数。"""
    counts: dict[str, Counter] = defaultdict(Counter)
    base = CHAPTER_DIR / book
    if not base.is_dir():
        return counts
    for p in base.rglob("*.md"):
        raw = p.read_text(encoding="utf-8-sig")
        chars = parse_list_field(raw, "characters") or []
        items = parse_list_field(raw, "items") or []
        if not chars or not items:
            continue
        for cid in chars:
            for iid in items:
                counts[cid][iid] += 1
    return counts


def gap_characters(book: str) -> list[tuple[str, dict, str]]:
    min_w = CHARACTER_ITEM_WEIGHT_MIN.get(book, 40)
    occupant = load_occupant(book)
    out: list[tuple[str, dict, str]] = []
    char_dir = CHAR_DIR / book
    for path in sorted(char_dir.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        cid = fm.get("id") or path.stem
        if _char_item_ids(fm):
            continue
        if occupant.get(cid):
            continue
        weight = int(fm.get("weight") or 0)
        status = fm.get("status") or ""
        if status not in CHARACTER_ITEM_IMPORTANT_STATUS and weight < min_w:
            continue
        out.append((cid, fm, str(path)))
    return out


def pick_items(
    book: str,
    cid: str,
    fm: dict,
    *,
    coappear: dict[str, Counter],
    wiki_map: dict,
    catalog: dict[str, dict],
    item_ids: set[str],
) -> tuple[list[str], list[str], list[str]]:
    costumes: list[str] = []
    keys: list[str] = []
    fabao: list[str] = []

    merged = merge_fields_with_wiki(
        {"服饰": fm.get("服饰"), "关键物品": fm.get("关键物品")},
        wiki_map.get(cid),
        item_ids,
    )
    keys = list(merged.get("关键物品") or [])
    costumes = list(merged.get("服饰") or [])

    likes = list(fm.get("喜好") or [])
    if cid in XYJ_FIELDS:
        likes = merge_item_lists(likes, XYJ_FIELDS[cid].get("喜好"))
    promo = [x for x in likes if isinstance(x, str) and x in item_ids]
    if promo:
        keys = merge_item_lists(keys, promo)

    if not keys and not costumes and not fabao:
        top = coappear.get(cid)
        if top:
            iid, _ = top.most_common(1)[0]
            field = item_target_field(catalog.get(iid, {"kind": "artifacts"}))
            if fm.get("type") == "monster" and field == "关键物品":
                fabao = [iid]
            elif field == "服饰":
                costumes = [iid]
            else:
                keys = [iid]

    return costumes, keys, fabao


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def fill_book(book: str, *, dry_run: bool) -> int:
    gaps = gap_characters(book)
    if not gaps:
        print(f"[{book}] 无待补人物名物链")
        return 0

    coappear = coappear_items(book)
    wiki_map = build_char_item_map(book)
    catalog = list_item_catalog(book)
    item_ids = list_known_item_ids(book)
    updated = 0

    for cid, fm, path_str in gaps:
        path = CHAR_DIR / book / f"{cid}.md"
        _, body = parse_frontmatter(path)
        costumes, keys, fabao = pick_items(
            book, cid, fm,
            coappear=coappear,
            wiki_map=wiki_map,
            catalog=catalog,
            item_ids=item_ids,
        )
        if not costumes and not keys and not fabao:
            continue

        if costumes:
            fm["服饰"] = costumes
        if keys:
            fm["关键物品"] = keys
        if fabao:
            fm["法宝"] = fabao
        updated += 1
        print(f"  {cid}: 服饰{len(costumes)} 关键{len(keys)} 法宝{len(fabao)}")
        if not dry_run:
            write_frontmatter(path, fm, body)

    print(f"[{book}] {'(dry-run) ' if dry_run else ''}补全 {updated}/{len(gaps)} 人")
    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description="Fill character item gaps from co-appear & likes")
    ap.add_argument("book", nargs="?", help="书名")
    ap.add_argument("--all", action="store_true", help="红楼梦 + 西游记")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    books = ["红楼梦", "西游记"] if args.all else ([args.book] if args.book else [])
    if not books:
        ap.error("请指定书名或 --all")

    total = 0
    for book in books:
        total += fill_book(book, dry_run=args.dry_run)
    if total and not args.dry_run:
        print("提示: 运行 build_crosslinks.py 刷新 occupant_items")


if __name__ == "__main__":
    main()
