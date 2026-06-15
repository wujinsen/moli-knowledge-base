#!/usr/bin/env python3
"""合并 xyj_bestiary_fields.py 写入 xiyouji.bestiary.json。

用法: python scripts/build_xyj_bestiary_json.py
"""
from __future__ import annotations

import json
import sys

from _common import CHAR_DIR, DATA_DIR
from xyj_bestiary_fields import FIELDS

BOOK = "西游记"
OUT = DATA_DIR / "xiyouji.bestiary.json"


def main() -> int:
    data = json.loads(OUT.read_text(encoding="utf-8"))
    char_ids = sorted(p.stem for p in (CHAR_DIR / BOOK).glob("*.md"))
    missing = [cid for cid in char_ids if cid not in FIELDS]
    extra = [cid for cid in FIELDS if cid not in char_ids]
    if missing:
        print(f"error: FIELDS 缺 {len(missing)} 人: {', '.join(missing)}", file=sys.stderr)
        return 1
    if extra:
        print(f"warn: FIELDS 多: {', '.join(extra)}")

    data["fields"] = {cid: FIELDS[cid] for cid in char_ids}

    item_ids: set[str] = set()
    content = DATA_DIR.parent / "content"
    for sub in ("artifacts",):
        d = content / sub / BOOK
        if d.is_dir():
            item_ids |= {p.stem for p in d.glob("*.md")}
    for vals in FIELDS.values():
        for like in vals.get("喜好", []):
            item_ids.add(like)
    ids_out = DATA_DIR / "xiyouji.item_ids.json"
    ids_out.write_text(
        json.dumps(sorted(item_ids), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[{BOOK}] 写入 {OUT.name}: {len(char_ids)} 人 · {len(data.get('groups', {}))} 组 · {len(item_ids)} 名物 id")
    return 0


if __name__ == "__main__":
    sys.exit(main())
