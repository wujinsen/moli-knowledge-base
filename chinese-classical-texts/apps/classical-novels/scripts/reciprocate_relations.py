#!/usr/bin/env python3
"""/dream 辅助 — 补全非对称 relations 的反向边（只改 frontmatter）。

非 SYMMETRIC 类型（主仆、父子等）：A→B 存在而 B 无 A 时，在 B 页追加同类型反向边。

用法:
  python scripts/reciprocate_relations.py 红楼梦 [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, parse_frontmatter, resolve_books  # noqa: E402

SYMMETRIC = {
    "夫妻", "兄弟", "姐妹", "妯娌", "师兄弟", "同僚", "朋友", "结拜", "情人", "仇敌", "敌对",
}


def write_frontmatter(path: Path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def collect_one_way(book: str) -> tuple[dict[str, dict], dict[str, Path], list[tuple[str, str, str]]]:
    char_dir = CHAR_DIR / book
    paths: dict[str, Path] = {}
    fms: dict[str, dict] = {}
    rel_targets: dict[str, set[str]] = {}

    for p in sorted(char_dir.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        cid = fm.get("id") or p.stem
        paths[cid] = p
        fms[cid] = fm
        rel_targets[cid] = {r["target"] for r in (fm.get("relations") or [])}

    ids = set(paths)
    one_way: list[tuple[str, str, str]] = []
    for src, fm in fms.items():
        for r in fm.get("relations") or []:
            t = r["target"]
            if t not in ids:
                continue
            rt = r.get("type", "")
            if rt in SYMMETRIC:
                continue
            if src not in rel_targets[t]:
                one_way.append((src, t, rt))
    return fms, paths, one_way


def patch_main_section(body: str, src: str, rtype: str) -> str:
    """若存在 ## 主要关系 且缺 [[src]]，追加一条 bullet。"""
    if f"[[{src}]]" in body:
        return body
    m = re.search(r"(## 主要关系\s*\n)(.*?)(?=\n## |\Z)", body, re.S)
    if not m:
        return body
    header, section = m.group(1), m.group(2)
    line = f"- [[{src}]]（{rtype}）\n"
    if section.strip():
        new_section = section.rstrip() + "\n" + line
    else:
        new_section = line
    return body[: m.start()] + header + new_section + body[m.end() :]


def reciprocate(book: str, dry_run: bool) -> int:
    fms, paths, one_way = collect_one_way(book)
    added = 0
    by_target: dict[str, list[tuple[str, str]]] = {}
    for src, tgt, rt in one_way:
        by_target.setdefault(tgt, []).append((src, rt))

    for tgt, pairs in sorted(by_target.items()):
        fm = fms[tgt]
        rels = list(fm.get("relations") or [])
        existing = {r["target"] for r in rels}
        fm_changed = False
        _, body = parse_frontmatter(paths[tgt])
        body_changed = False

        for src, rt in pairs:
            if src in existing:
                continue
            rels.append({"target": src, "type": rt})
            existing.add(src)
            fm_changed = True
            added += 1
            new_body = patch_main_section(body, src, rt)
            if new_body != body:
                body = new_body
                body_changed = True
            print(f"  + {tgt} ← {src} ({rt})")

        if fm_changed:
            fm["relations"] = rels
            if not dry_run:
                write_frontmatter(paths[tgt], fm, body if body_changed else parse_frontmatter(paths[tgt])[1])

    return added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("book", nargs="?", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for book in resolve_books(args.book):
        before = len(collect_one_way(book)[2])
        print(f"[{book}] 非对称单边 {before} 条" + (" (dry-run)" if args.dry_run else ""))
        n = reciprocate(book, args.dry_run)
        after = before if args.dry_run else len(collect_one_way(book)[2])
        print(f"[{book}] 补反向边 {n} 条 · 剩余 {after} 条\n")


if __name__ == "__main__":
    main()
