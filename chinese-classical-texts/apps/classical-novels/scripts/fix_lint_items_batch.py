#!/usr/bin/env python3
"""批量清 lint 名物待办：回目 items[] · crosslinks · 人物 frontmatter。

流水线:
  1. align_chapter_items — 正文扫描补 items[]
  2. sync_character_items_from_wiki — 名物页 holder/wearer 反推
  3. sync_character_items_from_crosslinks — occupant drift 回填
  4. build_crosslinks — 重建 occupant_items
  5. align_chapter_items — 二次（occupant 推断）
  6. sync_character_items_from_wiki — 二次

用法:
  python scripts/fix_lint_items_batch.py 红楼梦 西游记
  python scripts/fix_lint_items_batch.py --all
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print(f"\n>>> {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT.parent, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch fix item lint for books")
    ap.add_argument("books", nargs="*", help="书名")
    ap.add_argument("--all", action="store_true", help="红楼梦 + 西游记")
    args = ap.parse_args()

    books = list(args.books)
    if args.all:
        books = ["红楼梦", "西游记"]
    if not books:
        ap.error("请指定书名或 --all")

    py = sys.executable
    for book in books:
        print(f"\n========== {book} ==========")
        run([py, str(ROOT / "align_chapter_items.py"), book])
        run([py, str(ROOT / "sync_character_items_from_wiki.py"), book])
        run([py, str(ROOT / "sync_character_items_from_crosslinks.py"), book])
        run([py, str(ROOT / "build_crosslinks.py"), book])
        run([py, str(ROOT / "align_chapter_items.py"), book])
        run([py, str(ROOT / "sync_character_items_from_wiki.py"), book])
        run([py, str(ROOT / "fill_character_item_gaps.py"), book])
        run([py, str(ROOT / "sync_character_items_from_crosslinks.py"), book])
        run([py, str(ROOT / "build_crosslinks.py"), book])

    for book in books:
        if book == "红楼梦":
            run([py, str(ROOT / "clean_chapter_items.py"), book])

    for book in books:
        run([py, str(ROOT / "lint_report.py"), book])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
