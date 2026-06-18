#!/usr/bin/env python3
"""/guard JSON 报告 — 供维护台 Studio 批处理 Tab 调用。

用法:
  python scripts/guard_report.py 红楼梦
  python scripts/guard_report.py 红楼梦 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import CONTENT, iter_characters, parse_frontmatter, resolve_books
from trust_guard import (
    chapter_num,
    load_cihua_body,
    name_terms,
    parse_plot_bullets,
    text_has_any,
    verify_plot_line,
    verify_relation_edge,
)

BOOK_SLUG = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

SLUG_BOOK = {v: k for k, v in BOOK_SLUG.items()}

MAX_ITEMS = 60


def _guard_transactions_report(book: str) -> tuple[list[dict], int]:
    items: list[dict] = []
    tx_dir = CONTENT / "transactions" / book
    if not tx_dir.is_dir():
        return items, 0
    for path in sorted(tx_dir.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        tid = fm.get("id", path.stem)
        if fm.get("amount_normalized") is None:
            items.append(
                {
                    "kind": "transaction",
                    "entityId": tid,
                    "severity": "unverified",
                    "message": "缺 amount_normalized",
                }
            )
        if not fm.get("source"):
            items.append(
                {
                    "kind": "transaction",
                    "entityId": tid,
                    "severity": "unverified",
                    "message": "缺 source",
                }
            )
        if fm.get("conversion_disputed"):
            items.append(
                {
                    "kind": "transaction",
                    "entityId": tid,
                    "severity": "warn",
                    "message": "conversion_disputed（换算存疑，需人工复核）",
                }
            )
    return items, len(items)


def guard_book_report(book: str) -> dict:
    all_fms: dict[str, tuple] = {}
    for path, fm, body in iter_characters(book):
        cid = fm.get("id") or path.stem
        all_fms[cid] = (path, fm, body)

    first_appear_items: list[dict] = []
    plot_items: list[dict] = []
    relation_items: list[dict] = []
    plot_checked = 0
    rel_checked = 0
    chapter_cache: dict[int, str | None] = {}

    for cid, (_path, fm, body) in all_fms.items():
        no = chapter_num(fm.get("first_appear"))
        if no:
            text = load_cihua_body(book, no)
            if text is not None and not text_has_any(text, name_terms(fm, cid)):
                first_appear_items.append(
                    {
                        "kind": "first_appear",
                        "characterId": cid,
                        "severity": "unverified",
                        "message": f"first_appear=第{no}回 原文未见其名",
                        "chapter": no,
                    }
                )

        for chaps, plot in parse_plot_bullets(body):
            if not chaps:
                continue
            plot_checked += 1
            ok, hint = verify_plot_line(cid, fm, chaps, plot, book)
            if not ok:
                plot_items.append(
                    {
                        "kind": "plot",
                        "characterId": cid,
                        "severity": "unverified",
                        "message": plot[:120],
                        "chapters": chaps,
                        "hint": hint,
                    }
                )

        for rel in fm.get("relations") or []:
            if not isinstance(rel, dict):
                continue
            target = rel.get("target")
            rtype = rel.get("type", "?")
            if not target:
                continue
            rel_checked += 1
            ok, hint = verify_relation_edge(
                book, cid, fm, body, target, rtype, all_fms, chapter_cache
            )
            if not ok:
                role = rel.get("role")
                extra = f" role={role}" if role else ""
                relation_items.append(
                    {
                        "kind": "relation",
                        "characterId": cid,
                        "severity": "unverified",
                        "message": f"→ {target} ({rtype}{extra})",
                        "target": target,
                        "relationType": rtype,
                        "hint": hint,
                    }
                )

    tx_items, tx_count = _guard_transactions_report(book)

    sections = [
        {
            "id": "first_appear",
            "title": "first_appear 原文校验",
            "count": len(first_appear_items),
            "items": first_appear_items[:MAX_ITEMS],
            "truncated": max(0, len(first_appear_items) - MAX_ITEMS),
        },
        {
            "id": "plot",
            "title": "关键情节锚词",
            "count": len(plot_items),
            "checked": plot_checked,
            "items": plot_items[:MAX_ITEMS],
            "truncated": max(0, len(plot_items) - MAX_ITEMS),
        },
        {
            "id": "relation",
            "title": "relations 同现校验",
            "count": len(relation_items),
            "checked": rel_checked,
            "items": relation_items[:MAX_ITEMS],
            "truncated": max(0, len(relation_items) - MAX_ITEMS),
        },
        {
            "id": "transaction",
            "title": "transactions 字段",
            "count": tx_count,
            "items": tx_items[:MAX_ITEMS],
            "truncated": max(0, len(tx_items) - MAX_ITEMS),
        },
    ]

    total = len(first_appear_items) + len(plot_items) + len(relation_items) + tx_count

    return {
        "book": book,
        "bookSlug": BOOK_SLUG.get(book, book),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "passed": total == 0,
        "totalIssues": total,
        "summary": {
            "firstAppearUnverified": len(first_appear_items),
            "plotChecked": plot_checked,
            "plotUnverified": len(plot_items),
            "relationChecked": rel_checked,
            "relationUnverified": len(relation_items),
            "transactionIssues": tx_count,
        },
        "sections": sections,
    }


def build_report(book: str | None = None) -> dict:
    if book:
        return guard_book_report(book)
    # 全书合并（一般 Studio 按 slug 单书调用）
    books = resolve_books(book)
    if len(books) == 1:
        return guard_book_report(books[0])
    merged_sections: dict[str, dict] = {}
    total = 0
    summaries = []
    for b in books:
        r = guard_book_report(b)
        total += r["totalIssues"]
        summaries.append({"book": b, "totalIssues": r["totalIssues"], "passed": r["passed"]})
        for sec in r["sections"]:
            mid = sec["id"]
            if mid not in merged_sections:
                merged_sections[mid] = {**sec, "items": [], "count": 0, "truncated": 0}
            merged_sections[mid]["count"] += sec["count"]
            merged_sections[mid]["items"].extend(sec["items"])
    sections = []
    for sec in merged_sections.values():
        sec["items"] = sec["items"][:MAX_ITEMS]
        sections.append(sec)
    return {
        "book": "all",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "passed": total == 0,
        "totalIssues": total,
        "books": summaries,
        "sections": sections,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    report = build_report(args.book)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print(f"=== {report.get('book')} guard === passed={report['passed']} issues={report['totalIssues']}")
    for sec in report["sections"]:
        if sec["count"]:
            print(f"  {sec['title']}: {sec['count']}")


if __name__ == "__main__":
    main()
