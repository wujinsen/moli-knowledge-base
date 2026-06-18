#!/usr/bin/env python3
"""B7 名物纵切：生成 items_cross_index.json + items_topics.json。"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from _common import DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "src" / "content"
OUT_INDEX = DATA_DIR / "items_cross_index.json"
OUT_TOPICS = DATA_DIR / "hongloumeng.items_topics.json"

SLUG_BY_BOOK = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}
KIND_DIRS = {
    "medicine": CONTENT / "medicines",
    "dish": CONTENT / "dishes",
    "costume": CONTENT / "costumes",
    "custom": CONTENT / "customs",
    "artifact": CONTENT / "artifacts",
}


def load_items(book: str) -> list[dict]:
    rows: list[dict] = []
    for kind, base in KIND_DIRS.items():
        d = base / book
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            fm, _ = parse_frontmatter(p)
            if fm.get("book") != book:
                continue
            rows.append(
                {
                    "id": fm["id"],
                    "name": fm.get("name", fm["id"]),
                    "kind": kind,
                    "chapters": _chapters(fm),
                    "characters": _characters(fm),
                }
            )
    return rows


def _chapters(fm: dict) -> list[int]:
    nums: set[int] = set()
    fa = fm.get("first_appear") or ""
    m = re.search(r"第(\d+)回", fa)
    if m:
        nums.add(int(m.group(1)))
    for a in fm.get("appear_in") or []:
        m = re.search(r"第(\d+)回", str(a))
        if m:
            nums.add(int(m.group(1)))
    return sorted(nums)


def _characters(fm: dict) -> list[str]:
    chars: set[str] = set()
    for key in ("eaters", "wearer", "patient", "participants", "prescriber", "physician"):
        for c in fm.get(key) or []:
            if isinstance(c, str) and c and not c.endswith("等"):
                chars.add(c.split("等")[0].strip())
    return sorted(chars)


def load_crosslinks(book: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    path = DATA_DIR / f"{book.replace('西游记', 'xiyouji').replace('红楼梦', 'hongloumeng').replace('金瓶梅', 'jinpingmei')}.crosslinks.json"
    if book == "红楼梦":
        path = DATA_DIR / "hongloumeng.crosslinks.json"
    elif book == "金瓶梅":
        path = DATA_DIR / "jinpingmei.crosslinks.json"
    else:
        path = DATA_DIR / "xiyouji.crosslinks.json"
    if not path.exists():
        return {}, {}
    data = json.loads(path.read_text(encoding="utf-8"))
    occ = data.get("occupant_items") or {}
    loc = data.get("location_items") or {}
    return occ, loc


def chapter_items(book: str) -> dict[int, list[str]]:
    by_ch: dict[int, set[str]] = defaultdict(set)
    d = CONTENT / "chapters" / book
    if not d.is_dir():
        return {}
    for p in d.rglob("*.md"):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != book:
            continue
        ch = fm.get("number")
        if ch is None:
            continue
        for iid in fm.get("items") or []:
            by_ch[int(ch)].add(iid)
    return {k: sorted(v) for k, v in sorted(by_ch.items())}


def scan_topic_links(book: str, item_ids: set[str]) -> dict[str, list[dict]]:
    by_item: dict[str, list[dict]] = defaultdict(list)
    d = CONTENT / "topics" / book
    if not d.is_dir():
        return {}
    for p in d.glob("*.md"):
        fm, body = parse_frontmatter(p)
        title = fm.get("title", p.stem)
        slug = p.stem
        text = body + json.dumps(fm, ensure_ascii=False)
        for iid in item_ids:
            if f"[[{iid}]]" in text or f"/i/{iid}" in text or f"/d/{iid}" in text:
                by_item[iid].append({"title": title, "slug": slug})
    for iid in by_item:
        seen: set[str] = set()
        uniq = []
        for t in by_item[iid]:
            if t["slug"] not in seen:
                seen.add(t["slug"])
                uniq.append(t)
        by_item[iid] = uniq[:8]
    return dict(by_item)


def build_book(book: str) -> dict:
    items = load_items(book)
    item_map = {i["id"]: i for i in items}
    occ, _loc = load_crosslinks(book)
    ch_from_chapters = chapter_items(book)

    by_ch: dict[str, list[dict]] = defaultdict(list)
    by_char: dict[str, list[dict]] = defaultdict(list)

    def add_row(row: dict, chapters: list[int], chars: list[str]) -> None:
        for ch in chapters:
            if row["id"] not in {r["id"] for r in by_ch[str(ch)]}:
                by_ch[str(ch)].append(row)
        for c in chars:
            if row["id"] not in {r["id"] for r in by_char[c]}:
                by_char[c].append(row)

    for item in items:
        row = {"id": item["id"], "name": item["name"], "kind": item["kind"]}
        chars = set(item["characters"])
        for cid, ids in occ.items():
            if item["id"] in ids:
                chars.add(cid)
        chapters = set(item["chapters"])
        for ch, ids in ch_from_chapters.items():
            if item["id"] in ids:
                chapters.add(ch)
        add_row(row, sorted(chapters), sorted(chars))

    for ch, ids in ch_from_chapters.items():
        for iid in ids:
            if iid in item_map and iid not in {r["id"] for r in by_ch[str(ch)]}:
                i = item_map[iid]
                by_ch[str(ch)].append({"id": i["id"], "name": i["name"], "kind": i["kind"]})

    slug = SLUG_BY_BOOK[book]
    return {
        "book": book,
        "slug": slug,
        "count": len(items),
        "byChapter": dict(by_ch),
        "byCharacter": dict(by_char),
        "entries": items,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    books_payload: dict[str, dict] = {}
    for book in SLUG_BY_BOOK:
        books_payload[SLUG_BY_BOOK[book]] = build_book(book)

    index_payload = {"generated_by": "build_items_cross_index.py", "books": books_payload}

    hlm_items = {i["id"] for i in books_payload["honglou"]["entries"]}
    topics_payload = {
        "book": "红楼梦",
        "generated_by": "build_items_cross_index.py",
        "links": scan_topic_links("红楼梦", hlm_items),
    }

    if args.write:
        OUT_INDEX.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        OUT_TOPICS.write_text(json.dumps(topics_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for slug, b in books_payload.items():
            print(
                f"  {slug}: {b['count']} items, "
                f"{len(b['byChapter'])} chapters, {len(b['byCharacter'])} characters, "
                f"{sum(len(v) for v in topics_payload['links'].values())} topic links"
            )
        print(f"written → {OUT_INDEX.name}, {OUT_TOPICS.name}")
    else:
        print(json.dumps({k: v["count"] for k, v in books_payload.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
