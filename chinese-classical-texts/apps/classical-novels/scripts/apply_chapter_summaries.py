#!/usr/bin/env python3
"""Apply curated chapter summaries from src/data/<book>.chapter_summaries.json.

Only updates frontmatter summary when key exists and differs.
Supports 程高本 and optional 脂砚斋本 (same chapter numbers).

Usage:
  python scripts/apply_chapter_summaries.py 红楼梦
  python scripts/apply_chapter_summaries.py 红楼梦 --subdir 脂砚斋本
  python scripts/apply_chapter_summaries.py 红楼梦 --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _common import CHAPTER_DIR, DATA_DIR
from tag_chapter_meta import parse_scalar_field

SUMMARY_KEY = "summary"


def load_overrides(book: str) -> dict[int, str]:
    path = DATA_DIR / f"{book}.chapter_summaries.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("summaries") or {}
    out: dict[int, str] = {}
    for k, v in raw.items():
        if v and str(k).isdigit():
            out[int(k)] = str(v).strip()
    return out


def patch_summary(raw: str, summary: str) -> tuple[str, bool]:
    current = (parse_scalar_field(raw, SUMMARY_KEY) or "").strip()
    if current == summary:
        return raw, False
    if re.search(rf"^{SUMMARY_KEY}:\s*", raw, re.M):
        new_raw = re.sub(
            rf"^{SUMMARY_KEY}:\s*.*$",
            f"{SUMMARY_KEY}: {summary}",
            raw,
            count=1,
            flags=re.M,
        )
    else:
        new_raw = re.sub(
            r"\n---\s*\n",
            f"\n{SUMMARY_KEY}: {summary}\n---\n",
            raw,
            count=1,
        )
    return new_raw, True


def iter_files(book: str, subdir: str | None) -> list[Path]:
    base = CHAPTER_DIR / book
    if subdir:
        base = base / subdir
    return sorted(base.glob("[0-9]*.md"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply curated chapter summaries")
    ap.add_argument("book", nargs="?", default="红楼梦")
    ap.add_argument("--subdir", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    overrides = load_overrides(args.book)
    if not overrides:
        print(f"No overrides in {args.book}.chapter_summaries.json")
        return 1

    updated = 0
    for path in iter_files(args.book, args.subdir or None):
        num = int(path.stem)
        summary = overrides.get(num)
        if not summary:
            continue
        raw = path.read_text(encoding="utf-8-sig")
        new_raw, changed = patch_summary(raw, summary)
        if changed:
            updated += 1
            rel = path.relative_to(CHAPTER_DIR / args.book)
            print(f"  {rel}")
            if not args.dry_run:
                path.write_text(new_raw, encoding="utf-8")

    scope = args.subdir or "程高本"
    print(f"[{args.book}/{scope}] updated {updated} summaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
