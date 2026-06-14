#!/usr/bin/env python3
"""/graph — 扫描人物 frontmatter，汇总成 src/data/<书>.relations.json。

- 去重双向关系
- 校验关系类型受控词表
- 把 contradicts 渲染成矛盾边（dashed）
用法: python scripts/build_relations.py [书名]
"""
from __future__ import annotations

import json
import sys

from _common import DATA_DIR, iter_characters, resolve_books

RELATION_TYPES = {
    "夫妻", "父子", "母子", "兄弟", "姐妹", "祖孙", "妯娌",
    "主仆", "师徒", "师兄弟", "同僚", "朋友", "结拜", "君臣",
    "情人", "恋慕", "仇敌", "敌对",
}
SYMMETRIC = {"夫妻", "兄弟", "姐妹", "妯娌", "师兄弟", "同僚", "朋友", "结拜", "情人", "仇敌", "敌对"}


def build_book(book: str) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[tuple] = set()
    known_ids: set[str] = set()
    warnings: list[str] = []
    topic_degree: dict[str, int] = {}

    chars = list(iter_characters(book))
    for _, fm, _ in chars:
        known_ids.add(fm.get("id", ""))

    for path, fm, _ in chars:
        cid = fm.get("id")
        if not cid:
            warnings.append(f"{path.name}: 缺 id")
            continue
        nodes.append({
            "id": cid,
            "type": fm.get("type", "character"),
            "faction": fm.get("faction", "未知"),
            "weight": fm.get("weight", 30),
        })
        for rel in fm.get("relations") or []:
            target, rtype = rel.get("target"), rel.get("type")
            if rtype not in RELATION_TYPES:
                warnings.append(f"{cid}: 非法关系类型 '{rtype}'")
                continue
            if target not in known_ids:
                warnings.append(f"{cid}→{target}: 目标无独立页（可建页）")
            if rtype in SYMMETRIC:
                key = tuple(sorted([cid, target])) + (rtype,)
            else:
                key = (cid, target, rtype)
            if key in seen:
                continue
            seen.add(key)
            edges.append({
                "source": cid, "target": target, "type": rtype,
                "contradiction": False,
            })
        # 矛盾边：指向版本异文议题（合成 topic 节点）
        for topic in fm.get("contradicts") or []:
            topic_degree[topic] = topic_degree.get(topic, 0) + 1
            edges.append({
                "source": cid, "target": topic, "type": "矛盾",
                "contradiction": True,
            })

    # 为每个被引用的议题补一个合成节点，使矛盾边可在图谱中渲染并聚类
    for topic, deg in topic_degree.items():
        nodes.append({
            "id": topic,
            "type": "topic",
            "faction": "版本异文",
            "weight": min(100, 24 + deg * 12),
        })

    return {"book": book, "nodes": nodes, "edges": edges, "warnings": warnings}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for book in resolve_books(arg):
        result = build_book(book)
        if not result["nodes"]:
            print(f"[{book}] 无人物，跳过")
            continue
        out = DATA_DIR / f"{book}.relations.json"
        out.write_text(
            json.dumps(
                {"book": book, "nodes": result["nodes"], "edges": result["edges"]},
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        print(f"[{book}] {len(result['nodes'])} 节点 / {len(result['edges'])} 边 → {out.name}")
        for w in result["warnings"]:
            print(f"  warn: {w}")


if __name__ == "__main__":
    main()
