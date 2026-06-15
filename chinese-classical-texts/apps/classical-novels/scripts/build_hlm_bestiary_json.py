#!/usr/bin/env python3
"""合并 hlm_bestiary_fields.py 写入 hongloumeng.bestiary.json，校验 132 人全覆盖。

用法: python scripts/build_hlm_bestiary_json.py
"""
from __future__ import annotations

import json
import sys

from _common import CHAR_DIR, DATA_DIR
from hlm_bestiary_fields import FIELDS, GROUPS

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

    payload = {"book": BOOK, "groups": GROUPS, "fields": {cid: FIELDS[cid] for cid in char_ids}}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    item_ids: set[str] = set()
    content = DATA_DIR.parent / "content"
    for sub in ("dishes", "medicines", "costumes", "customs"):
        d = content / sub / BOOK
        if d.is_dir():
            item_ids |= {p.stem for p in d.glob("*.md")}
    cross_path = DATA_DIR / "hongloumeng.crosslinks.json"
    if cross_path.is_file():
        cross = json.loads(cross_path.read_text(encoding="utf-8"))
        for bucket in cross.values():
            if isinstance(bucket, dict):
                for vals in bucket.values():
                    item_ids |= set(vals)
    ids_out = DATA_DIR / "hongloumeng.item_ids.json"
    ids_out.write_text(
        json.dumps(sorted(item_ids), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[{BOOK}] 写入 {OUT.name}: {len(char_ids)} 人 · {len(GROUPS)} 组 · {len(item_ids)} 名物 id")


if __name__ == "__main__":
    main()
