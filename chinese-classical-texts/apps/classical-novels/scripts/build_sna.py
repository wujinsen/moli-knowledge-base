#!/usr/bin/env python3
"""Build *.sna.json — 金瓶梅社会网络分析构建期数据（J5）。

在 build_relations.compute_sna 基础上增补派系摘要、帮闲圈子网与白银 crosslinks。

Usage:
  python scripts/build_sna.py 金瓶梅
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _common import DATA_DIR, resolve_books  # noqa: E402
from build_relations import build_book, compute_sna  # noqa: E402

SLUG = {"红楼梦": "hongloumeng", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}
BANGXIAN_FACTION = "帮闲圈"


def load_crosslinks(slug: str) -> dict:
    path = DATA_DIR / f"{slug}.crosslinks.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def enrich(book: str, slug: str) -> dict:
    result = build_book(book)
    nodes = result["nodes"]
    edges = result["edges"]
    for n in nodes:
        n["_book"] = book

    base = compute_sna(nodes, edges)
    metrics = base["metrics"]

    # 派系内介数排名
    by_faction: dict[str, list[dict]] = defaultdict(list)
    for m in metrics:
        fac = m.get("faction") or "未知"
        by_faction[fac].append(m)
    for fac, group in by_faction.items():
        group.sort(key=lambda x: (-x["betweenness"], -x["degree"], x["id"]))
        for rank, m in enumerate(group, start=1):
            m["faction_rank"] = rank

    factions_summary = {}
    for fac, group in sorted(by_faction.items()):
        top = sorted(group, key=lambda x: (-x["betweenness"], -x["degree"]))[:3]
        factions_summary[fac] = {
            "count": len(group),
            "top_betweenness": [m["id"] for m in top],
            "max_degree": max((m["degree"] for m in group), default=0),
        }

    bangxian = [m for m in metrics if m.get("faction") == BANGXIAN_FACTION]
    bangxian.sort(key=lambda x: (-x["betweenness"], -x["degree"], x["id"]))
    bangxian_hubs = [m["id"] for m in bangxian[:5]]

    cl = load_crosslinks(slug)
    occupant_tx = cl.get("occupant_transactions") or {}
    silver_links = {k: v for k, v in sorted(occupant_tx.items()) if v}

    char_nodes = [n for n in nodes if n.get("type") == "character"]
    return {
        "book": book,
        "generated": date.today().isoformat(),
        "node_count": len(char_nodes),
        "edge_count": len(edges),
        "hubs": base["hubs"],
        "bangxian_hubs": bangxian_hubs,
        "factions": factions_summary,
        "metrics": metrics,
        "silver_links": silver_links,
    }


def sync_topic_summary(book: str, data: dict) -> None:
    """回填帮闲圈 topic 的节点规模行（可选）。"""
    if book != "金瓶梅":
        return
    topic = ROOT / "src/content/topics/金瓶梅/帮闲圈分析.md"
    if not topic.is_file():
        return
    text = topic.read_text(encoding="utf-8")
    bx = data["bangxian_hubs"]
    hubs = data["hubs"][:3]
    line = (
        f"> 生成：build_sna.py · {data['node_count']} 人物节点 · "
        f"介数 Top：{', '.join(hubs)} · 帮闲圈：{', '.join(bx[:3]) if bx else '—'}"
    )
    import re

    text = re.sub(
        r"> 生成：[^\n]+",
        line,
        text,
        count=1,
    )
    topic.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("book", nargs="?", default="金瓶梅")
    parser.add_argument("--no-topic", action="store_true", help="不回填帮闲圈 topic")
    args = parser.parse_args()

    for book in resolve_books(args.book):
        slug = SLUG.get(book, book)
        data = enrich(book, slug)
        out = DATA_DIR / f"{slug}.sna.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # 兼容旧路径
        legacy = DATA_DIR / f"{book}.sna.json"
        legacy.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
        print(
            f"[{book}] sna → {out.name} "
            f"({data['node_count']} nodes, 帮闲 Top: {', '.join(data['bangxian_hubs'][:3])})"
        )
        if not args.no_topic:
            sync_topic_summary(book, data)


if __name__ == "__main__":
    main()
