#!/usr/bin/env python3
"""C5 版本对勘 J3：生成 *.compare.json（异文索引 · 版本对 · 专题互链）。"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
VARIANTS_DIR = CONTENT / "variants"

SLUG_BY_BOOK = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}

COMPARE_PAIRS: dict[str, dict[str, dict[str, str]]] = {
    "jinpingmei": {
        "cihua-chongzhen": {"left": "词话本", "right": "崇祯本", "label": "词话 ↔ 崇祯"},
        "cihua-zhupo": {"left": "词话本", "right": "张竹坡评本", "label": "词话 ↔ 竹坡"},
        "chongzhen-zhupo": {"left": "崇祯本", "right": "张竹坡评本", "label": "崇祯 ↔ 竹坡"},
    },
    "xiyouji": {
        "shide-tongben": {"left": "世德堂本", "right": "通本", "label": "世德堂 ↔ 通本"},
    },
    "honglou": {
        "zhiben-chenggao": {"left": "脂砚斋本", "right": "程高本", "label": "脂本 ↔ 程高"},
    },
}


def pair_slug(ed_a: str, ed_b: str, book_slug: str) -> str | None:
    pairs = COMPARE_PAIRS.get(book_slug, {})
    for slug, p in pairs.items():
        if {ed_a, ed_b} == {p["left"], p["right"]}:
            return slug
    return None


def load_variants(book: str) -> list[dict]:
    d = VARIANTS_DIR / book
    if not d.is_dir():
        return []
    rows: list[dict] = []
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != book or fm.get("type") != "variant":
            continue
        rows.append(fm)
    return rows


def load_variant_topics(book_slug: str) -> list[dict]:
    path = DATA_DIR / f"{book_slug}.variant-topics.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("topics") or []


def build_book(book: str) -> dict | None:
    slug = SLUG_BY_BOOK.get(book)
    if not slug or slug not in COMPARE_PAIRS:
        return None

    variants = load_variants(book)
    by_ch: dict[str, list[dict]] = defaultdict(list)
    pair_chapters: dict[str, set[int]] = defaultdict(set)

    for fm in variants:
        ch = int(fm["chapter"])
        ed_a = fm.get("edition_a", "")
        ed_b = fm.get("edition_b", "")
        pairs: list[str] = []
        for ps in COMPARE_PAIRS[slug]:
            p = COMPARE_PAIRS[slug][ps]
            if {ed_a, ed_b} == {p["left"], p["right"]}:
                pairs.append(ps)
                pair_chapters[ps].add(ch)
        row = {
            "id": fm["id"],
            "category": fm.get("category", ""),
            "summary": fm.get("summary", ""),
            "edition_a": ed_a,
            "edition_b": ed_b,
            "text_a": fm.get("text_a"),
            "text_b": fm.get("text_b"),
            "topic_id": fm.get("topic_id"),
            "tags": fm.get("tags") or [],
            "pairs": pairs,
        }
        by_ch[str(ch)].append(row)

    pairs_out: dict[str, dict] = {}
    for ps, meta in COMPARE_PAIRS[slug].items():
        chs = sorted(pair_chapters.get(ps, set()))
        count = sum(1 for v in by_ch.values() for x in v if ps in x["pairs"])
        pairs_out[ps] = {
            **meta,
            "variant_count": count,
            "chapters_with_variants": chs,
        }

    return {
        "book": book,
        "slug": slug,
        "generated_by": "build_compare.py",
        "variant_total": len(variants),
        "chapter_count_with_variants": len(by_ch),
        "pairs": pairs_out,
        "by_chapter": dict(sorted(by_ch.items(), key=lambda x: int(x[0]))),
        "topics": load_variant_topics(slug),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", default="金瓶梅")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    payload = build_book(args.book)
    if not payload:
        print(f"skip: no compare pairs for {args.book}")
        return

    slug = payload["slug"]
    out = DATA_DIR / f"{slug}.compare.json"

    if args.write:
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(
            f"  {slug}: {payload['variant_total']} variants · "
            f"{payload['chapter_count_with_variants']} chapters · "
            f"{len(payload['pairs'])} pairs"
        )
        for ps, p in payload["pairs"].items():
            print(f"    {ps}: {p['variant_count']} anchors · {len(p['chapters_with_variants'])} chapters")
        print(f"written → {out.name}")
    else:
        print(json.dumps({k: payload[k] for k in ("variant_total", "chapter_count_with_variants")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
