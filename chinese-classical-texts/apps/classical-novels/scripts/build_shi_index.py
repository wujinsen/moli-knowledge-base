#!/usr/bin/env python3
"""B2 诗词意象 P2：生成章回 × 人物 × 意象交叉索引 shi_index.json。"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from _common import DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "src" / "content"
OUT = DATA_DIR / "shi_index.json"

SLUG_BY_BOOK = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}


def is_imagery_id(s: str) -> bool:
    return s.startswith(("hl-", "jpm-", "xyj-"))


def load_extra_links(book: str) -> dict[str, list[dict]]:
    path = DATA_DIR / f"{book}.imagery-links.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    by_source: dict[str, list[dict]] = defaultdict(list)
    for link in data.get("links", []):
        by_source[link["source"]].append(link)
    return by_source


def row_from_fm(fm: dict, extra: list[dict]) -> dict:
    chars: set[str] = set(fm.get("characters") or [])
    for link in fm.get("links") or []:
        tgt = link.get("target", "")
        if link.get("target_kind", "character") == "character" or not is_imagery_id(tgt):
            if tgt and not is_imagery_id(tgt):
                chars.add(tgt)
    for link in extra:
        tgt = link.get("target", "")
        if tgt and not is_imagery_id(tgt):
            chars.add(tgt)

    chapters: set[int] = set(fm.get("chapters") or [])
    for link in fm.get("links") or []:
        ch = link.get("chapter")
        if ch is not None:
            chapters.add(int(ch))
    for link in extra:
        ch = link.get("chapter")
        if ch is not None:
            chapters.add(int(ch))

    has_inf = any(l.get("inference") for l in fm.get("links") or []) or any(
        l.get("inference") for l in extra
    )

    return {
        "id": fm["id"],
        "title": fm["title"],
        "subtype": fm.get("subtype", ""),
        "chapters": sorted(chapters),
        "characters": sorted(chars),
        "hasInference": has_inf,
    }


def build_book(book: str) -> dict:
    img_dir = CONTENT / "imagery" / book
    extra_all = load_extra_links(book)
    entries: list[dict] = []
    by_ch: dict[str, list[dict]] = defaultdict(list)
    by_char: dict[str, list[dict]] = defaultdict(list)

    for path in sorted(img_dir.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        if fm.get("book") != book:
            continue
        extra = extra_all.get(fm["id"], [])
        row = row_from_fm(fm, extra)
        entries.append(row)
        for ch in row["chapters"]:
            by_ch[str(ch)].append(row)
        for c in row["characters"]:
            by_char[c].append(row)

    for rows in by_ch.values():
        rows.sort(key=lambda r: r["title"])
    for rows in by_char.values():
        rows.sort(key=lambda r: (r["chapters"][0] if r["chapters"] else 999, r["title"]))

    slug = SLUG_BY_BOOK[book]
    return {
        "book": book,
        "slug": slug,
        "count": len(entries),
        "byChapter": dict(by_ch),
        "byCharacter": dict(by_char),
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    books: dict[str, dict] = {}
    for book in SLUG_BY_BOOK:
        books[SLUG_BY_BOOK[book]] = build_book(book)

    payload = {
        "generated_by": "build_shi_index.py",
        "books": books,
    }

    if args.write:
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        for slug, b in books.items():
            print(f"  {slug}: {b['count']} entries, {len(b['byChapter'])} chapters, {len(b['byCharacter'])} characters")
        print(f"written → {OUT.relative_to(ROOT)}")
    else:
        print(json.dumps({k: v["count"] for k, v in books.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
