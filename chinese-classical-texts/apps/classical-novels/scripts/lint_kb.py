#!/usr/bin/env python3
"""/lint — 知识库体检（只报告，不改写）。

用法: python scripts/lint_kb.py 红楼梦
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from _common import BOOKS, CHAPTER_DIR, CONTENT, DATA_DIR, iter_characters, parse_frontmatter
from tag_chapter_meta import load_location_ids, load_location_pairs, parse_list_field

ROOT = Path(__file__).resolve().parents[1]


def location_ids(book: str) -> set[str]:
    ids = load_location_ids(book)
    for a, lid in load_location_pairs(book):
        ids.add(lid)
        ids.add(a)
    ids |= {"赖大家", "贾母套间"}
    return ids


def lint_items_location_dup(book: str) -> list[str]:
    loc_ids = location_ids(book)
    issues = []
    base = CHAPTER_DIR / book
    for p in sorted(base.rglob("*.md")):
        raw = p.read_text(encoding="utf-8-sig")
        items = parse_list_field(raw, "items") or []
        locs = parse_list_field(raw, "locations") or []
        dup = [i for i in items if i in loc_ids or i in locs]
        if dup:
            issues.append(f"items与locations: {p.relative_to(CHAPTER_DIR)} → {dup}")
    return issues


def chapter_count(book: str) -> int:
    p = CONTENT / "books" / f"{book}.md"
    if p.exists():
        fm, _ = parse_frontmatter(p)
        if fm.get("chapter_count"):
            return int(fm["chapter_count"])
    base = CHAPTER_DIR / book
    if base.exists():
        return len(list(base.glob("*.md")))
    return 120


def lint_summary_keys(book: str) -> list[str]:
    p = DATA_DIR / f"{book}.chapter_summaries.json"
    if not p.exists():
        return [f"missing {p.name}"]
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    summaries = data.get("summaries") or {}
    n = chapter_count(book)
    missing = [str(i) for i in range(1, n + 1) if str(i) not in summaries]
    return [f"chapter_summaries missing keys: {missing}"] if missing else []


def lint_character_fields(book: str) -> list[str]:
    issues = []
    for path, fm, _ in iter_characters(book):
        cid = fm.get("id") or path.stem
        if not fm.get("summary"):
            issues.append(f"no summary: {cid}")
        if not fm.get("first_appear"):
            issues.append(f"no first_appear: {cid}")
    return issues


def lint_chapter_characters_unknown(book: str) -> list[str]:
    known = {fm.get("id") for _, fm, _ in iter_characters(book)}
    for _, fm, _ in iter_characters(book):
        for a in fm.get("aliases") or []:
            known.add(a)
    unknown: dict[str, set[str]] = {}
    base = CHAPTER_DIR / book
    for p in base.rglob("*.md"):
        if "脂砚斋本" not in str(p):
            continue
        raw = p.read_text(encoding="utf-8-sig")
        chars = parse_list_field(raw, "characters") or []
        for c in chars:
            if c and c not in known and c != "通灵宝玉":
                unknown.setdefault(c, set()).add(str(p.relative_to(CHAPTER_DIR)))
    return [f"unknown character in chapters: {c} @ {sorted(v)[:3]}" for c, v in sorted(unknown.items())[:20]]


def lint_broken_doc_links(book: str) -> list[str]:
    topics = CONTENT / "topics" / book
    if not topics.exists():
        return []
    issues = []
    pat = re.compile(r"docs/([^`\s)]+\.md)")
    for tp in topics.glob("*.md"):
        for m in pat.finditer(tp.read_text(encoding="utf-8-sig")):
            doc = ROOT / "docs" / m.group(1)
            if not doc.exists():
                issues.append(f"broken doc link in {tp.name}: {m.group(1)}")
    return issues


def lint_location_graph(book: str) -> list[str]:
    """Orphans, zero chapter coverage, weak inbound (≤2 non-index)."""
    if book != "红楼梦":
        return []
    loc_dir = CONTENT / "locations" / book
    if not loc_dir.exists():
        return []
    loc_ids: set[str] = set()
    pages: dict[str, str] = {}
    for p in loc_dir.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        lid = fm.get("id") or p.stem
        loc_ids.add(lid)
        pages[lid] = p.read_text(encoding="utf-8")

    inbound: dict[str, set[str]] = defaultdict(set)

    def scan(text: str, source: str) -> None:
        for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", text):
            t = m.group(1).strip()
            if t in loc_ids:
                inbound[t].add(source)

    for lid, raw in pages.items():
        parts = raw.split("---", 2)
        body = parts[2] if len(parts) > 2 else ""
        fm_data, _ = parse_frontmatter(loc_dir / f"{lid}.md")
        for other in loc_ids:
            if other != lid and f"[[{other}]]" in body:
                inbound[other].add(f"wiki:{lid}")
        for n in fm_data.get("nearby") or []:
            if isinstance(n, str) and n in loc_ids and n != lid:
                inbound[n].add(f"nearby:{lid}")

    for sub in ("characters", "topics", "events"):
        d = CONTENT / sub / book
        if not d.exists():
            continue
        for p in d.rglob("*.md"):
            scan(p.read_text(encoding="utf-8"), f"{sub}:{p.stem}")

    idx = CONTENT / "topics" / book / "大观园建筑名录.md"
    if idx.exists():
        txt = idx.read_text(encoding="utf-8")
        for lid in loc_ids:
            if f"/l/{lid}" in txt:
                inbound[lid].add("index")

    ch_count: dict[str, int] = defaultdict(int)
    base = CHAPTER_DIR / book
    for p in base.glob("[0-9]*.md"):
        raw = p.read_text(encoding="utf-8-sig")
        locs = parse_list_field(raw, "locations") or []
        for x in locs:
            if x in loc_ids:
                ch_count[x] += 1

    issues: list[str] = []
    orphans = sorted(l for l in loc_ids if not inbound[l])
    if orphans:
        issues.append(f"location 孤儿页 ({len(orphans)}): {', '.join(orphans)}")
    zero_ch = sorted(l for l in loc_ids if ch_count[l] == 0)
    if zero_ch:
        issues.append(f"locations[] 零覆盖 ({len(zero_ch)}): {', '.join(zero_ch)}")
    weak = sorted(l for l in loc_ids if 0 < len(inbound[l]) <= 2 and "index" in inbound[l])
    if weak:
        issues.append(
            f"location 弱入链仅名录 ({len(weak)}): {', '.join(weak[:12])}"
            + (f" …+{len(weak)-12}" if len(weak) > 12 else "")
        )
    return issues


def main() -> None:
    book = sys.argv[1] if len(sys.argv) > 1 else "红楼梦"
    sections = [
        ("items与locations", lint_items_location_dup(book)),
        ("chapter_summaries", lint_summary_keys(book)),
        ("character fields", lint_character_fields(book)),
        ("doc links", lint_broken_doc_links(book)),
        ("unknown characters (脂评本抽样)", lint_chapter_characters_unknown(book)),
        ("location graph", lint_location_graph(book)),
    ]
    total = 0
    for title, items in sections:
        print(f"\n=== {title} ({len(items)}) ===")
        for line in items[:30]:
            print(line)
            total += 1
        if len(items) > 30:
            print(f"  ... +{len(items) - 30} more")
    print(f"\nLint 合计 {total} 条" + ("（通过）" if total == 0 else ""))


if __name__ == "__main__":
    main()
