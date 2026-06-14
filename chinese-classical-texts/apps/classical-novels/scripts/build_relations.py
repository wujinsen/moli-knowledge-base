#!/usr/bin/env python3
"""/graph — 扫描人物 frontmatter，汇总成 src/data/<书>.relations.json。

- 去重双向关系
- 校验关系类型受控词表
- 把 contradicts 渲染成矛盾边（dashed）
- --sna：输出 src/data/<书>.sna.json（度 / 介数中心性）

用法: python scripts/build_relations.py [书名] [--sna]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

from _common import DATA_DIR, iter_characters, resolve_books

RELATION_TYPES = {
    "夫妻", "父子", "母子", "兄弟", "姐妹", "祖孙", "妯娌",
    "主仆", "师徒", "师兄弟", "同僚", "朋友", "结拜", "君臣",
    "情人", "恋慕", "仇敌", "敌对",
    # 金瓶梅
    "帮闲", "贿赂", "借贷", "认干亲", "庇护", "资助", "嫉妒", "陷害",
}
SYMMETRIC = {
    "夫妻", "兄弟", "姐妹", "妯娌", "师兄弟", "同僚", "朋友", "结拜", "情人", "仇敌", "敌对",
}


def betweenness_centrality(adj: dict[str, set[str]]) -> dict[str, float]:
    """Brandes 算法（无权重无向图）。"""
    nodes = list(adj.keys())
    bc = {v: 0.0 for v in nodes}
    for s in nodes:
        stack: list[str] = []
        pred: dict[str, list[str]] = defaultdict(list)
        sigma: dict[str, int] = defaultdict(int)
        dist: dict[str, int] = {}
        sigma[s] = 1
        dist[s] = 0
        queue = [s]
        while queue:
            v = queue.pop(0)
            stack.append(v)
            for w in adj[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta: dict[str, float] = {v: 0.0 for v in nodes}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                if sigma[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]
    n = len(nodes)
    if n > 2:
        scale = 2 / ((n - 1) * (n - 2))
        bc = {k: v * scale for k, v in bc.items()}
    return bc


def compute_sna(nodes: list[dict], edges: list[dict]) -> dict:
    char_nodes = [n for n in nodes if n.get("type") == "character"]
    ids = {n["id"] for n in char_nodes}
    adj: dict[str, set[str]] = {i: set() for i in ids}
    for e in edges:
        if e.get("contradiction"):
            continue
        s, t, typ = e["source"], e["target"], e["type"]
        if s not in ids or t not in ids:
            continue
        adj[s].add(t)
        if typ in SYMMETRIC:
            adj[t].add(s)
        else:
            adj[t].add(s)  # SNA 用无向近似

    bc = betweenness_centrality(adj)
    max_deg = max((len(adj[i]) for i in ids), default=1) or 1
    metrics = []
    meta = {n["id"]: n for n in char_nodes}
    for cid in sorted(ids):
        deg = len(adj[cid])
        metrics.append({
            "id": cid,
            "degree": deg,
            "degree_norm": round(deg / max_deg, 3),
            "betweenness": round(bc.get(cid, 0), 4),
            "faction": meta[cid].get("faction"),
            "ximen_proximity": meta[cid].get("ximen_proximity"),
        })
    metrics.sort(key=lambda m: (-m["betweenness"], -m["degree"], m["id"]))
    hubs = [m["id"] for m in metrics[:5]]
    return {"book": nodes[0].get("_book") if nodes else "", "metrics": metrics, "hubs": hubs}


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
        node: dict = {
            "id": cid,
            "type": fm.get("type", "character"),
            "faction": fm.get("faction", "未知"),
            "weight": fm.get("weight", 30),
        }
        if fm.get("ximen_proximity"):
            node["ximen_proximity"] = fm["ximen_proximity"]
        node["_book"] = book
        nodes.append(node)
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
        for topic in fm.get("contradicts") or []:
            topic_degree[topic] = topic_degree.get(topic, 0) + 1
            edges.append({
                "source": cid, "target": topic, "type": "矛盾",
                "contradiction": True,
            })

    for topic, deg in topic_degree.items():
        nodes.append({
            "id": topic,
            "type": "topic",
            "faction": "版本异文",
            "weight": min(100, 24 + deg * 12),
            "_book": book,
        })

    for n in nodes:
        n.pop("_book", None)

    return {"book": book, "nodes": nodes, "edges": edges, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("book", nargs="?", default=None)
    parser.add_argument("--sna", action="store_true", help="输出 SNA 指标 JSON")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for book in resolve_books(args.book):
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

        if args.sna or book == "金瓶梅":
            # 重建带 _book 的节点供 SNA
            sna_input = build_book(book)
            for n in sna_input["nodes"]:
                n["_book"] = book
            sna = compute_sna(sna_input["nodes"], sna_input["edges"])
            sna["book"] = book
            sna_path = DATA_DIR / f"{book}.sna.json"
            sna_path.write_text(json.dumps(sna, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{book}] SNA → {sna_path.name}（Top: {', '.join(sna['hubs'][:3])}）")


if __name__ == "__main__":
    main()
