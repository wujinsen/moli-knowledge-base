#!/usr/bin/env python3
"""生成 content 集合 JSON 快照，供 dev 下 Astro content store 为空时回退。

用法:
  python scripts/build_content_snapshots.py [--write]
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from _common import BOOKS, DATA_DIR, parse_frontmatter


def json_safe(obj: object) -> object:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    return obj

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "src" / "content"

SLUG_BY_BOOK = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

ITEM_DIRS: dict[str, Path] = {
    "medicine": CONTENT / "medicines",
    "dish": CONTENT / "dishes",
    "costume": CONTENT / "costumes",
    "custom": CONTENT / "customs",
    "artifact": CONTENT / "artifacts",
}

OUTPUTS: dict[str, Path] = {
    "characters": DATA_DIR / "characters_index.json",
    "events": DATA_DIR / "events_index.json",
    "locations": DATA_DIR / "locations_index.json",
    "items": DATA_DIR / "items_index.json",
    "topics": DATA_DIR / "topics_index.json",
    "imagery": DATA_DIR / "imagery_index.json",
    "transactions": DATA_DIR / "transactions_index.json",
}


def _defaults(fm: dict, pairs: dict[str, object]) -> dict:
    for k, v in pairs.items():
        fm.setdefault(k, v() if callable(v) else v)
    return fm


def load_book_dir(base: Path, book: str, *, entry_id: Callable[[Path, str], str] | None = None) -> list[dict]:
    d = base / book
    if not d.is_dir():
        return []
    rows: list[dict] = []
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != book:
            continue
        if entry_id:
            fm["_entry_id"] = entry_id(p, book)
        rows.append(fm)
    return rows


def load_characters(book: str) -> list[dict]:
    rows = load_book_dir(CONTENT / "characters", book)
    char_ids = {r.get("id") for r in rows if r.get("id")}
    catalog = None
    if book in ("红楼梦", "金瓶梅", "西游记"):
        from _item_wiki import (
            filter_hlm_keepsake_ids,
            filter_hlm_like_ids,
            filter_jpm_costume_ids,
            filter_jpm_keepsake_ids,
            filter_jpm_like_ids,
            filter_xyj_keepsake_ids,
            filter_xyj_like_ids,
            list_item_catalog,
        )

        catalog = list_item_catalog(book)
    for fm in rows:
        _defaults(
            fm,
            {
                "aliases": [],
                "tags": [],
                "relations": [],
                "喜好": [],
                "服饰": [],
                "关键物品": [],
                "能力": [],
                "法宝": [],
                "arc": [],
            },
        )
        if catalog is None:
            continue
        rel = fm.get("relations") or []
        cid = fm.get("id") or ""
        ctype = fm.get("type") or "character"
        likes = fm.get("喜好") or []
        if likes:
            if book == "红楼梦":
                fm["喜好"] = filter_hlm_like_ids(
                    likes, catalog, char_ids, relations=rel
                )
            elif book == "金瓶梅":
                fm["喜好"] = filter_jpm_like_ids(
                    likes, catalog, char_ids, relations=rel
                )
            elif book == "西游记":
                fm["喜好"] = filter_xyj_like_ids(
                    likes, catalog, char_ids, char_id=cid, faction=fm.get("faction") or "", relations=rel
                )
        keys = fm.get("关键物品") or []
        if keys:
            if book == "红楼梦":
                filtered = filter_hlm_keepsake_ids(
                    keys, catalog, char_ids, book=book
                )
            elif book == "金瓶梅":
                filtered = filter_jpm_keepsake_ids(
                    keys, catalog, char_ids, book=book
                )
            elif book == "西游记":
                filtered = filter_xyj_keepsake_ids(
                    keys,
                    catalog,
                    cid,
                    char_type=ctype,
                    char_ids=char_ids,
                    book=book,
                )
            else:
                filtered = keys
            if filtered:
                fm["关键物品"] = filtered
            else:
                fm.pop("关键物品", None)
        costumes = fm.get("服饰") or []
        if costumes and book == "金瓶梅":
            filtered_c = filter_jpm_costume_ids(costumes, catalog, cid)
            if filtered_c:
                fm["服饰"] = filtered_c
            else:
                fm.pop("服饰", None)
    rows.sort(key=lambda r: -(r.get("weight") or 0))
    return rows


def load_events(book: str) -> list[dict]:
    rows = load_book_dir(CONTENT / "events", book)
    for fm in rows:
        _defaults(
            fm,
            {
                "aliases": [],
                "chapters": [],
                "locations": [],
                "characters": [],
                "monsters": [],
                "artifacts": [],
                "tags": [],
                "transaction_refs": [],
                "variants": [],
                "contradicts": [],
                "scoped_relations": [],
            },
        )
    rows.sort(key=lambda r: ((r.get("chapters") or [999])[0], r.get("id", "")))
    return rows


def load_locations(book: str) -> list[dict]:
    rows = load_book_dir(CONTENT / "locations", book)
    for fm in rows:
        _defaults(
            fm,
            {
                "aliases": [],
                "occupants": [],
                "nearby": [],
                "features": [],
                "furnishings": [],
                "plants": [],
                "appear_in": [],
                "tags": [],
            },
        )
    rows.sort(key=lambda r: r.get("name", ""))
    return rows


def load_items(book: str) -> list[dict]:
    rows: list[dict] = []
    for kind, base in ITEM_DIRS.items():
        for p in sorted((base / book).glob("*.md")) if (base / book).is_dir() else []:
            fm, _ = parse_frontmatter(p)
            if fm.get("book") != book:
                continue
            fm["kind"] = kind
            _defaults(fm, {"tags": [], "appear_in": []})
            rows.append(fm)
    rows.sort(key=lambda r: r.get("name", ""))
    return rows


def load_topics(book: str) -> list[dict]:
    rows = load_book_dir(
        CONTENT / "topics",
        book,
        entry_id=lambda p, b: f"{b}/{p.stem}",
    )
    for fm in rows:
        _defaults(fm, {"tags": [], "derived_from": [], "hypotheses": [], "readings": []})
    rows.sort(key=lambda r: r.get("title", r.get("id", "")))
    return rows


def load_imagery(book: str) -> list[dict]:
    rows = load_book_dir(
        CONTENT / "imagery",
        book,
        entry_id=lambda p, b: f"{b}/{p.stem}",
    )
    for fm in rows:
        _defaults(fm, {"chapters": [], "characters": [], "links": [], "tags": []})
    rows.sort(key=lambda r: r.get("title", r.get("id", "")))
    return rows


def load_transactions(book: str) -> list[dict]:
    rows = load_book_dir(CONTENT / "transactions", book)
    for fm in rows:
        _defaults(fm, {"tags": []})
    rows.sort(key=lambda r: (r.get("chapter") or 0, r.get("id", "")))
    return rows


LOADERS: dict[str, Callable[[str], list[dict]]] = {
    "characters": load_characters,
    "events": load_events,
    "locations": load_locations,
    "items": load_items,
    "topics": load_topics,
    "imagery": load_imagery,
    "transactions": load_transactions,
}


def build_payload(name: str) -> dict:
    books: dict[str, dict] = {}
    for book in BOOKS:
        slug = SLUG_BY_BOOK[book]
        entries = LOADERS[name](book)
        books[slug] = {"book": book, "slug": slug, "count": len(entries), "entries": entries}
    return {"generated_by": "build_content_snapshots.py", "books": books}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    for name, out_path in OUTPUTS.items():
        payload = build_payload(name)
        total = sum(b["count"] for b in payload["books"].values())
        counts = ", ".join(f"{s}={payload['books'][s]['count']}" for s in payload["books"])
        print(f"  {name}: {total} ({counts})")
        if args.write:
            out_path.write_text(
                json.dumps(json_safe(payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    if args.write:
        print(f"written {len(OUTPUTS)} snapshot files → src/data/")
        import subprocess
        import sys

        shi = ROOT / "scripts" / "build_shi_index.py"
        subprocess.run([sys.executable, str(shi), "--write"], cwd=ROOT, check=True)
        karma = ROOT / "scripts" / "build_shi_karma.py"
        subprocess.run([sys.executable, str(karma), "--write"], cwd=ROOT, check=True)
        wuxing = ROOT / "scripts" / "build_shi_wuxing.py"
        subprocess.run([sys.executable, str(wuxing), "--write"], cwd=ROOT, check=True)
        nan = ROOT / "scripts" / "build_nan.py"
        subprocess.run([sys.executable, str(nan), "--write"], cwd=ROOT, check=True)
        items_x = ROOT / "scripts" / "build_items_cross_index.py"
        subprocess.run([sys.executable, str(items_x), "--write"], cwd=ROOT, check=True)
        for script in ("build_silver.py", "build_financial.py", "build_chain.py", "build_sna.py"):
            p = ROOT / "scripts" / script
            subprocess.run([sys.executable, str(p), "金瓶梅"], cwd=ROOT, check=True)
        for book in ("金瓶梅", "西游记"):
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build_compare.py"), book, "--write"],
                cwd=ROOT,
                check=True,
            )
    else:
        print("(dry-run, add --write)")


if __name__ == "__main__":
    main()
