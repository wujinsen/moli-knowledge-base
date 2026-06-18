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
    lint_location_graph,
    lint_summary_keys,
)

BOOK_SLUG = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

SECTIONS = [
    ("items_locations", "items 与 locations 重复", lint_items_location_dup),
    ("chapter_summaries", "回目 summary 缺漏", lint_summary_keys),
    ("character_fields", "人物字段缺漏", lint_character_fields),
    ("doc_links", "文档内链断裂", lint_broken_doc_links),
    ("unknown_characters", "未知人物（脂评本抽样）", lint_chapter_characters_unknown),
    ("location_graph", "地点图谱", lint_location_graph),
]

MAX_ITEMS = 50


def build_report(book: str) -> dict:
    sections = []
    total = 0
    for sid, title, fn in SECTIONS:
        items = fn(book)
        total += len(items)
        sections.append(
            {
                "id": sid,
                "title": title,
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
    for sec in report["sections"]:
        print(f"\n--- {sec['title']} ({sec['count']}) ---")
        for line in sec["items"][:10]:
            print(line)
        if sec["truncated"]:
            print(f"  ... +{sec['truncated']} more")
    d = report["density"]
    print(f"\n--- density: {d['totalCharacters']} chars, graph {d['graphNodes']}/{d['graphEdges']} ---")


if __name__ == "__main__":
    main()
