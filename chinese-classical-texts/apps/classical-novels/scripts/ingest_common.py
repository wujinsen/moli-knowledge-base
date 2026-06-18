#!/usr/bin/env python3
"""Shared /ingest chapter analysis for Studio."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

BOOK_SLUG = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

EDITION_SLUG = {
    "程高本": "chenggao",
    "脂砚斋本": "zhiben",
    "词话本": "cihua",
    "崇祯本": "chongzhen",
    "张竹坡评本": "zhupo",
    "世德堂本": "shide",
    "通本": "tongben",
}
SLUG_EDITION = {v: k for k, v in EDITION_SLUG.items()}

ITEM_DIRS = ("artifacts", "dishes", "medicines", "costumes", "customs")
LOCATION_DIR = "locations"

# 尚无人物页、无法进 alias 表的配角名（正文 substring 检测）
LITERAL_BODY_NAMES: dict[str, list[str]] = {
    "红楼梦": [],
}


def content_root(novels_root: Path) -> Path:
    return novels_root / "src" / "content"


def chapter_file(book: str, chapter: int, edition_slug: str | None, novels_root: Path) -> Path:
    base = content_root(novels_root) / "chapters" / book
    edition = SLUG_EDITION.get(edition_slug or "", "")
    if book == "红楼梦" and edition == "脂砚斋本":
        p = base / "脂砚斋本" / f"{chapter:03d}.md"
        if p.exists():
            return p
    return base / f"{chapter:03d}.md"


def read_url(book_slug: str, chapter: int, edition_slug: str | None, book: str) -> str:
    default_by_book = {
        "红楼梦": "zhiben" if chapter <= 80 else "chenggao",
        "金瓶梅": "cihua",
        "西游记": "shide",
    }
    ed = edition_slug or default_by_book.get(book, "default")
    if book == "红楼梦" and chapter > 80 and ed == "zhiben":
        ed = "chenggao"
    if book in ("红楼梦", "金瓶梅", "西游记"):
        return f"/{book_slug}/read/{ed}/{chapter}"
    return f"/{book_slug}/read/{chapter}"


def parse_chapter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def strip_html(text: str) -> str:
    t = re.sub(r"<[^>]+>", "", text)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def known_character_ids(book: str, novels_root: Path) -> set[str]:
    char_dir = content_root(novels_root) / "characters" / book
    if not char_dir.exists():
        return set()
    return {p.stem for p in char_dir.glob("*.md")}


def known_location_ids(book: str, novels_root: Path) -> set[str]:
    loc_dir = content_root(novels_root) / LOCATION_DIR / book
    if not loc_dir.exists():
        return set()
    return {p.stem for p in loc_dir.glob("*.md")}


def find_item_wiki(book: str, item_id: str, novels_root: Path) -> str | None:
    for kind in ITEM_DIRS:
        p = content_root(novels_root) / kind / book / f"{item_id}.md"
        if p.exists():
            return str(p.relative_to(novels_root)).replace("\\", "/")
    return None


def body_only_characters(book: str, body: str, listed: set[str], novels_root: Path) -> list[str]:
    """正文出现但 frontmatter characters[] 未列的人物（canonical id 或字面名）。"""
    try:
        from tag_chapter_characters import build_alias_map, find_characters, strip_html as tag_strip_html
    except ImportError:
        tag_strip_html = strip_html
        build_alias_map = find_characters = None  # type: ignore

    plain = tag_strip_html(body) if build_alias_map else strip_html(body)
    found: list[str] = []
    seen: set[str] = set()

    if build_alias_map and find_characters:
        alias_pairs = build_alias_map(book)
        for cid in find_characters(plain, alias_pairs):
            if cid not in listed and cid not in seen:
                seen.add(cid)
                found.append(cid)

    for name in LITERAL_BODY_NAMES.get(book, []):
        if name in plain and name not in listed and name not in seen:
            seen.add(name)
            found.append(name)

    return found


def analyze_chapter_ingest(
    book: str,
    chapter: int,
    *,
    novels_root: Path,
    edition_slug: str | None = None,
) -> dict:
    book_slug = BOOK_SLUG.get(book, book)
    path = chapter_file(book, chapter, edition_slug, novels_root)
    if not path.exists():
        raise FileNotFoundError(f"chapter not found: {chapter}")

    fm, body = parse_chapter(path)
    rel_path = str(path.relative_to(novels_root)).replace("\\", "/")
    edition_name = fm.get("edition") or SLUG_EDITION.get(edition_slug or "", "程高本")
    ed_slug = edition_slug or EDITION_SLUG.get(edition_name, "chenggao")

    chars = list(fm.get("characters") or [])
    locs = list(fm.get("locations") or [])
    items = list(fm.get("items") or [])
    char_set = set(chars)

    known_chars = known_character_ids(book, novels_root)
    known_locs = known_location_ids(book, novels_root)

    missing_chars = [c for c in chars if c not in known_chars]
    missing_locs = [loc for loc in locs if loc not in known_locs]
    missing_items = [i for i in items if not find_item_wiki(book, i, novels_root)]

    body_only = body_only_characters(book, body, char_set, novels_root)
    excerpt = strip_html(body)[:480]
    if len(strip_html(body)) > 480:
        excerpt += "…"

    tasks: list[dict] = []
    if not fm.get("summary"):
        tasks.append({"id": "summary", "label": "补写回目 summary", "severity": "warn"})
    if missing_chars:
        tasks.append(
            {
                "id": "missing_char_pages",
                "label": f"缺人物页 {len(missing_chars)} 个",
                "severity": "info",
                "entities": missing_chars[:12],
            }
        )
    if body_only:
        tasks.append(
            {
                "id": "fm_characters",
                "label": f"正文提及但 frontmatter 未列 {len(body_only)} 个",
                "severity": "warn",
                "entities": body_only,
            }
        )
    if missing_locs:
        tasks.append(
            {
                "id": "missing_loc_pages",
                "label": f"缺地点页 {len(missing_locs)} 个",
                "severity": "info",
                "entities": missing_locs[:8],
            }
        )
    if missing_items:
        tasks.append(
            {
                "id": "missing_item_pages",
                "label": f"缺名物页 {len(missing_items)} 个",
                "severity": "warn",
                "entities": missing_items,
            }
        )
    tasks.append({"id": "plot_bullets", "label": "更新登场人物关键情节（带出处）", "severity": "info"})
    tasks.append({"id": "index_log", "label": "更新 index.md 与 log.md", "severity": "info"})

    return {
        "book": book,
        "bookSlug": book_slug,
        "chapter": chapter,
        "title": fm.get("title") or f"第{chapter}回",
        "edition": edition_name,
        "editionSlug": ed_slug,
        "readUrl": read_url(book_slug, chapter, ed_slug, book),
        "chapterPath": rel_path,
        "excerpt": excerpt,
        "frontmatter": {
            "characters": len(chars),
            "locations": len(locs),
            "items": len(items),
            "hasSummary": bool(fm.get("summary")),
        },
        "charactersListed": chars,
        "charactersWithPage": [c for c in chars if c in known_chars],
        "charactersMissingPage": missing_chars,
        "bodyOnlyCharacters": body_only,
        "locationsListed": locs,
        "locationsMissingPage": missing_locs,
        "itemsListed": items,
        "itemsMissingPage": missing_items,
        "tasks": tasks,
        "entityPath": rel_path,
        "entityFrontmatter": fm,
    }
