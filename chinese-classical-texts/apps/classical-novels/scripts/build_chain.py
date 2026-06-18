#!/usr/bin/env python3
"""C2 发家衰败链 P3–P4：生成 jinpingmei.chain.json（事件轴 + 交易芯片 + 人物反查）。"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter, resolve_books

SLUG = {"红楼梦": "hongloumeng", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}

JPM_CHAIN_PHASES = [
    {"key": "rise", "label": "发家根基", "range": [1, 17]},
    {"key": "climb", "label": "政商攀升", "range": [18, 40]},
    {"key": "peak", "label": "鼎盛极奢", "range": [41, 65]},
    {"key": "fall", "label": "衰败散府", "range": [66, 100]},
]


def phase_for(ch: int) -> dict:
    for p in JPM_CHAIN_PHASES:
        lo, hi = p["range"]
        if lo <= ch <= hi:
            return p
    return JPM_CHAIN_PHASES[2]


def load_silver_tx(book: str) -> dict[str, dict]:
    slug = SLUG.get(book, book)
    path = DATA_DIR / f"{slug}.silver.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {t["id"]: t for t in data.get("transactions", [])}


def load_sna_hubs(book: str) -> tuple[list[str], list[str]]:
    slug = SLUG.get(book, book)
    path = DATA_DIR / f"{slug}.sna.json"
    if not path.exists():
        return [], []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("hubs") or [], data.get("bangxian_hubs") or []


def pick_graph_focus(characters: list[str], hubs: list[str], bangxian: list[str]) -> str | None:
    priority = set(bangxian + hubs)
    for c in characters:
        if c in priority:
            return c
    return characters[0] if characters else None


def load_chain_events(book: str) -> list[dict]:
    d = CONTENT / "events" / book
    rows: list[dict] = []
    for path in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        if fm.get("book") != book:
            continue
        st = fm.get("subtype")
        if st not in ("financial", "plot"):
            continue
        ch = (fm.get("chapters") or [0])[0]
        ph = phase_for(int(ch))
        rows.append(
            {
                "id": fm["id"],
                "title": fm.get("title", ""),
                "subtype": st,
                "financial_kind": fm.get("financial_kind", ""),
                "chapters": fm.get("chapters") or [],
                "chapter": int(ch),
                "phase": ph["key"],
                "phase_label": ph["label"],
                "amount_liang": fm.get("amount_liang"),
                "summary": fm.get("summary", ""),
                "characters": fm.get("characters") or [],
                "locations": fm.get("locations") or [],
                "transaction_refs": fm.get("transaction_refs") or [],
                "prev": fm.get("prev"),
                "next": fm.get("next"),
                "tags": fm.get("tags") or [],
            }
        )
    rows.sort(key=lambda r: (r["chapter"], r["id"]))
    return rows


def build(book: str) -> dict:
    events = load_chain_events(book)
    tx_map = load_silver_tx(book)
    hubs, bangxian = load_sna_hubs(book)

    tx_chips: dict[str, dict] = {}
    for tid, t in tx_map.items():
        tx_chips[tid] = {
            "liang": t.get("liang"),
            "summary": t.get("summary", ""),
            "subtype": t.get("subtype", ""),
            "chapter": t.get("chapter"),
            "disputed": bool(t.get("disputed")),
        }

    by_character: dict[str, list[str]] = {}
    for ev in events:
        gf = pick_graph_focus(ev["characters"], hubs, bangxian)
        refs = ev["transaction_refs"]
        ev["module_links"] = {
            "graph_focus": gf,
            "has_silver": len(refs) > 0,
            "has_sna": bool(gf),
        }
        for c in ev["characters"]:
            by_character.setdefault(c, []).append(ev["id"])

    phase_counts = []
    for p in JPM_CHAIN_PHASES:
        lo, hi = p["range"]
        phase_counts.append(
            {**p, "count": sum(1 for e in events if lo <= e["chapter"] <= hi)}
        )

    return {
        "book": book,
        "generated": date.today().isoformat(),
        "event_count": len(events),
        "financial_count": sum(1 for e in events if e["subtype"] == "financial"),
        "plot_count": sum(1 for e in events if e["subtype"] == "plot"),
        "phases": phase_counts,
        "tx_chips": tx_chips,
        "by_character": by_character,
        "events": events,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", default="金瓶梅")
    args = ap.parse_args()
    for book in resolve_books(args.book):
        slug = SLUG.get(book, book)
        data = build(book)
        out = DATA_DIR / f"{slug}.chain.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        chips = sum(len(e["transaction_refs"]) for e in data["events"])
        print(
            f"[{book}] chain → {out.name} "
            f"({data['event_count']} events, {chips} tx refs, {len(data['tx_chips'])} chips)"
        )


if __name__ == "__main__":
    main()
