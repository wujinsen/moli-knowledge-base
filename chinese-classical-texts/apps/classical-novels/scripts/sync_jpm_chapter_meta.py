#!/usr/bin/env python3
"""将词话本章回 frontmatter（characters/locations/summary/items）同步至崇祯本、张竹坡评本。

用法：python scripts/sync_jpm_chapter_meta.py
"""
from __future__ import annotations

import re
from pathlib import Path

from _common import CHAPTER_DIR

BOOK = "金瓶梅"
SOURCE = "词话本"
TARGETS = ["崇祯本", "张竹坡评本"]
FIELDS = ("characters", "locations", "summary", "items")


def extract_field(raw: str, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(.+)$", raw, re.M)
    return m.group(0) if m else None


def patch_fields(raw: str, fields: dict[str, str]) -> str:
    out = raw
    for key, line in fields.items():
        if re.search(rf"^{key}:", out, re.M):
            out = re.sub(rf"^{key}:.*$", line, out, count=1, flags=re.M)
        else:
            out = re.sub(r"(^---\s*\n(?:.*?\n)*?)(?=\n---)", rf"\1{line}\n", out, count=1, flags=re.M)
    return out


def main() -> int:
    src_dir = CHAPTER_DIR / BOOK / SOURCE
    updated = 0
    for tgt in TARGETS:
        tgt_dir = CHAPTER_DIR / BOOK / tgt
        for src in sorted(src_dir.glob("[0-9]*.md")):
            dst = tgt_dir / src.name
            if not dst.exists():
                continue
            src_raw = src.read_text(encoding="utf-8")
            dst_raw = dst.read_text(encoding="utf-8")
            patch: dict[str, str] = {}
            for key in FIELDS:
                line = extract_field(src_raw, key)
                if line:
                    patch[key] = line
            if not patch:
                continue
            new_raw = patch_fields(dst_raw, patch)
            if new_raw != dst_raw:
                dst.write_text(new_raw, encoding="utf-8")
                updated += 1
    print(f"[{BOOK}] synced {updated} chapter files from {SOURCE} → {', '.join(TARGETS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
