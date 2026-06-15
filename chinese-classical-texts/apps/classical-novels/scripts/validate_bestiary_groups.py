#!/usr/bin/env python3
"""校验三书 bestiary.json 的 groups 是否覆盖全部人物/妖怪 id。

用法: python scripts/validate_bestiary_groups.py
"""
from __future__ import annotations

import json
import sys

from _common import CHAR_DIR, DATA_DIR

BOOKS = {
    "红楼梦": ("hongloumeng.bestiary.json", "honglou"),
    "金瓶梅": ("jinpingmei.bestiary.json", "jinpingmei"),
    "西游记": ("xiyouji.bestiary.json", "xiyouji"),
}


def main() -> int:
    errors = 0
    for book, (fname, _slug) in BOOKS.items():
        path = DATA_DIR / fname
        if not path.is_file():
            print(f"  skip {book}: 无 {fname}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        groups: dict[str, list[str]] = data.get("groups") or {}
        if not groups:
            print(f"  warn {book}: 无 groups（将回退 faction 分组）")
            continue
        char_ids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
        listed = {cid for ids in groups.values() for cid in ids}
        missing = sorted(char_ids - listed)
        unknown = sorted(listed - char_ids)
        dupes: list[str] = []
        seen: set[str] = set()
        for label, ids in groups.items():
            for cid in ids:
                if cid in seen:
                    dupes.append(f"{label}/{cid}")
                seen.add(cid)
        print(f"[{book}] groups {len(groups)} 组 · 列出 {len(listed)}/{len(char_ids)} 人")
        if missing:
            print(f"  error 未分组: {', '.join(missing)}")
            errors += 1
        if unknown:
            print(f"  error 无实体页: {', '.join(unknown)}")
            errors += 1
        if dupes:
            print(f"  error 重复: {', '.join(dupes)}")
            errors += 1
    if errors:
        print(f"\n{errors} 项错误")
        return 1
    print("\n校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
