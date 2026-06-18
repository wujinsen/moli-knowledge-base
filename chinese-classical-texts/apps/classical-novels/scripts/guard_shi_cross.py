#!/usr/bin/env python3
"""Cross-book imagery links guard: ids exist, predicate 互文, bidirectional pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import CONTENT, DATA_DIR

ROOT = Path(__file__).resolve().parents[1]
IMG_ROOT = CONTENT / "imagery"
PREFIX_BOOK = {"hl-": "红楼梦", "jpm-": "金瓶梅", "xyj-": "西游记"}


def book_for_id(iid: str) -> str | None:
    for prefix, book in PREFIX_BOOK.items():
        if iid.startswith(prefix):
            return book
    return None


def imagery_exists(iid: str) -> bool:
    book = book_for_id(iid)
    if not book:
        return False
    return (IMG_ROOT / book / f"{iid}.md").exists()


def main() -> int:
    errors: list[str] = []
    path = DATA_DIR / "cross-book.imagery-links.json"
    if not path.exists():
        print("guard_shi_cross FAILED: missing cross-book.imagery-links.json")
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    links = data.get("links") or []
    if len(links) < 65:
        errors.append(f"links 过少: {len(links)}")

    seen: set[tuple[str, str, str]] = set()
    for i, link in enumerate(links):
        src = link.get("source")
        tgt = link.get("target")
        pred = link.get("predicate")
        if not src or not tgt:
            errors.append(f"link[{i}]: 缺 source/target")
            continue
        if pred != "互文":
            errors.append(f"link[{i}] {src}->{tgt}: predicate 应为 互文")
        if not link.get("inference"):
            errors.append(f"link[{i}] {src}->{tgt}: 应 inference: true")
        if not imagery_exists(src):
            errors.append(f"link[{i}]: source 不存在 {src}")
        if not imagery_exists(tgt):
            errors.append(f"link[{i}]: target 不存在 {tgt}")
        key = (src, pred or "", tgt)
        if key in seen:
            errors.append(f"重复边: {src} -> {tgt}")
        seen.add(key)

    books_touched: set[str] = set()
    for link in links:
        for end in (link.get("source"), link.get("target")):
            b = book_for_id(end or "")
            if b:
                books_touched.add(b)
    if len(books_touched) < 3:
        errors.append(f"应覆盖三书，实际: {books_touched}")

    if errors:
        print("guard_shi_cross FAILED:")
        for e in errors[:30]:
            print(f"  - {e}")
        return 1

    pairs = len(links) // 2
    print(f"guard_shi_cross OK: {len(links)} directed edges · ~{pairs} pairs · books {sorted(books_touched)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
