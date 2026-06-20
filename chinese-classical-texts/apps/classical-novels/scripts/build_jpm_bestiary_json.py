#!/usr/bin/env python3
"""合并 jpm_bestiary_fields.py 写入 jinpingmei.bestiary.json（保留 groups 与原 fields）。

用法: python scripts/build_jpm_bestiary_json.py
"""
from __future__ import annotations

import json
import sys

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter
from _item_wiki import (
    build_chip_item_ids,
    filter_jpm_costume_ids,
    filter_jpm_keepsake_ids,
    filter_jpm_like_ids,
    list_item_catalog,
    merge_item_lists,
)
from jpm_bestiary_fields import EXTRA

BOOK = "金瓶梅"
OUT = DATA_DIR / "jinpingmei.bestiary.json"


def main() -> int:
    data = json.loads(OUT.read_text(encoding="utf-8"))
    fields: dict[str, dict] = data.setdefault("fields", {})
    char_dir = CHAR_DIR / BOOK
    char_ids = sorted(p.stem for p in char_dir.glob("*.md"))
    char_ids_set = set(char_ids)
    catalog = list_item_catalog(BOOK)

    for cid in char_ids:
        base = dict(fields.get(cid, {}))
        extra = dict(EXTRA.get(cid, {}))
        if extra:
            base.update(extra)
        path = char_dir / f"{cid}.md"
        fm: dict = {}
        rel: list = []
        if path.is_file():
            fm, _ = parse_frontmatter(path)
            rel = fm.get("relations") or []
        for key in ("喜好", "服饰", "关键物品"):
            fm_vals = fm.get(key)
            if fm_vals:
                base[key] = merge_item_lists(base.get(key), list(fm_vals))
        if base.get("喜好"):
            filtered = filter_jpm_like_ids(
                base["喜好"], catalog, char_ids_set, relations=rel
            )
            if filtered:
                base["喜好"] = filtered
            else:
                base.pop("喜好", None)
        if base.get("关键物品"):
            filtered_keys = filter_jpm_keepsake_ids(
                base["关键物品"], catalog, char_ids_set, book=BOOK
            )
            if filtered_keys:
                base["关键物品"] = filtered_keys
            else:
                base.pop("关键物品", None)
        if base.get("服饰"):
            filtered_c = filter_jpm_costume_ids(base["服饰"], catalog, cid)
            if filtered_c:
                base["服饰"] = filtered_c
            else:
                base.pop("服饰", None)
        fields[cid] = base

    missing = [cid for cid in char_ids if cid not in EXTRA]
    if missing:
        print(f"  warn: EXTRA 缺: {', '.join(missing[:8])}{'…' if len(missing) > 8 else ''}")

    data["fields"] = fields
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    chip_extra: set[str] = set()
    for vals in fields.values():
        for key in ("关键物品", "服饰"):
            for x in vals.get(key) or []:
                chip_extra.add(x)
    item_ids = build_chip_item_ids(BOOK, catalog, char_ids_set, extra_ids=chip_extra)
    ids_out = DATA_DIR / "jinpingmei.item_ids.json"
    ids_out.write_text(
        json.dumps(sorted(item_ids), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"[{BOOK}] 写入 {OUT.name}: {len(char_ids)} 人 · "
        f"groups {len(data.get('groups', {}))} 组 · {len(item_ids)} 名物 id"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
