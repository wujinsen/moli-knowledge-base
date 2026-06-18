#!/usr/bin/env python3
"""将词话本章回 frontmatter（characters/locations/summary/items）同步至崇祯本、张竹坡评本。

三版本 items[] 并集对齐请用：python scripts/align_jpm_chapter_items.py

用法：python scripts/sync_jpm_chapter_meta.py
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from _common import CHAPTER_DIR, parse_frontmatter

BOOK = "金瓶梅"
SOURCE = "词话本"
TARGETS = ["崇祯本", "张竹坡评本"]
FIELDS = ("characters", "locations", "summary", "items")


def patch_from_source(src_fm: dict, dst_raw: str) -> str | None:
    dst_fm, body = _split_fm(dst_raw)
    changed = False
    for key in FIELDS:
        if key not in src_fm or src_fm[key] is None:
            continue
        if dst_fm.get(key) == src_fm[key]:
            continue
        dst_fm[key] = src_fm[key]
        changed = True
    if not changed:
        return None
    text = yaml.dump(dst_fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{text}---\n{body}"


def _split_fm(raw: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    if not m:
        return {}, raw
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def main() -> int:
    src_dir = CHAPTER_DIR / BOOK / SOURCE
    updated = 0
    for tgt in TARGETS:
        tgt_dir = CHAPTER_DIR / BOOK / tgt
        for src in sorted(src_dir.glob("[0-9]*.md")):
            dst = tgt_dir / src.name
            if not dst.is_file():
                continue
            src_fm, _ = parse_frontmatter(src)
            dst_raw = dst.read_text(encoding="utf-8-sig")
            new_raw = patch_from_source(src_fm, dst_raw)
            if new_raw is None:
                continue
            dst.write_text(new_raw, encoding="utf-8")
            updated += 1
    print(f"[{BOOK}] synced {updated} chapter files from {SOURCE} → {', '.join(TARGETS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
