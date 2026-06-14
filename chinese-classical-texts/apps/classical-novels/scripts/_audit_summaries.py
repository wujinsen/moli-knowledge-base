#!/usr/bin/env python3
"""List chapters whose summary equals title_to_summary(title)."""
from pathlib import Path

from _common import CHAPTER_DIR
from tag_chapter_meta import parse_scalar_field, title_to_summary


def audit(book: str, subdir: str | None) -> list[int]:
    base = CHAPTER_DIR / book
    if subdir:
        base = base / subdir
        files = sorted(base.glob("[0-9]*.md"))
    else:
        files = sorted(p for p in base.glob("[0-9]*.md") if p.parent.name == book)
    auto: list[int] = []
    for p in files:
        raw = p.read_text(encoding="utf-8-sig")
        title = parse_scalar_field(raw, "title") or ""
        summary = (parse_scalar_field(raw, "summary") or "").strip()
        if summary == title_to_summary(title):
            auto.append(int(p.stem))
    label = subdir or "程高本"
    print(f"=== {label} === total={len(files)} auto={len(auto)}")
    print(" ", auto)
    return auto


if __name__ == "__main__":
    audit("红楼梦", None)
    audit("红楼梦", "脂砚斋本")
