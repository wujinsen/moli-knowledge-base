#!/usr/bin/env python3
"""金瓶梅三版本回目 items[] 对齐：词话本 + 崇祯本 + 张竹坡评本。

以词话本 items[] 为基准，合并各版本正文扫描结果，三版写入同一并集列表。
（库内无独立「通本」目录；张竹坡评本即竹坡/通本系。）

用法：
  python scripts/align_jpm_chapter_items.py
  python scripts/align_jpm_chapter_items.py --dry-run
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CHAPTER_DIR
from lint_modules import list_known_item_ids
from tag_chapter_meta import find_ids, format_list, load_item_pairs, parse_list_field, split_body, strip_html

BOOK = "金瓶梅"
EDITIONS = ("词话本", "崇祯本", "张竹坡评本")


def chapter_paths(ch: int) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for ed in EDITIONS:
        p = CHAPTER_DIR / BOOK / ed / f"{ch:03d}.md"
        if p.is_file():
            out[ed] = p
    return out


def scan_items(raw: str, pairs, known: set[str]) -> set[str]:
    body = strip_html(split_body(raw))
    return set(find_ids(body, pairs, {})) & known


def write_items(raw: str, merged: list[str]) -> str:
    new_fm = format_list("items", merged)
    if re.search(r"^items:\s*\[", raw, re.M):
        return re.sub(r"^items:\s*\[[^\]]*\]", new_fm.strip(), raw, count=1, flags=re.M)
    if re.search(r"^summary:", raw, re.M):
        return re.sub(r"(^summary:.*\n)", rf"\1{new_fm}\n", raw, count=1, flags=re.M)
    return re.sub(r"(^---\s*\n(?:.*?\n)*?)(?=---\n)", rf"\1{new_fm}\n", raw, count=1, flags=re.M)


def align_chapter(ch: int, pairs, known: set[str], *, dry_run: bool) -> tuple[list[str], dict[str, int]]:
    paths = chapter_paths(ch)
    if not paths:
        return [], {}

    union: set[str] = set()
    for p in paths.values():
        raw = p.read_text(encoding="utf-8-sig")
        cur = set(parse_list_field(raw, "items") or [])
        found = scan_items(raw, pairs, known)
        union |= cur | found

    merged = sorted(union)
    deltas: dict[str, int] = {}
    for ed, p in paths.items():
        raw = p.read_text(encoding="utf-8-sig")
        cur = sorted(parse_list_field(raw, "items") or [])
        if cur == merged:
            continue
        deltas[ed] = len(merged) - len(cur)
        if not dry_run:
            p.write_text(write_items(raw, merged), encoding="utf-8")
    return merged, deltas


def main() -> int:
    parser = argparse.ArgumentParser(description="Align 金瓶梅 chapter items[] across editions")
    parser.add_argument("--dry-run", action="store_true", help="Report only, do not write")
    args = parser.parse_args()

    pairs = load_item_pairs(BOOK)
    known = list_known_item_ids(BOOK)
    total = 0
    by_ed: dict[str, int] = {e: 0 for e in EDITIONS}

    for ch in range(1, 101):
        merged, deltas = align_chapter(ch, pairs, known, dry_run=args.dry_run)
        if not merged or not deltas:
            continue
        parts = ", ".join(f"{e}+{n}" for e, n in sorted(deltas.items()))
        print(f"  第{ch:02d}回 → {len(merged)} 项 ({parts})")
        total += len(deltas)
        for e, n in deltas.items():
            if n:
                by_ed[e] += 1

    mode = "dry-run" if args.dry_run else "written"
    print(
        f"[{BOOK}] items[] 三版对齐 {mode}: "
        + ", ".join(f"{e} {by_ed[e]} 回" for e in EDITIONS)
        + f" · 共 {total} 处变更"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
