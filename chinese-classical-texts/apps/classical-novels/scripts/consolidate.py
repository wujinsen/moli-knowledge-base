#!/usr/bin/env python3
"""/consolidate — 睡眠式巩固（重算重要度 + 别名冲突检测）。

当前实现的自动部分：
  - 重算 weight：按 关系数 与 出场标记 综合打分（0–100），写回 frontmatter。
  - 别名冲突检测：若不同人物共用别名，报告。
（更复杂的知识压缩 / 跨版本巩固由 LLM 按 AGENTS.md /dream 流程执行。）
用法: python scripts/consolidate.py [书名] [--write]
"""
from __future__ import annotations

import re
import sys

from _common import iter_characters, resolve_books


def score(fm: dict) -> int:
    rel = len(fm.get("relations") or [])
    base = {"主角": 60, "重要": 40, "配角": 20}.get(fm.get("status", ""), 20)
    return min(100, base + rel * 6)


def main():
    args = sys.argv[1:]
    write = "--write" in args
    book_arg = next((a for a in args if not a.startswith("--")), None)

    for book in resolve_books(book_arg):
        alias_owner: dict[str, str] = {}
        for path, fm, body in iter_characters(book):
            cid = fm.get("id", path.stem)
            new_w = score(fm)
            old_w = fm.get("weight")
            for a in (fm.get("aliases") or []):
                if a in alias_owner and alias_owner[a] != cid:
                    print(f"[{book}] 别名冲突: '{a}' 同属 {alias_owner[a]} 与 {cid}")
                alias_owner[a] = cid
            note = "" if old_w == new_w else f"(was {old_w})"
            print(f"[{book}] {cid}: weight={new_w} {note}")
            if write and old_w != new_w:
                text = path.read_text(encoding="utf-8")
                if re.search(r"^weight:.*$", text, re.M):
                    text = re.sub(r"^weight:.*$", f"weight: {new_w}", text, flags=re.M)
                else:
                    text = text.replace("\n---", f"\nweight: {new_w}\n---", 1)
                path.write_text(text, encoding="utf-8")
    if not write:
        print("（预览模式，加 --write 写回 weight）")


if __name__ == "__main__":
    main()
