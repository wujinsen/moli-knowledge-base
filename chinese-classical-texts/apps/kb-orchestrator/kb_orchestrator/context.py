from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

from .config import CROSSLINKS_SLUG, ITEM_DIRS, NOVELS_ROOT, SLUG_BOOK
from .parse_md import count_plot_bullets, parse_chapter_num, parse_frontmatter

_SCRIPTS = NOVELS_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from ingest_common import analyze_chapter_ingest  # noqa: E402


def _content(book: str) -> Path:
    return NOVELS_ROOT / "src" / "content"


def _data(book: str) -> Path:
    return NOVELS_ROOT / "src" / "data"


def _load_item_ids(book: str) -> set[str]:
    slug = CROSSLINKS_SLUG.get(book, book)
    path = _data(book) / f"{slug}.item_ids.json"
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def _load_crosslinks(book: str) -> dict:
    slug = CROSSLINKS_SLUG.get(book, book)
    path = _data(book) / f"{slug}.crosslinks.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _find_item_wiki(book: str, item_id: str) -> tuple[str | None, dict]:
    for kind in ITEM_DIRS:
        p = _content(book) / kind / book / f"{item_id}.md"
        if p.exists():
            fm, _ = parse_frontmatter(p)
            return str(p.relative_to(NOVELS_ROOT)).replace("\\", "/"), fm
    return None, {}


def _item_link(book: str, item_id: str, item_ids: set[str], occupant: list[str]) -> dict:
    wiki_path, fm = _find_item_wiki(book, item_id)
    linked = item_id in item_ids and wiki_path is not None
    issues: list[str] = []
    if item_id not in item_ids:
        issues.append("not_in_item_ids")
    if not wiki_path:
        issues.append("missing_wiki_page")
    if item_id not in occupant and linked:
        issues.append("missing_from_crosslinks")
    wearer = fm.get("wearer") if fm else None
    return {
        "id": item_id,
        "kind": "costume" if wiki_path and "/costumes/" in wiki_path else None,
        "wikiPath": wiki_path,
        "wearer": wearer,
        "first_appear": fm.get("first_appear") if fm else None,
        "linked": linked,
        "issues": issues,
    }


def _chapters_with_items(book: str, item_ids: list[str]) -> list[dict]:
    ch_dir = _content(book) / "chapters" / book
    if not ch_dir.exists():
        return []
    rows: list[dict] = []
    want = set(item_ids)
    for p in sorted(ch_dir.glob("*.md")):
        if not re.match(r"^\d+\.md$", p.name):
            continue
        fm, _ = parse_frontmatter(p)
        items = fm.get("items") or []
        hit = [i for i in items if i in want]
        if hit:
            n = int(p.stem)
            rows.append({"n": n, "items": hit, "summary": (fm.get("summary") or "")[:80]})
    return rows[:8]


def _lint_hints(key_items: list[dict], costumes: list[dict]) -> list[dict]:
    hints: list[dict] = []
    for it in key_items + costumes:
        if "missing_from_crosslinks" in (it.get("issues") or []):
            hints.append(
                {
                    "code": "crosslinks_missing_item",
                    "severity": "warn",
                    "message": f"occupant_items 缺 {it['id']}，但 frontmatter 已列",
                }
            )
        if "missing_wiki_page" in (it.get("issues") or []):
            hints.append(
                {
                    "code": "missing_wiki_page",
                    "severity": "error",
                    "message": f"名物页不存在：{it['id']}",
                }
            )
    return hints


def _ingest_lint_hints(data: dict) -> list[dict]:
    hints: list[dict] = []
    missing = data.get("charactersMissingPage") or []
    if missing:
        hints.append(
            {
                "code": "missing_character_pages",
                "severity": "info",
                "message": f"本回 {len(missing)} 个登场人物尚无独立页：{', '.join(missing[:4])}{'…' if len(missing) > 4 else ''}",
            }
        )
    body_only = data.get("bodyOnlyCharacters") or []
    if body_only:
        hints.append(
            {
                "code": "body_only_characters",
                "severity": "warn",
                "message": f"正文提及但 frontmatter 未列：{', '.join(body_only)}",
            }
        )
    if not (data.get("frontmatter") or {}).get("hasSummary"):
        hints.append(
            {
                "code": "missing_summary",
                "severity": "warn",
                "message": "回目 frontmatter 缺 summary",
            }
        )
    return hints


