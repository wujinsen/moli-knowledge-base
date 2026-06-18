#!/usr/bin/env python3
"""补全新建金瓶梅地点：回目 locations[] · 名录互链 · parent 修正。"""
from __future__ import annotations

import re
from pathlib import Path

from _common import CHAPTER_DIR, CONTENT

BOOK = "金瓶梅"
EDITIONS = ("崇祯本", "词话本", "张竹坡评本")
CH_LOC = {
    27: ["卧云亭"],
    52: ["卧云亭"],
    96: ["卧云亭"],
    84: ["雪涧洞"],
    89: ["永福禅林"],
    93: ["谢家酒楼"],
    94: ["谢家酒楼"],
}


def merge_locations(raw: str, add: list[str]) -> tuple[str, bool]:
    m = re.search(r"^locations:\s*\n((?:[ \t]*-[ \t].+\n?)+)", raw, re.M)
    if not m:
        return raw, False
    existing = re.findall(r"^[ \t]*-[ \t]+(.+)$", m.group(1), re.M)
    merged = existing[:]
    changed = False
    for lid in add:
        if lid not in merged:
            merged.append(lid)
            changed = True
    if not changed:
        return raw, False
    block = "locations:\n" + "".join(f"  - {x}\n" for x in merged)
    new_raw = re.sub(
        r"^locations:\s*\n(?:[ \t]*-[ \t].+\n?)+",
        block,
        raw,
        count=1,
        flags=re.M,
    )
    return new_raw, True


def patch_chapters() -> int:
    n = 0
    for ch, add in CH_LOC.items():
        for ed in EDITIONS:
            p = CHAPTER_DIR / BOOK / ed / f"{ch:03d}.md"
            if not p.is_file():
                continue
            raw = p.read_text(encoding="utf-8-sig")
            new_raw, ok = merge_locations(raw, add)
            if ok:
                p.write_text(new_raw, encoding="utf-8")
                n += 1
                print(f"  ch {ch:03d} ({ed}): +{add}")
    return n


def patch_xie_parent() -> None:
    p = CONTENT / "locations" / BOOK / "谢家酒楼.md"
    raw = p.read_text(encoding="utf-8-sig")
    raw = raw.replace("parent: 临清", "parent: 临清钞关")
    p.write_text(raw, encoding="utf-8")


def patch_topic() -> None:
    p = CONTENT / "topics" / BOOK / "西门府建筑名录.md"
    raw = p.read_text(encoding="utf-8-sig")
    if "卧云亭" in raw:
        return
    raw = raw.replace(
        "  - 翡翠轩\n",
        "  - 翡翠轩\n  - 卧云亭\n",
    )
    raw = raw.replace(
        "[[卷棚]]，[[角门]] 通厅园）",
        "[[卷棚]] / [[卧云亭]]，[[角门]] 通厅园）",
    )
    block = """

## 外延节点（本轮 roster）

- [[谢家酒楼]] · [[永福禅林]] · [[雪涧洞]] · [[徐崶]]（严州知府，第92回）
"""
    if "外延节点" not in raw:
        raw = raw.rstrip() + block + "\n"
    p.write_text(raw, encoding="utf-8")


def main() -> int:
    print("[金瓶梅] patch new locations …")
    patch_xie_parent()
    n = patch_chapters()
    patch_topic()
    print(f"  chapters updated: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
