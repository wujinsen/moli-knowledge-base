#!/usr/bin/env python3
"""/lint JSON 报告 — 供维护台 Studio 批处理 Tab 调用。

用法:
  python scripts/lint_report.py 红楼梦
  python scripts/lint_report.py 红楼梦 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lint_character_density import collect_density
from lint_kb import (
    lint_broken_doc_links,
    lint_chapter_characters_unknown,
    lint_character_fields,
    lint_items_location_dup,
    lint_summary_keys,
)
from lint_modules import module_sections, module_stats

BOOK_SLUG = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

CORE_SECTIONS = [
    ("items_locations", "回目卫生 · items∩locations", "core", lint_items_location_dup),
    ("chapter_summaries", "回目 · summary 缺漏", "core", lint_summary_keys),
    ("character_fields", "人物 · 字段缺漏", "core", lint_character_fields),
    ("doc_links", "主题 · 文档内链断裂", "core", lint_broken_doc_links),
    ("unknown_characters", "回目 · 未知人物（脂评本）", "core", lint_chapter_characters_unknown),
]

MAX_ITEMS = 50


def build_report(book: str) -> dict:
    sections = []
    total = 0
    for sid, title, group, fn in CORE_SECTIONS + module_sections(book):
        items = fn(book)
        total += len(items)
        sections.append(
            {
                "id": sid,
                "title": title,
                "group": group,
                "count": len(items),
                "items": items[:MAX_ITEMS],
                "truncated": max(0, len(items) - MAX_ITEMS),
            }
        )

    density = collect_density(book)
    return {
        "book": book,
        "bookSlug": BOOK_SLUG.get(book, book),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalIssues": total,
        "passed": total == 0,
        "sections": sections,
        "moduleStats": module_stats(book),
        "density": density,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge base lint JSON report")
    parser.add_argument("book", nargs="?", default="红楼梦")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args()

    report = build_report(args.book)
    if args.json:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print(f"=== {args.book} lint report ===")
    print(f"totalIssues: {report['totalIssues']} passed={report['passed']}")
    ms = report.get("moduleStats") or {}
    if ms:
        parts = []
        if "items" in ms:
            parts.append(f"名物 {ms['items']['count']}")
        if "places" in ms:
            parts.append(f"建筑 {ms['places']['count']}")
        if "shi" in ms:
            parts.append(f"意象 {ms['shi']['count']}")
        print("modules: " + " · ".join(parts))
    for sec in report["sections"]:
        print(f"\n--- [{sec.get('group', '?')}] {sec['title']} ({sec['count']}) ---")
        for line in sec["items"][:10]:
            print(line)
        if sec["truncated"]:
            print(f"  ... +{sec['truncated']} more")
    d = report["density"]
    print(f"\n--- density: {d['totalCharacters']} chars, graph {d['graphNodes']}/{d['graphEdges']} ---")


if __name__ == "__main__":
    main()