def build_chapter_context(
    *,
    book_slug: str,
    chapter: int,
    route: str,
    edition_slug: str | None = None,
    session_id: str | None = None,
) -> dict:
    book = SLUG_BOOK.get(book_slug)
    if not book:
        raise ValueError(f"unknown bookSlug: {book_slug}")

    data = analyze_chapter_ingest(
        book,
        chapter,
        novels_root=NOVELS_ROOT,
        edition_slug=edition_slug,
    )
    title = data.get("title") or f"第{chapter}回"
    return {
        "sessionId": session_id or f"sess_{uuid.uuid4().hex[:12]}",
        "version": "0.1",
        "book": book,
        "bookSlug": book_slug,
        "rulesRef": "apps/classical-novels/AGENTS.md",
        "page": {
            "kind": "chapter",
            "entityId": str(chapter),
            "entityType": "chapter",
            "name": f"第{chapter}回 · {title}",
            "route": route,
            "editionSlug": data.get("editionSlug"),
        },
        "entity": {
            "path": data["chapterPath"],
            "frontmatter": data.get("entityFrontmatter") or {},
            "plotBullets": 0,
            "relationsCount": 0,
        },
        "ingest": {
            "chapter": chapter,
            "title": title,
            "edition": data.get("edition"),
            "editionSlug": data.get("editionSlug"),
            "readUrl": data.get("readUrl"),
            "excerpt": data.get("excerpt"),
            "charactersListed": data.get("charactersListed") or [],
            "charactersMissingPage": data.get("charactersMissingPage") or [],
            "bodyOnlyCharacters": data.get("bodyOnlyCharacters") or [],
            "locationsMissingPage": data.get("locationsMissingPage") or [],
            "itemsMissingPage": data.get("itemsMissingPage") or [],
            "tasks": data.get("tasks") or [],
        },
        "lintHints": _ingest_lint_hints(data),
        "allowedIntents": [
            "ingest_chapter",
            "add_plot_bullet",
            "query",
            "run_guard",
            "run_lint",
        ],
    }


def build_character_context(
    *,
    book_slug: str,
    page_kind: str,
    entity_id: str,
    route: str,
    session_id: str | None = None,
) -> dict:
    book = SLUG_BOOK.get(book_slug)
    if not book:
        raise ValueError(f"unknown bookSlug: {book_slug}")

    char_path = _content(book) / "characters" / book / f"{entity_id}.md"
    if not char_path.exists():
        raise FileNotFoundError(f"character not found: {entity_id}")

    fm, body = parse_frontmatter(char_path)
    item_ids_set = _load_item_ids(book)
    cl = _load_crosslinks(book)
    occupant = list((cl.get("occupant_items") or {}).get(entity_id) or [])

    key_raw = list(fm.get("关键物品") or [])
    costume_raw = list(fm.get("服饰") or [])
    key_items = [_item_link(book, i, item_ids_set, occupant) for i in key_raw]
    costumes = [_item_link(book, i, item_ids_set, occupant) for i in costume_raw]
    missing_xl = [i for i in key_raw if i not in occupant]

    first_ch = parse_chapter_num(fm.get("first_appear") or "")
    plot_chapters: list[int] = []
    plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    if plot_sec:
        for ln in plot_sec.group(1).splitlines():
            m = re.search(r"第(\d+)回", ln)
            if m:
                plot_chapters.append(int(m.group(1)))
    suggested = sorted({c for c in ([first_ch] if first_ch else []) + plot_chapters})[:12]
    with_items = _chapters_with_items(book, key_raw + costume_raw)

    rel_path = str(char_path.relative_to(NOVELS_ROOT)).replace("\\", "/")
    return {
        "sessionId": session_id or f"sess_{uuid.uuid4().hex[:12]}",
        "version": "0.1",
        "book": book,
        "bookSlug": book_slug,
        "rulesRef": "apps/classical-novels/AGENTS.md",
        "page": {
            "kind": page_kind,
            "entityId": entity_id,
            "entityType": fm.get("type") or "character",
            "name": fm.get("name") or entity_id,
            "route": route,
        },
        "entity": {
            "path": rel_path,
            "frontmatter": fm,
            "plotBullets": count_plot_bullets(body),
            "relationsCount": len(fm.get("relations") or []),
        },
        "items": {
            "keyItems": key_items,
            "costumes": costumes,
            "crosslinksOccupant": occupant,
            "missingFromCrosslinks": missing_xl,
        },
        "chapters": {
            "suggested": suggested,
            "withItems": with_items,
        },
        "lintHints": _lint_hints(key_items, costumes),
        "allowedIntents": [
            "fix_key_item",
            "fix_costume",
            "add_plot_bullet",
            "query",
            "run_guard",
            "run_lint",
        ],
    }


def build_maintenance_context(
    *,
    book_slug: str,
    page_kind: str,
    entity_id: str,
    route: str,
    edition_slug: str | None = None,
    session_id: str | None = None,
) -> dict:
    if page_kind == "chapter":
        try:
            chapter = int(entity_id)
        except ValueError as e:
            raise ValueError(f"invalid chapter entityId: {entity_id}") from e
        return build_chapter_context(
            book_slug=book_slug,
            chapter=chapter,
            route=route,
            edition_slug=edition_slug,
            session_id=session_id,
        )
    return build_character_context(
        book_slug=book_slug,
        page_kind=page_kind,
        entity_id=entity_id,
        route=route,
        session_id=session_id,
    )
