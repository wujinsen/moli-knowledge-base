"""名物百科 ↔ 人物 frontmatter 的服饰/关键物品映射。"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from _common import CHAR_DIR, CONTENT, parse_frontmatter

ITEM_DIRS = ("artifacts", "dishes", "medicines", "costumes", "customs")
PERSON_LIST_FIELDS = ("eaters", "wearers", "holders", "owners", "participants")
PERSON_SINGLE_FIELDS = ("wearer", "patient", "owner", "prescriber", "holder", "physician")
WIKI_LINK = re.compile(r"\[\[([^\]|]+)")


def list_item_catalog(book: str) -> dict[str, dict]:
    """item_id → {kind, type, ...frontmatter}"""
    catalog: dict[str, dict] = {}
    for kind in ITEM_DIRS:
        d = CONTENT / kind / book
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            fm, _ = parse_frontmatter(p)
            if fm.get("book") != book:
                continue
            iid = fm.get("id") or p.stem
            catalog[iid] = {"kind": kind, **fm}
    return catalog


def list_known_item_ids(book: str) -> set[str]:
    return set(list_item_catalog(book))


def item_target_field(meta: dict) -> str:
    """costume/fabric → 服饰；其余名物 → 关键物品。"""
    kind = meta.get("kind", "")
    typ = meta.get("type", "")
    if kind == "costumes" and typ in ("costume", "fabric"):
        return "服饰"
    return "关键物品"


def parse_person_refs(raw: str, char_ids: set[str]) -> list[str]:
    if not raw or not isinstance(raw, str):
        return []
    text = raw.strip()
    if text in char_ids:
        return [text]
    refs: list[str] = []
    for part in re.split(r"[；;、,]", text):
        name = re.sub(r"[（(].*?[）)]", "", part.strip()).strip()
        if not name:
            continue
        if name in char_ids:
            refs.append(name)
            continue
        for cid in sorted(char_ids, key=len, reverse=True):
            if cid in name:
                refs.append(cid)
                break
    return refs


def merge_item_lists(*lists: list[str] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for lst in lists:
        for x in lst or []:
            if not x or x in seen:
                continue
            seen.add(x)
            out.append(x)
    return out


def build_char_item_map(book: str) -> dict[str, dict[str, list[str]]]:
    """从名物页 wearer 等字段 + 人物正文 [[名物]] 链接汇总。"""
    char_ids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
    catalog = list_item_catalog(book)
    item_ids = set(catalog)
    buckets: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"服饰": set(), "关键物品": set()}
    )

    for iid, meta in catalog.items():
        field = item_target_field(meta)
        persons: set[str] = set()
        for key in PERSON_LIST_FIELDS:
            for raw in meta.get(key) or []:
                if isinstance(raw, str):
                    persons.update(parse_person_refs(raw, char_ids))
        for key in PERSON_SINGLE_FIELDS:
            raw = meta.get(key)
            if isinstance(raw, str):
                persons.update(parse_person_refs(raw, char_ids))
        for pid in persons:
            buckets[pid][field].add(iid)

    char_dir = CHAR_DIR / book
    if char_dir.is_dir():
        for p in char_dir.glob("*.md"):
            cid = p.stem
            text = p.read_text(encoding="utf-8-sig")
            for m in WIKI_LINK.finditer(text):
                iid = m.group(1).strip()
                if iid not in item_ids:
                    continue
                field = item_target_field(catalog[iid])
                buckets[cid][field].add(iid)

    return {
        cid: {k: sorted(v) for k, v in fields.items() if v}
        for cid, fields in buckets.items()
        if any(fields.values())
    }


def merge_fields_with_wiki(
    entry: dict,
    wiki: dict[str, list[str]] | None,
    item_ids: set[str],
) -> dict:
    out = dict(entry)
    wiki = wiki or {}
    for field in ("服饰", "关键物品"):
        out[field] = merge_item_lists(out.get(field), wiki.get(field))
    likes = out.get("喜好") or []
    promo = [x for x in likes if isinstance(x, str) and x in item_ids]
    if promo:
        out["关键物品"] = merge_item_lists(out.get("关键物品"), promo)
    for field in ("服饰", "关键物品"):
        if not out.get(field):
            out.pop(field, None)
    return out
