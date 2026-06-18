#!/usr/bin/env python3
"""Build *.crosslinks.json from entity frontmatter (+ optional manual seeds).

Outputs slug filenames (jinpingmei.crosslinks.json) for Vite SSR stability.

Usage:
  python scripts/build_crosslinks.py 金瓶梅
  python scripts/build_crosslinks.py --all
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter, resolve_books

CROSSLINKS_SLUG: dict[str, str] = {
    "红楼梦": "hongloumeng",
    "西游记": "xiyouji",
    "金瓶梅": "jinpingmei",
}

ITEM_DIRS = ("artifacts", "dishes", "medicines", "costumes", "customs")
PERSON_FIELDS = ("eaters", "wearers", "holders", "owners")
SINGLE_PERSON_FIELDS = ("wearer", "patient", "owner", "prescriber", "holder")


def _add(bucket: dict[str, list[str]], key: str, value: str) -> None:
    if not key or not value:
        return
    lst = bucket.setdefault(key, [])
    if value not in lst:
        lst.append(value)


def _merge_bucket(
    base: dict[str, list[str]], extra: dict[str, list[str]]
) -> dict[str, list[str]]:
    for key, ids in extra.items():
        for iid in ids:
            _add(base, key, iid)
    return {k: sorted(v) for k, v in sorted(base.items())}


def load_items(book: str) -> list[tuple[str, dict]]:
    rows: list[tuple[str, dict]] = []
    for kind in ITEM_DIRS:
        d = CONTENT / kind / book
        if not d.exists():
            continue
        for p in sorted(d.glob("*.md")):
            fm, _ = parse_frontmatter(p)
            iid = fm.get("id") or p.stem
            rows.append((iid, fm))
    return rows


def load_transactions(book: str) -> list[tuple[str, dict]]:
    d = CONTENT / "transactions" / book
    if not d.exists():
        return []
    rows: list[tuple[str, dict]] = []
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        tid = fm.get("id") or p.stem
        rows.append((tid, fm))
    return rows


def load_characters(book: str) -> list[tuple[str, dict]]:
    d = CONTENT / "characters" / book
    if not d.exists():
        return []
    rows: list[tuple[str, dict]] = []
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        cid = fm.get("id") or p.stem
        rows.append((cid, fm))
    return rows


def build_from_characters(book: str) -> dict[str, list[str]]:
    """人物 frontmatter 关键物品/服饰 → occupant_items（与 Studio 待办对齐）。"""
    occupant_items: dict[str, list[str]] = defaultdict(list)
    for cid, fm in load_characters(book):
        for field in ("关键物品", "服饰"):
            val = fm.get(field)
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str) and item:
                        _add(occupant_items, cid, item)
    return dict(occupant_items)


def build_from_entities(book: str) -> dict:
    location_items: dict[str, list[str]] = defaultdict(list)
    occupant_items: dict[str, list[str]] = defaultdict(list)
    occupant_transactions: dict[str, list[str]] = defaultdict(list)
    item_ids: set[str] = set()

    for iid, fm in load_items(book):
        item_ids.add(iid)
        loc = fm.get("location")
        if isinstance(loc, str) and loc:
            _add(location_items, loc, iid)

        for field in PERSON_FIELDS:
            val = fm.get(field)
            if isinstance(val, list):
                for person in val:
                    if isinstance(person, str):
                        _add(occupant_items, person, iid)

        for field in SINGLE_PERSON_FIELDS:
            val = fm.get(field)
            if isinstance(val, str) and val:
                _add(occupant_items, val, iid)

    for tid, fm in load_transactions(book):
        parties = [
            fm.get("buyer"),
            fm.get("seller"),
            fm.get("payee"),
        ]
        for person in parties:
            if isinstance(person, str) and person:
                _add(occupant_transactions, person, tid)

        item_ref = fm.get("item_ref")
        if isinstance(item_ref, str) and item_ref in item_ids:
            for person in parties:
                if isinstance(person, str) and person:
                    _add(occupant_items, person, item_ref)

    return {
        "location_items": dict(location_items),
        "occupant_items": dict(occupant_items),
        "occupant_transactions": dict(occupant_transactions),
    }


def output_path(book: str) -> Path:
    slug = CROSSLINKS_SLUG.get(book, book)
    return DATA_DIR / f"{slug}.crosslinks.json"


def load_existing(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_book(book: str) -> Path:
    out = output_path(book)
    existing = load_existing(out)
    generated = build_from_entities(book)
    from_chars = build_from_characters(book)

    location_items = _merge_bucket(
        existing.get("location_items") or {},
        generated["location_items"],
    )
    occupant_items = _merge_bucket(
        existing.get("occupant_items") or {},
        generated["occupant_items"],
    )
    occupant_items = _merge_bucket(occupant_items, from_chars)
    occupant_transactions = _merge_bucket(
        existing.get("occupant_transactions") or {},
        generated["occupant_transactions"],
    )

    payload = {
        "book": book,
        "generated": date.today().isoformat(),
        "location_items": location_items,
        "occupant_items": occupant_items,
    }
    if occupant_transactions:
        payload["occupant_transactions"] = occupant_transactions

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Build crosslinks JSON")
    ap.add_argument("book", nargs="?", help="书名")
    ap.add_argument("--all", action="store_true", help="三书全部重建")
    args = ap.parse_args()

    books = resolve_books(None if args.all else args.book)
    if not books:
        ap.error("请指定书名或 --all")

    for book in books:
        path = build_book(book)
        data = json.loads(path.read_text(encoding="utf-8"))
        loc_n = len(data.get("location_items") or {})
        occ_n = len(data.get("occupant_items") or {})
        tx_n = len(data.get("occupant_transactions") or {})
        print(f"{book}: {path.name} — {loc_n} 地点, {occ_n} 人物, {tx_n} 交易人物")


if __name__ == "__main__":
    main()
