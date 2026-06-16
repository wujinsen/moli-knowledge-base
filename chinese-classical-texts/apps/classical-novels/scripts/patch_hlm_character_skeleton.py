#!/usr/bin/env python3
"""/dream 辅助 — 补人物页骨架（主要关系 / 评析）。

用法:
  python scripts/patch_hlm_character_skeleton.py 红楼梦 [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, parse_frontmatter, resolve_books  # noqa: E402

TYPE_ORDER = [
    "情人", "夫妻", "父子", "母子", "兄弟", "姐妹", "祖孙", "妯娌",
    "主仆", "师徒", "朋友", "结拜", "君臣", "恋慕", "仇敌", "敌对",
]


def write_frontmatter(path: Path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def rel_line(rel: dict) -> str:
    t, rt = rel["target"], rel.get("type", "")
    role = rel.get("role")
    if role:
        return f"- [[{t}]]：{rt}（{role}）。"
    return f"- [[{t}]]：{rt}。"


def grouped_rel_lines(rels: list[dict]) -> list[str]:
    if not rels:
        return ["- （见正文互链与回目出场。）"]
    if len(rels) <= 8:
        return [rel_line(r) for r in rels]

    by_type: dict[str, list[dict]] = defaultdict(list)
    for r in rels:
        by_type[r.get("type", "")].append(r)

    lines: list[str] = []
    for rt in TYPE_ORDER:
        group = by_type.pop(rt, [])
        if not group:
            continue
        if len(group) == 1:
            lines.append(rel_line(group[0]))
        else:
            links = "、".join(f"[[{g['target']}]]" for g in group)
            lines.append(f"- {rt}：{links}。")
    for rt, group in sorted(by_type.items()):
        links = "、".join(f"[[{g['target']}]]" for g in group)
        lines.append(f"- {rt}：{links}。")
    return lines


def make_review(fm: dict) -> str:
    summary = (fm.get("summary") or "").strip()
    status = fm.get("status") or "配角"
    tags = fm.get("tags") or []
    name = fm.get("name") or fm.get("id") or "此人"
    first = fm.get("first_appear") or ""

    if summary:
        lead = summary.split("；")[0].rstrip("。")
    else:
        lead = f"{name}为{status}级人物"

    if status == "主角":
        return f"{lead}；全书「情」与「空」之枢纽人物。"
    if status == "重要":
        return f"{lead}；属重要配角，与主线人物、情节空间紧密相连。"
    if "小厮" in tags:
        suffix = f"（{first}）" if first else ""
        return f"{lead}；怡红/跟班小厮辈，以随侍、传话见出场{suffix}。"
    if "丫鬟" in tags or "婢" in "".join(tags):
        return f"{lead}；婢仆辈配角，随主出场、见府内日常。"
    if "神话" in tags or fm.get("faction") == "太虚幻境":
        return f"{lead}；神话层人物，提纲全书命运与还泪结构。"
    return f"{lead}；{status}级人物，情节虽少但可回指主线空间。"


def section_bounds(body: str, heading: str) -> tuple[int, int] | None:
    pat = rf"(## {re.escape(heading)}\s*\n)(.*?)(?=\n## |\Z)"
    m = re.search(pat, body, re.S)
    if not m:
        return None
    return m.start(), m.end()


def insert_after_section(body: str, after: str, new_heading: str, content: str) -> str:
    bounds = section_bounds(body, after)
    if bounds:
        _, end = bounds
        block = f"\n## {new_heading}\n\n{content.rstrip()}\n"
        return body[:end] + block + body[end:]
    block = f"## {new_heading}\n\n{content.rstrip()}\n\n"
    return block + body.lstrip("\n")


def insert_before_section(body: str, before: str, new_heading: str, content: str) -> str:
    bounds = section_bounds(body, before)
    if bounds:
        start, _ = bounds
        block = f"## {new_heading}\n\n{content.rstrip()}\n\n"
        return body[:start] + block + body[start:]
    return body.rstrip() + f"\n\n## {new_heading}\n\n{content.rstrip()}\n"


def patch_body(fm: dict, body: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    rels = fm.get("relations") or []

    if "## 主要关系" not in body:
        lines = grouped_rel_lines(rels)
        content = "\n".join(lines)
        if section_bounds(body, "身份"):
            body = insert_after_section(body, "身份", "主要关系", content)
        elif section_bounds(body, "关键情节"):
            # insert before 关键情节
            bounds = section_bounds(body, "关键情节")
            assert bounds
            start, _ = bounds
            block = f"## 主要关系\n\n{content.rstrip()}\n\n"
            body = body[:start] + block + body[start:]
        else:
            body = f"## 主要关系\n\n{content.rstrip()}\n\n" + body.lstrip("\n")
        changes.append("主要关系")

    if "## 评析" not in body:
        review = make_review(fm)
        content = review
        for anchor in ("## 相关", "## 关联地点", "## 居所与名物"):
            if section_bounds(body, anchor.replace("## ", "")):
                body = insert_before_section(body, anchor.replace("## ", ""), "评析", content)
                changes.append("评析")
                break
        else:
            if section_bounds(body, "关键情节"):
                body = insert_after_section(body, "关键情节", "评析", content)
            else:
                body = body.rstrip() + f"\n\n## 评析\n\n{content.rstrip()}\n"
            changes.append("评析")

    return body, changes


def scan_thin(book: str) -> list[tuple[str, list[str]]]:
    char_dir = CHAR_DIR / book
    out: list[tuple[str, list[str]]] = []
    for p in sorted(char_dir.glob("*.md")):
        txt = p.read_text(encoding="utf-8-sig")
        miss = []
        if "## 主要关系" not in txt:
            miss.append("缺主要关系")
        if "## 评析" not in txt:
            miss.append("缺评析")
        if miss:
            out.append((p.stem, miss))
    return out


def patch_book(book: str, dry_run: bool) -> int:
    char_dir = CHAR_DIR / book
    n = 0
    for p in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(p)
        new_body, changes = patch_body(fm, body)
        if not changes:
            continue
        cid = fm.get("id") or p.stem
        print(f"  {cid}: {', '.join(changes)}")
        if not dry_run:
            write_frontmatter(p, fm, new_body)
        n += 1
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("book", nargs="?", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for book in resolve_books(args.book):
        if book != "红楼梦":
            print(f"[{book}] 暂仅支持红楼梦")
            continue
        before = len(scan_thin(book))
        print(f"[{book}] 结构薄页 {before} 页" + (" (dry-run)" if args.dry_run else ""))
        n = patch_book(book, args.dry_run)
        after = before if args.dry_run else len(scan_thin(book))
        print(f"[{book}] 修补 {n} 页 · 剩余 {after} 页\n")


if __name__ == "__main__":
    main()
