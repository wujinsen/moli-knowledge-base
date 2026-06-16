#!/usr/bin/env python3
"""从 chapters/*.md frontmatter 生成回目索引快照。

dev 下 content store 为空时，首页与阅读目录可回退此 JSON（与 garden_map 策略一致）。

用法:
  python scripts/build_chapter_index.py [--write]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import CHAPTER_DIR, DATA_DIR, parse_frontmatter

OUT = DATA_DIR / "chapters_index.json"
DEFAULT_EDITION = "程高本"


def load_all() -> dict:
    books: dict[str, dict[str, list[dict]]] = {}
    for path in sorted(CHAPTER_DIR.rglob("*.md")):
        fm, _ = parse_frontmatter(path)
        if fm.get("type") != "chapter":
            continue
        book = fm.get("book")
        number = fm.get("number")
        title = fm.get("title")
        if not book or number is None or not title:
            continue
        edition = fm.get("edition") or DEFAULT_EDITION
        books.setdefault(book, {}).setdefault(edition, []).append(
            {"number": int(number), "title": str(title)}
        )
    for ed_map in books.values():
        for items in ed_map.values():
            items.sort(key=lambda x: x["number"])
    return {"books": books}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    data = load_all()
    total = sum(len(v) for ed in data["books"].values() for v in ed.values())
    print(f"chapters_index: {len(data['books'])} books, {total} entries → {OUT.name}")
    for book, eds in data["books"].items():
        print(f"  {book}: " + ", ".join(f"{ed}×{len(items)}" for ed, items in eds.items()))
    if args.write:
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("written")
    else:
        print("(dry-run, add --write)")


if __name__ == "__main__":
    main()
