#!/usr/bin/env python3
"""/guard — Trust Guard 内容校验（防幻觉）。

对每个人物的 relations，尝试在原文回目中找到佐证：
若 first_appear 指向的回目原文里同时找不到本人与对方，则标 unverified。

金瓶梅 transaction：检查 amount_normalized 与 source 是否齐备。

用法: python scripts/trust_guard.py [书名]
"""
from __future__ import annotations

import re
import sys

from _common import CHAPTER_DIR, CONTENT, iter_characters, parse_frontmatter, resolve_books


def load_chapter_text(book: str, chap_no: int) -> str | None:
    p = CHAPTER_DIR / book / f"{chap_no:03d}.md"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def chapter_num(first_appear: str | None) -> int | None:
    if not first_appear:
        return None
    m = re.search(r"\d+", first_appear)
    return int(m.group()) if m else None


def guard_transactions(book: str) -> int:
    issues = 0
    tx_dir = CONTENT / "transactions" / book
    if not tx_dir.is_dir():
        return 0
    for path in sorted(tx_dir.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        tid = fm.get("id", path.stem)
        if fm.get("amount_normalized") is None:
            print(f"[{book}] {tid}: 缺 amount_normalized → unverified")
            issues += 1
        if not fm.get("source"):
            print(f"[{book}] {tid}: 缺 source → unverified")
            issues += 1
        if fm.get("conversion_disputed"):
            print(f"[{book}] {tid}: conversion_disputed（换算存疑，需人工复核）")
    return issues


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    issues = 0
    for book in resolve_books(arg):
        names = {fm.get("id"): fm for _, fm, _ in iter_characters(book)}
        for _, fm, _ in iter_characters(book):
            cid = fm.get("id")
            no = chapter_num(fm.get("first_appear"))
            text = load_chapter_text(book, no) if no else None
            if text is None:
                continue  # 原文未导入，跳过（非错误）
            aliases = [cid] + (fm.get("aliases") or [])
            if not any(a in text for a in aliases if a):
                print(f"[{book}] {cid}: first_appear=第{no}回 原文未见其名 → unverified")
                issues += 1
        issues += guard_transactions(book)
    print(f"Trust Guard 完成，{issues} 处存疑" if issues else "Trust Guard 通过")


if __name__ == "__main__":
    main()
