#!/usr/bin/env python3
"""合并 jpm_bestiary_fields.py 写入 jinpingmei.bestiary.json（保留 groups 与原 fields）。

用法: python scripts/build_jpm_bestiary_json.py
"""
from __future__ import annotations

import json
import sys

from _common import CHAR_DIR, DATA_DIR
from jpm_bestiary_fields import EXTRA

BOOK = "金瓶梅"
OUT = DATA_DIR / "jinpingmei.bestiary.json"


def main() -> int:
    data = json.loads(OUT.read_text(encoding="utf-8"))
    fields: dict[str, dict] = data.setdefault("fields", {})
    char_ids = sorted(p.stem for p in (CHAR_DIR / BOOK).glob("*.md"))

    for cid in char_ids:
        base = dict(fields.get(cid, {}))
        extra = EXTRA.get(cid, {})
        if extra:
            base.update(extra)
        fields[cid] = base

    missing = [cid for cid in char_ids if cid not in EXTRA]
    if missing:
        print(f"  warn: EXTRA 缺: {', '.join(missing)}")

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[{BOOK}] 写入 {OUT.name}: {len(char_ids)} 人 · groups {len(data.get('groups', {}))} 组")
    return 0


if __name__ == "__main__":
    sys.exit(main())
