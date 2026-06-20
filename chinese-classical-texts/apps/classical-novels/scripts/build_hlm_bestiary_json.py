#!/usr/bin/env python3
"""合并 hlm_bestiary_fields.py 写入 hongloumeng.bestiary.json，校验 132 人全覆盖。

用法: python scripts/build_hlm_bestiary_json.py
"""
from __future__ import annotations

import json
import sys

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter
from hlm_bestiary_fields import FIELDS, GROUPS
from outcome_extract import extract_outcome
from _item_wiki import build_char_item_map, build_chip_item_ids, list_item_catalog, list_known_item_ids, merge_fields_with_wiki, filter_hlm_keepsake_ids, filter_hlm_like_ids

BOOK = "红楼梦"
OUT = DATA_DIR / "hongloumeng.bestiary.json"


def main() -> None:
    char_ids = sorted(p.stem for p in (CHAR_DIR / BOOK).glob("*.md"))
    missing = [cid for cid in char_ids if cid not in FIELDS]
    extra = [cid for cid in FIELDS if cid not in char_ids]
    if missing:
        print(f"error: FIELDS 缺 {len(missing)} 人: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    if extra:
        print(f"warn: FIELDS 多 {len(extra)} 人: {', '.join(extra)}")

    payload_fields: dict[str, dict] = {}
    char_dir = CHAR_DIR / BOOK
    wiki_map = build_char_item_map(BOOK)
    item_ids = list_known_item_ids(BOOK)
    catalog = list_item_catalog(BOOK)
    char_ids_set = set(char_ids)
    for cid in char_ids:
        base = dict(FIELDS[cid])
        if base.get("关键物品"):
            base["关键物品"] = filter_hlm_keepsake_ids(
                base["关键物品"], catalog, char_ids_set, book=BOOK
            )
        path = char_dir / f"{cid}.md"
        fm, body = ({}, "")
        if path.is_file():
            fm, body = parse_frontmatter(path)
        rel = fm.get("relations") or []
        if base.get("喜好"):
            base["喜好"] = filter_hlm_like_ids(
                base["喜好"], catalog, char_ids_set, relations=rel
            )
        entry = merge_fields_with_wiki(
            base, wiki_map.get(cid), item_ids, book=BOOK, catalog=catalog
        )
        if path.is_file():
            o = extract_outcome(fm, body)
            if o:
                entry["结局"] = o
        payload_fields[cid] = entry

    payload = {"book": BOOK, "groups": GROUPS, "fields": payload_fields}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    item_ids = build_chip_item_ids(BOOK, catalog, set(char_ids))
    ids_out = DATA_DIR / "hongloumeng.item_ids.json"
    ids_out.write_text(
        json.dumps(sorted(item_ids), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[{BOOK}] 写入 {OUT.name}: {len(char_ids)} 人 · {len(GROUPS)} 组 · {len(item_ids)} 名物 id")


if __name__ == "__main__":
    main()
