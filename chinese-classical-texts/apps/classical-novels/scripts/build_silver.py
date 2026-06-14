#!/usr/bin/env python3
"""Build *.silver.json — 金瓶梅白银流桑基图构建期数据（J4）。

Usage:
  python scripts/build_silver.py 金瓶梅
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter, resolve_books

SLUG = {"红楼梦": "hongloumeng", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}

POOL_COLORS: dict[str, str] = {
    "西门庆府": "#607a67",
    "蔡太师府": "#8a6532",
    "外部": "#9c8450",
    "妻妾奴婢": "#74332c",
    "帮闲圈": "#5c6359",
    "经营投资": "#33493c",
    "外室": "#6c8576",
    "宗教布施": "#266c7c",
    "官场打点": "#8a6a3b",
    "官府": "#4a5568",
    "玉皇庙": "#5a7a6a",
    "清河县": "#7a6a5a",
}

HUB = "西门庆府"


def pool_depth(name: str, out_to_hub: float, in_from_hub: float) -> int:
    if name == HUB:
        return 1
    if out_to_hub > in_from_hub * 1.05:
        return 0
    return 2


def load_transactions(book: str) -> list[dict]:
    d = CONTENT / "transactions" / book
    if not d.is_dir():
        return []
    rows: list[dict] = []
    for path in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        if fm.get("book") != book:
            continue
        liang = fm.get("amount_normalized")
        if liang is None:
            continue
        rows.append(
            {
                "id": fm["id"],
                "chapter": int(fm.get("chapter") or 0),
                "subtype": fm.get("subtype", ""),
                "liang": float(liang),
                "pool_from": fm.get("pool_from", ""),
                "pool_to": fm.get("pool_to", ""),
                "disputed": bool(fm.get("conversion_disputed")),
                "summary": fm.get("summary", ""),
                "source": fm.get("source", ""),
            }
        )
    rows.sort(key=lambda r: (r["chapter"], r["id"]))
    return rows


def verify_sources(book: str, txs: list[dict]) -> list[str]:
    issues: list[str] = []
    for t in txs:
        src = t.get("source") or ""
        ch = t["chapter"]
        if not src:
            issues.append(f"{t['id']}: 缺 source")
            continue
        if src.startswith("chapters/"):
            rel = src.replace("chapters/", "src/content/chapters/")
            base = Path(__file__).resolve().parents[1] / rel
            candidates = [
                base,
                base.parent / "词话本" / f"{ch:03d}.md",
                base.parent / "崇祯本" / f"{ch:03d}.md",
            ]
            if not any(p.exists() for p in candidates):
                issues.append(f"{t['id']}: source 不可达 ({src})")
    return issues


def build(book: str) -> dict:
    txs = load_transactions(book)
    link_map: dict[str, dict] = {}
    pool_out: dict[str, float] = defaultdict(float)
    pool_in: dict[str, float] = defaultdict(float)
    hub_in: dict[str, float] = defaultdict(float)
    hub_out: dict[str, float] = defaultdict(float)

    for t in txs:
        v = t["liang"]
        if v <= 0:
            continue
        pf, pt = t["pool_from"], t["pool_to"]
        key = f"{pf}→{pt}"
        bucket = link_map.setdefault(key, {"value": 0.0, "txs": []})
        bucket["value"] += v
        bucket["txs"].append(t["id"])
        pool_out[pf] += v
        pool_in[pt] += v
        if pt == HUB:
            hub_in[pf] += v
        if pf == HUB:
            hub_out[pt] += v

    pools = sorted(set(pool_out) | set(pool_in))
    pool_stats = []
    for name in pools:
        inf = round(pool_in[name], 2)
        outf = round(pool_out[name], 2)
        pool_stats.append(
            {
                "name": name,
                "inflow": inf,
                "outflow": outf,
                "net": round(inf - outf, 2),
                "depth": pool_depth(name, hub_in[name], hub_out[name]),
                "color": POOL_COLORS.get(name, "#607a67"),
            }
        )

    links = [
        {
            "source": k.split("→")[0],
            "target": k.split("→")[1],
            "value": round(v["value"], 2),
            "txs": v["txs"],
        }
        for k, v in sorted(link_map.items())
    ]

    by_ch: dict[int, list[str]] = defaultdict(list)
    for t in txs:
        if t["liang"] > 0:
            by_ch[t["chapter"]].append(t["id"])

    timeline = []
    cumulative = 0.0
    chapters = sorted(by_ch)
    for ch in chapters:
        delta = sum(t["liang"] for t in txs if t["chapter"] == ch and t["liang"] > 0)
        cumulative += delta
        timeline.append(
            {
                "chapter": ch,
                "delta": round(delta, 2),
                "cumulative": round(cumulative, 2),
                "tx_ids": by_ch[ch],
            }
        )

    hub_outflow = round(sum(hub_out.values()), 2)
    hub_inflow = round(sum(hub_in.values()), 2)

    return {
        "book": book,
        "generated": date.today().isoformat(),
        "transaction_count": len(txs),
        "disputed_count": sum(1 for t in txs if t["disputed"]),
        "total_liang": round(sum(t["liang"] for t in txs if t["liang"] > 0), 2),
        "chapter_min": min((t["chapter"] for t in txs), default=1),
        "chapter_max": max((t["chapter"] for t in txs), default=100),
        "hub": {
            "name": HUB,
            "inflow": hub_inflow,
            "outflow": hub_outflow,
            "net": round(hub_inflow - hub_outflow, 2),
        },
        "pools": pool_stats,
        "links": links,
        "timeline": timeline,
        "transactions": txs,
        "verify_issues": verify_sources(book, txs),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("book", nargs="?", default="金瓶梅")
    args = parser.parse_args()
    for book in resolve_books(args.book):
        slug = SLUG.get(book, book)
        data = build(book)
        out = DATA_DIR / f"{slug}.silver.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        issues = data.pop("verify_issues", [])
        print(f"[{book}] silver → {out.name} ({data['transaction_count']} tx, {data['total_liang']} 两)")
        if issues:
            for msg in issues:
                print(f"  [verify] {msg}")


if __name__ == "__main__":
    main()
