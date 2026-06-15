#!/usr/bin/env python3
"""合并 xyj_bestiary_fields.py 写入 xiyouji.bestiary.json。

用法: python scripts/build_xyj_bestiary_json.py
"""
from __future__ import annotations

import json
import sys

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter
from outcome_extract import extract_outcome
from xyj_bestiary_fields import FIELDS

BOOK = "西游记"
OUT = DATA_DIR / "xiyouji.bestiary.json"


def main() -> int:
    data = json.loads(OUT.read_text(encoding="utf-8"))
    char_dir = CHAR_DIR / BOOK
    missing_pages = [cid for cid in FIELDS if not (char_dir / f"{cid}.md").is_file()]
    if missing_pages:
        print(f"warn: FIELDS 无人物页: {', '.join(missing_pages)}")

    merged_fields: dict[str, dict] = {}
    for cid, base in FIELDS.items():
        entry = dict(base)
        if not entry.get("结局"):
            path = char_dir / f"{cid}.md"
            if path.is_file():
                fm, body = parse_frontmatter(path)
                if fm.get("结局"):
                    entry["结局"] = fm["结局"]
                else:
                    o = extract_outcome(fm, body)
                    if o:
                        entry["结局"] = o
        merged_fields[cid] = entry

    data["fields"] = merged_fields

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
    print(
        f"[{BOOK}] 写入 {OUT.name}: {len(merged_fields)} 人 · "
        f"{len(data.get('groups', {}))} 组 · {len(item_ids)} 名物 id"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
