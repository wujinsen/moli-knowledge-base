#!/usr/bin/env python3
"""/ingest JSON 报告 — 供维护台 Studio 摄取 Tab 调用。

用法:
  python scripts/ingest_report.py 红楼梦 73
  python scripts/ingest_report.py 红楼梦 73 --edition chenggao --json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest_common import analyze_chapter_ingest

NOVELS_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Chapter ingest checklist report")
    ap.add_argument("book", help="书名")
    ap.add_argument("chapter", type=int, help="回目序号")
    ap.add_argument("--edition", dest="edition_slug", default=None, help="版本 slug，如 chenggao / zhiben")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    try:
        data = analyze_chapter_ingest(
            args.book,
            args.chapter,
            novels_root=NOVELS_ROOT,
            edition_slug=args.edition_slug,
        )
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    data["generatedAt"] = datetime.now(timezone.utc).isoformat()
    data["ready"] = not any(t.get("severity") == "error" for t in data.get("tasks") or [])

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"{data['book']} 第{data['chapter']}回 · {data['title']}")
        print(f"  路径: {data['chapterPath']}")
        print(f"  人物 {data['frontmatter']['characters']} · 缺页 {len(data['charactersMissingPage'])}")
        if data["bodyOnlyCharacters"]:
            print(f"  正文未列入: {', '.join(data['bodyOnlyCharacters'])}")
        for t in data["tasks"]:
            print(f"  [{t['severity']}] {t['label']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
