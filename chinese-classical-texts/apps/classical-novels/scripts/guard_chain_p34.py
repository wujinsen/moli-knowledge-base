#!/usr/bin/env python3
"""C2 guard: 发家衰败链 P3–P4 — chain.json 与 events / silver 互证。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]


def load_event_tx_refs(book: str) -> dict[str, list[str]]:
    d = CONTENT / "events" / book
    out: dict[str, list[str]] = {}
    for p in d.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        if fm.get("subtype") not in ("financial", "plot"):
            continue
        out[fm["id"]] = fm.get("transaction_refs") or []
    return out


def main() -> int:
    chain_path = DATA_DIR / "jinpingmei.chain.json"
    silver_path = DATA_DIR / "jinpingmei.silver.json"
    errors: list[str] = []

    if not chain_path.exists():
        print("FAIL: missing jinpingmei.chain.json — run build_chain.py")
        return 1

    chain = json.loads(chain_path.read_text(encoding="utf-8"))
    event_refs = load_event_tx_refs("金瓶梅")
    silver_ids: set[str] = set()
    if silver_path.exists():
        silver = json.loads(silver_path.read_text(encoding="utf-8"))
        silver_ids = {t["id"] for t in silver.get("transactions", [])}

    chain_ids = {e["id"] for e in chain.get("events", [])}
    if chain_ids != set(event_refs):
        errors.append(f"chain events 与 frontmatter 不一致: {chain_ids ^ set(event_refs)}")

    for ev in chain.get("events", []):
        eid = ev["id"]
        refs = ev.get("transaction_refs") or []
        if refs != event_refs.get(eid, []):
            errors.append(f"{eid}: transaction_refs 与 event 页不一致")
        for tid in refs:
            if tid not in silver_ids:
                errors.append(f"{eid}: ref {tid} 不在 silver.json")
            if tid not in chain.get("tx_chips", {}):
                errors.append(f"{eid}: ref {tid} 缺 tx_chips")
        ml = ev.get("module_links") or {}
        if refs and not ml.get("has_silver"):
            errors.append(f"{eid}: 有 transaction_refs 但 has_silver=false")

    if not chain.get("by_character"):
        errors.append("by_character 为空")

    if errors:
        print("guard_chain_p34 FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    tx_refs = sum(len(e.get("transaction_refs") or []) for e in chain["events"])
    print(
        f"guard_chain_p34 OK: {chain['event_count']} events · "
        f"{tx_refs} tx refs · {len(chain['by_character'])} characters"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
