#!/usr/bin/env python3
"""/graph JSON 报告 — 供维护台 Studio 批处理 Tab 调用。

用法:
  python scripts/graph_report.py 红楼梦 --json          # 预览（不写盘）
  python scripts/graph_report.py 红楼梦 --json --apply  # 重建 relations.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import DATA_DIR
from build_relations import build_book, compute_sna

BOOK_SLUG = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

MAX_WARNINGS = 60


def _edge_type_counts(edges: list[dict]) -> list[dict]:
    c = Counter(e.get("type", "?") for e in edges)
    return [{"type": t, "count": n} for t, n in c.most_common()]


def _character_node_count(nodes: list[dict]) -> int:
    return sum(1 for n in nodes if n.get("type") in ("character", "monster"))


def build_report(book: str, *, apply: bool = False) -> dict:
    result = build_book(book)
    nodes = result["nodes"]
    edges = result["edges"]
    warnings = result["warnings"]

    report: dict = {
        "book": book,
        "bookSlug": BOOK_SLUG.get(book, book),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "preview": not apply,
        "applied": False,
        "nodeCount": len(nodes),
        "edgeCount": len(edges),
        "characterCount": _character_node_count(nodes),
        "topicCount": sum(1 for n in nodes if n.get("type") == "topic"),
        "contradictionEdges": sum(1 for e in edges if e.get("contradiction")),
        "edgeTypes": _edge_type_counts(edges),
        "warningCount": len(warnings),
        "warnings": warnings[:MAX_WARNINGS],
        "truncatedWarnings": max(0, len(warnings) - MAX_WARNINGS),
        "outputPath": f"src/data/{book}.relations.json",
        "snaPath": None,
        "snaHubs": [],
    }

    if not nodes:
        report["error"] = "无人物节点，跳过写盘"
        return report

    if not apply:
        return report

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / f"{book}.relations.json"
    out.write_text(
        json.dumps({"book": book, "nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report["applied"] = True
    report["preview"] = False

    if book == "金瓶梅":
        sna_input = build_book(book)
        for n in sna_input["nodes"]:
            n["_book"] = book
        sna = compute_sna(sna_input["nodes"], sna_input["edges"])
        sna["book"] = book
        sna_path = DATA_DIR / f"{book}.sna.json"
        sna_path.write_text(json.dumps(sna, ensure_ascii=False, indent=2), encoding="utf-8")
        report["snaPath"] = f"src/data/{book}.sna.json"
        report["snaHubs"] = sna.get("hubs", [])[:5]

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Graph rebuild JSON report")
    parser.add_argument("book", nargs="?", default="红楼梦")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Write relations.json (+ SNA for 金瓶梅)")
    args = parser.parse_args()

    report = build_report(args.book, apply=args.apply)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    mode = "APPLY" if args.apply else "PREVIEW"
    print(f"=== {args.book} graph {mode} ===")
    print(f"nodes={report['nodeCount']} edges={report['edgeCount']} warnings={report['warningCount']}")
    if report.get("applied"):
        print(f"written → {report['outputPath']}")


if __name__ == "__main__":
    main()
