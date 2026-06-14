#!/usr/bin/env python3
"""Build *.financial.json — 金瓶梅 economic_event 专题链（J6）。

Usage:
  python scripts/build_financial.py 金瓶梅
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _common import CONTENT, DATA_DIR, parse_frontmatter, resolve_books

SLUG = {"红楼梦": "hongloumeng", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}

# 专题轨（与 global prev/next 正交，按 business 逻辑分组）
TRACKS: list[dict] = [
    {
        "id": "yapu",
        "label": "药铺·经营",
        "description": "生药铺发迹 → 结拜买办 → 酒店/绒线铺扩张",
        "color": "#607a67",
        "kinds": ["药铺", "经营"],
        "event_ids": ["jpm-fe-001", "jpm-fe-006", "jpm-fe-009", "jpm-fe-004"],
    },
    {
        "id": "fangzhai",
        "label": "放债·帮闲",
        "description": "西门庆经帮闲圈对外放贷，应伯爵等居中撮合",
        "color": "#5c6359",
        "kinds": ["放债"],
        "event_ids": ["jpm-fe-008", "jpm-fe-003"],
    },
    {
        "id": "huilu",
        "label": "政商贿赂",
        "description": "翟管家—蔡京链：认干礼、寿礼、二次进献",
        "color": "#8a6532",
        "kinds": ["贿赂"],
        "event_ids": ["jpm-fe-007", "jpm-fe-002", "jpm-fe-011"],
    },
    {
        "id": "yicai",
        "label": "遗产·变现",
        "description": "李瓶儿私房物资经纪变卖，注入经营池",
        "color": "#74332c",
        "kinds": ["遗产"],
        "event_ids": ["jpm-fe-005"],
    },
    {
        "id": "shuai",
        "label": "衰败耗散",
        "description": "丧礼与散府前变卖家当",
        "color": "#33493c",
        "kinds": ["经营"],
        "event_ids": ["jpm-fe-012"],
    },
]


def load_financial_events(book: str) -> list[dict]:
    d = CONTENT / "events" / book
    rows: list[dict] = []
    for path in sorted(d.glob("jpm-fe-*.md")):
        fm, body = parse_frontmatter(path)
        if fm.get("subtype") != "financial":
            continue
        rows.append(
            {
                "id": fm["id"],
                "title": fm.get("title", ""),
                "financial_kind": fm.get("financial_kind", ""),
                "chapters": fm.get("chapters") or [],
                "chapter": (fm.get("chapters") or [0])[0],
                "characters": fm.get("characters") or [],
                "locations": fm.get("locations") or [],
                "amount_liang": fm.get("amount_liang"),
                "transaction_refs": fm.get("transaction_refs") or [],
                "prev": fm.get("prev"),
                "next": fm.get("next"),
                "summary": fm.get("summary", ""),
                "tags": fm.get("tags") or [],
            }
        )
    rows.sort(key=lambda r: (r["chapter"], r["id"]))
    return rows


def build_timeline(events: list[dict]) -> list[dict]:
    """沿 prev/next 走主链。"""
    by_id = {e["id"]: e for e in events}
    heads = [e for e in events if not e.get("prev") or e["prev"] not in by_id]
    if not heads:
        return sorted(events, key=lambda e: (e["chapter"], e["id"]))
    start = min(heads, key=lambda e: (e["chapter"], e["id"]))
    chain: list[dict] = []
    cur: dict | None = start
    seen: set[str] = set()
    while cur and cur["id"] not in seen:
        seen.add(cur["id"])
        chain.append(cur)
        nxt = cur.get("next")
        cur = by_id.get(nxt) if nxt else None
    for e in events:
        if e["id"] not in seen:
            chain.append(e)
    return chain


def enrich_tracks(events: list[dict], tracks: list[dict]) -> list[dict]:
    by_id = {e["id"]: e for e in events}
    out: list[dict] = []
    for t in tracks:
        nodes = [by_id[eid] for eid in t["event_ids"] if eid in by_id]
        total = sum(n["amount_liang"] or 0 for n in nodes if n.get("amount_liang"))
        tx_count = sum(len(n["transaction_refs"]) for n in nodes)
        out.append(
            {
                **{k: v for k, v in t.items() if k != "kinds"},
                "events": nodes,
                "total_liang": round(total, 2) if total else None,
                "transaction_count": tx_count,
            }
        )
    return out


def build(book: str) -> dict:
    events = load_financial_events(book)
    timeline = build_timeline(events)
    tracks = enrich_tracks(events, TRACKS)
    by_kind: dict[str, list[str]] = {}
    for e in events:
        k = e["financial_kind"] or "其他"
        by_kind.setdefault(k, []).append(e["id"])
    return {
        "book": book,
        "generated": date.today().isoformat(),
        "event_count": len(events),
        "timeline": timeline,
        "tracks": tracks,
        "by_kind": by_kind,
        "events": events,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("book", nargs="?", default="金瓶梅")
    args = parser.parse_args()
    for book in resolve_books(args.book):
        slug = SLUG.get(book, book)
        data = build(book)
        out = DATA_DIR / f"{slug}.financial.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[{book}] financial → {out.name} ({data['event_count']} events, {len(data['tracks'])} tracks)")


if __name__ == "__main__":
    main()
