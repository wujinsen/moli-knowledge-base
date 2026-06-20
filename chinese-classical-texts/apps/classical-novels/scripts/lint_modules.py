#!/usr/bin/env python3
"""/lint 扩展 — 名物百科 · 建筑图鉴 · 诗词意象（只报告）。"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from _common import CHAPTER_DIR, CONTENT, DATA_DIR, iter_characters, parse_frontmatter
from ingest_common import find_item_wiki
from tag_chapter_characters import split_body, strip_html
from tag_chapter_meta import find_ids, load_item_pairs, load_location_pairs, parse_list_field

ROOT = Path(__file__).resolve().parents[1]

ITEM_DIRS = ("artifacts", "dishes", "medicines", "costumes", "customs")
CROSSLINKS_SLUG = {"红楼梦": "hongloumeng", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}
PLACE_INDEX_TOPIC = {"红楼梦": "大观园建筑名录.md", "金瓶梅": "西门府建筑名录.md"}

HLM_INF_PRED = {"隐喻", "预示", "象征", "影射"}
HLM_POEM_EXEMPT = {"hl-p-02", "hl-p-07"}
JPM_OMEN = {"name_omen", "object_omen", "tune_omen"}
JPM_PHASES = {"欲起", "聚敛", "极盛", "反噬", "散尽"}
JPM_TEMPS = {"冷", "热"}
XYJ_WUXING_CORE = {
    "xyj-dan-xinyuan": "金",
    "xyj-dan-mumu": "木",
    "xyj-dan-huangpo": "土",
    "xyj-dan-yima": "水",
    "xyj-dan-yinger": "火",
}

# 名物覆盖 lint（内容扩面，非结构断链）
CHARACTER_ITEM_WEIGHT_MIN: dict[str, int] = {"红楼梦": 35, "金瓶梅": 40, "西游记": 45}
CHARACTER_ITEM_IMPORTANT_STATUS = frozenset({"主角", "重要"})
LINT_BODY_UNLISTED_MAX = 25
LINT_CHARACTER_GAPS_MAX = 30
IMAGERY_ITEM_ALIASES: dict[str, dict[str, str]] = {
    "金瓶梅": {
        "簪子": "簪环",
        "鞋": "红睡鞋",
        "蟒衣大红袍": "大红妆花袍",
        "皮袄": "貂鼠里皮袄",
        "镜": "妆镜",
        "酒": "宴饮纵酒",
        "银子": "白银",
        "红丸胎药": "薛姑子种子方",
        "色 · 刮骨钢刀": "四贪词",
        "气 · 颐指气使": "四贪词",
        "财 · 夺命绳索": "四贪词",
        "贯朽粟红 · 皮囊粪土": "四贪词",
    },
}


def book_features(book: str) -> set[str]:
    p = CONTENT / "books" / f"{book}.md"
    if not p.exists():
        return set()
    fm, _ = parse_frontmatter(p)
    return set(fm.get("features") or [])


def _has_places_module(book: str) -> bool:
    feats = book_features(book)
    if feats & {"places", "route", "town", "garden", "manor"}:
        return True
    loc_dir = CONTENT / "locations" / book
    return loc_dir.is_dir() and any(loc_dir.glob("*.md"))


def module_stats(book: str) -> dict:
    feats = book_features(book)
    stats: dict[str, dict] = {}
    if "items" in feats:
        stats["items"] = {"enabled": True, "count": len(list_known_item_ids(book))}
    if _has_places_module(book):
        stats["places"] = {"enabled": True, "count": len(_location_ids(book))}
    if "poems" in feats:
        stats["shi"] = {"enabled": True, "count": len(_imagery_ids(book))}
    return stats


def list_known_item_ids(book: str) -> set[str]:
    ids: set[str] = set()
    for kind in ITEM_DIRS:
        d = CONTENT / kind / book
        if d.is_dir():
            ids |= {p.stem for p in d.glob("*.md")}
    return ids


def _location_ids(book: str) -> set[str]:
    loc_dir = CONTENT / "locations" / book
    if not loc_dir.is_dir():
        return set()
    ids: set[str] = set()
    for p in loc_dir.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        ids.add(fm.get("id") or p.stem)
    return ids


def _imagery_ids(book: str) -> set[str]:
    d = CONTENT / "imagery" / book
    if not d.is_dir():
        return set()
    ids: set[str] = set()
    for p in d.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") == book:
            ids.add(fm.get("id") or p.stem)
    return ids


def _load_crosslinks(book: str) -> dict:
    slug = CROSSLINKS_SLUG.get(book, book)
    path = DATA_DIR / f"{slug}.crosslinks.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _chapter_item_refs(book: str) -> dict[str, set[int]]:
    refs: dict[str, set[int]] = defaultdict(set)
    base = CHAPTER_DIR / book
    if not base.exists():
        return refs
    for p in sorted(base.rglob("*.md")):
        m = re.search(r"(\d+)\.md$", p.name)
        if not m:
            continue
        ch = int(m.group(1))
        raw = p.read_text(encoding="utf-8-sig")
        for iid in parse_list_field(raw, "items") or []:
            if iid:
                refs[iid].add(ch)
    return refs


def _chapter_location_refs(book: str) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    base = CHAPTER_DIR / book
    if not base.exists():
        return counts
    loc_ids = _location_ids(book)
    for p in base.rglob("*.md"):
        raw = p.read_text(encoding="utf-8-sig")
        for lid in parse_list_field(raw, "locations") or []:
            if lid in loc_ids:
                counts[lid] += 1
    return counts


# ── 名物百科 ──────────────────────────────────────────────


def lint_items_missing_pages(book: str) -> list[str]:
    known = list_known_item_ids(book)
    issues: list[str] = []
    seen: set[str] = set()
    base = CHAPTER_DIR / book
    if not base.exists():
        return issues
    for p in sorted(base.rglob("*.md")):
        m = re.search(r"(\d+)\.md$", p.name)
        if not m:
            continue
        ch = int(m.group(1))
        raw = p.read_text(encoding="utf-8-sig")
        for iid in parse_list_field(raw, "items") or []:
            if not iid or iid in known or iid in seen:
                continue
            if find_item_wiki(book, iid, ROOT):
                known.add(iid)
                continue
            seen.add(iid)
            issues.append(f"缺实体页: {iid} @ 第{ch}回 items[]")
    return sorted(issues)


def lint_items_field_gaps(book: str) -> list[str]:
    issues: list[str] = []
    for kind in ITEM_DIRS:
        d = CONTENT / kind / book
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            fm, _ = parse_frontmatter(p)
            iid = fm.get("id") or p.stem
            miss = []
            if not fm.get("summary"):
                miss.append("summary")
            if not fm.get("first_appear") and not (fm.get("appear_in") or []):
                miss.append("first_appear/appear_in")
            if miss:
                issues.append(f"字段缺漏: {iid} · {', '.join(miss)}")
    return issues


def lint_items_orphans(book: str) -> list[str]:
    known = list_known_item_ids(book)
    ch_refs = _chapter_item_refs(book)
    cl = _load_crosslinks(book)
    linked: set[str] = set()
    for ids in (cl.get("occupant_items") or {}).values():
        linked.update(ids)
    for ids in (cl.get("location_items") or {}).values():
        linked.update(ids)

    inbound: dict[str, set[str]] = defaultdict(set)
    wiki_pat = re.compile(r"\[\[([^\]|]+)")

    def scan(text: str, src: str) -> None:
        for m in wiki_pat.finditer(text):
            t = m.group(1).strip()
            if t in known:
                inbound[t].add(src)
        slug = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}.get(book, "")
        if slug:
            for iid in known:
                if f"/{slug}/i/{iid}" in text:
                    inbound[iid].add(src)

    for sub in ("characters", "topics", "events"):
        d = CONTENT / sub / book
        if d.is_dir():
            for p in d.rglob("*.md"):
                scan(p.read_text(encoding="utf-8"), f"{sub}:{p.stem}")

    issues: list[str] = []
    for iid in sorted(known):
        if ch_refs.get(iid) or iid in linked:
            continue
        if len(inbound.get(iid, ())) >= 2:
            continue
        issues.append(f"名物孤儿: {iid} · 无回目/crosslinks · 入链={len(inbound.get(iid, ()))}")
    return issues


def _char_item_ids(fm: dict) -> list[str]:
    if fm.get("type") == "monster":
        return list(fm.get("法宝") or []) + list(fm.get("关键物品") or []) + list(fm.get("服饰") or [])
    return list(fm.get("关键物品") or []) + list(fm.get("服饰") or [])


def _item_location_skip(book: str) -> set[str]:
    """名物 id 若与地点/别名重合，不应写入 items[]。"""
    from tag_chapter_meta import load_location_ids

    skip = load_location_ids(book)
    for alias, lid in load_location_pairs(book):
        if alias:
            skip.add(alias)
        if lid:
            skip.add(lid)
    return skip


def lint_items_body_unlisted(book: str) -> list[str]:
    """正文扫描到已有名物 id，但回目 frontmatter items[] 未列。"""
    pairs = load_item_pairs(book)
    known = list_known_item_ids(book)
    loc_skip = _item_location_skip(book)
    issues: list[str] = []
    seen: set[tuple[int, str]] = set()
    base = CHAPTER_DIR / book
    if not base.exists():
        return issues
    for p in sorted(base.rglob("*.md")):
        m = re.search(r"(\d+)\.md$", p.name)
        if not m:
            continue
        ch = int(m.group(1))
        raw = p.read_text(encoding="utf-8-sig")
        listed = set(parse_list_field(raw, "items") or [])
        body = strip_html(split_body(raw))
        if not body.strip():
            continue
        for iid in find_ids(body, pairs, {}):
            if iid not in known or iid in listed or iid in loc_skip:
                continue
            key = (ch, iid)
            if key in seen:
                continue
            seen.add(key)
            issues.append(f"正文有名物未入 items[]: {iid} @ 第{ch}回")
            if len(issues) >= LINT_BODY_UNLISTED_MAX:
                return sorted(issues)
    return sorted(issues)


def lint_items_character_gaps(book: str) -> list[str]:
    """重要人物缺 服饰/关键物品（crosslinks 有可写入 card 的名物但 frontmatter 未写）。"""
    from _item_wiki import hlm_frontmatter_from_occ, list_item_catalog

    min_w = CHARACTER_ITEM_WEIGHT_MIN.get(book, 40)
    occupant = (_load_crosslinks(book).get("occupant_items") or {})
    catalog = list_item_catalog(book) if book == "红楼梦" else {}
    drift: list[tuple[int, str, int]] = []
    gaps: list[tuple[int, str, str]] = []
    for _path, fm, _body in iter_characters(book):
        cid = fm.get("id") or _path.stem
        if _char_item_ids(fm):
            continue
        occ = occupant.get(cid) or []
        weight = int(fm.get("weight") or 0)
        status = fm.get("status") or ""
        if occ:
            if book == "红楼梦":
                costumes, keys = hlm_frontmatter_from_occ(occ, catalog, cid)
                actionable = len(costumes) + len(keys)
                if not actionable:
                    continue
                drift.append((weight, cid, actionable))
            else:
                drift.append((weight, cid, len(occ)))
            continue
        if status in CHARACTER_ITEM_IMPORTANT_STATUS or weight >= min_w:
            gaps.append((weight, cid, status or "配角"))
    issues: list[str] = []
    for weight, cid, n in sorted(drift, key=lambda x: (-x[0], x[1])):
        issues.append(f"人物缺 frontmatter 名物: {cid} · crosslinks 可写 card {n} 件")
        if len(issues) >= LINT_CHARACTER_GAPS_MAX:
            return issues
    for weight, cid, status in sorted(gaps, key=lambda x: (-x[0], x[1])):
        issues.append(f"人物缺名物链: {cid} · weight={weight} · {status}")
        if len(issues) >= LINT_CHARACTER_GAPS_MAX:
            break
    return issues


def lint_hlm_bestiary_semantics(book: str) -> list[str]:
    """红楼梦图鉴字段语义：喜好/关键物品勿填地点·宴事·诊脉链/礼仪链。"""
    if book != "红楼梦":
        return []
    from _item_wiki import list_item_catalog, validate_card_field_semantics

    catalog = list_item_catalog(book)
    cids = {p.stem for p in (CONTENT / "characters" / book).glob("*.md")}
    issues: list[str] = []
    for _path, fm, _body in iter_characters(book):
        cid = fm.get("id") or _path.stem
        issues.extend(validate_card_field_semantics(book, cid, fm, catalog, cids))
    return sorted(issues)[:80]


def lint_xyj_bestiary_semantics(book: str) -> list[str]:
    """西游记图鉴字段语义：喜好勿填地点/洞府/职责/部属；妖怪勿填关键物品。"""
    if book != "西游记":
        return []
    import json
    from _item_wiki import (
        audit_item_ids_pollution,
        list_item_catalog,
        validate_card_field_semantics,
    )

    catalog = list_item_catalog(book)
    cids = {p.stem for p in (CONTENT / "characters" / book).glob("*.md")}
    issues: list[str] = []
    item_ids_path = DATA_DIR / "xiyouji.item_ids.json"
    if item_ids_path.is_file():
        item_ids = set(json.loads(item_ids_path.read_text(encoding="utf-8")))
        for iid in audit_item_ids_pollution(book, item_ids, cids):
            issues.append(f"item_ids 含人物 id（chip 误链 /i/）: {iid}")
    for _path, fm, _body in iter_characters(book):
        cid = fm.get("id") or _path.stem
        issues.extend(validate_card_field_semantics(book, cid, fm, catalog, cids))
    return sorted(issues)[:80]


def lint_jpm_bestiary_semantics(book: str) -> list[str]:
    """金瓶梅图鉴：喜好勿填帮闲差事；关键物品勿填礼仪/凑分链；服饰勿填六房齐整共用。"""
    if book != "金瓶梅":
        return []
    import json
    from _item_wiki import audit_item_ids_pollution, list_item_catalog, validate_card_field_semantics

    catalog = list_item_catalog(book)
    cids = {p.stem for p in (CONTENT / "characters" / book).glob("*.md")}
    issues: list[str] = []
    path = DATA_DIR / "jinpingmei.item_ids.json"
    if path.is_file():
        item_ids = set(json.loads(path.read_text(encoding="utf-8")))
        for iid in audit_item_ids_pollution(book, item_ids, cids):
            issues.append(f"item_ids 含人物 id: {iid}")
    for _path, fm, _body in iter_characters(book):
        cid = fm.get("id") or _path.stem
        issues.extend(validate_card_field_semantics(book, cid, fm, catalog, cids))
    return sorted(issues)[:80]


def lint_bestiary_json_fields(book: str) -> list[str]:
    """图鉴 JSON fields 源数据语义（bestiary.json 层）。"""
    if book not in ("红楼梦", "金瓶梅", "西游记"):
        return []
    from _item_wiki import audit_bestiary_json_fields

    return audit_bestiary_json_fields(book)[:80]


def lint_hlm_item_ids_pollution(book: str) -> list[str]:
    """红楼梦 item_ids.json 勿含人物 id。"""
    if book != "红楼梦":
        return []
    import json
    from _item_wiki import audit_item_ids_pollution

    cids = {p.stem for p in (CONTENT / "characters" / book).glob("*.md")}
    path = DATA_DIR / "hongloumeng.item_ids.json"
    if not path.is_file():
        return []
    item_ids = set(json.loads(path.read_text(encoding="utf-8")))
    return [f"item_ids 含人物 id: {iid}" for iid in audit_item_ids_pollution(book, item_ids, cids)]


def _omen_covered_by_item(
    book: str, title: str, known: set[str], pair_dict: dict[str, str]
) -> bool:
    aliases = IMAGERY_ITEM_ALIASES.get(book, {})
    head = re.split(r"[·（(]", title, 1)[0].strip()
    for cand in (head, title):
        if cand in aliases and aliases[cand] in known:
            return True
        if cand in known:
            return True
        mapped = pair_dict.get(cand)
        if mapped and mapped in known:
            return True
    for iid in known:
        if len(iid) >= 2 and iid in title:
            return True
    for alias, iid in pair_dict.items():
        if len(alias) >= 2 and alias in title and iid in known:
            return True
    return False


def lint_items_imagery_unmaterialized(book: str) -> list[str]:
    """object_omen 意象尚无对应名物实体页（/i/）。"""
    if "poems" not in book_features(book):
        return []
    known = list_known_item_ids(book)
    pair_dict = dict(load_item_pairs(book))
    issues: list[str] = []
    d = CONTENT / "imagery" / book
    if not d.is_dir():
        return issues
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("subtype") != "object_omen":
            continue
        img_id = fm.get("id") or p.stem
        title = (fm.get("title") or fm.get("name") or img_id).strip()
        if _omen_covered_by_item(book, title, known, pair_dict):
            continue
        issues.append(f"物象谶缺实体页: {title} ({img_id})")
    return issues


def lint_items_crosslinks_gap(book: str) -> list[str]:
    cl = _load_crosslinks(book)
    occupant = cl.get("occupant_items") or {}
    issues: list[str] = []
    char_dir = CONTENT / "characters" / book
    if not char_dir.is_dir():
        return issues
    for p in sorted(char_dir.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        cid = fm.get("id") or p.stem
        items = list(fm.get("关键物品") or []) + list(fm.get("服饰") or [])
        occ = set(occupant.get(cid) or [])
        for item in items:
            if item and item not in occ:
                issues.append(f"crosslinks 未链: {cid} → {item}")
    return issues


# ── 建筑图鉴 ──────────────────────────────────────────────


def lint_places_field_gaps(book: str) -> list[str]:
    issues: list[str] = []
    loc_dir = CONTENT / "locations" / book
    if not loc_dir.is_dir():
        return issues
    for p in sorted(loc_dir.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        lid = fm.get("id") or p.stem
        miss = []
        if not fm.get("summary"):
            miss.append("summary")
        if not fm.get("first_appear") and not (fm.get("appear_in") or []):
            miss.append("first_appear/appear_in")
        if miss:
            issues.append(f"字段缺漏: {lid} · {', '.join(miss)}")
    return issues


def lint_places_nearby_broken(book: str) -> list[str]:
    loc_ids = _location_ids(book)
    issues: list[str] = []
    loc_dir = CONTENT / "locations" / book
    if not loc_dir.is_dir():
        return issues
    for p in sorted(loc_dir.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        lid = fm.get("id") or p.stem
        parent = fm.get("parent")
        if isinstance(parent, str) and parent.strip() and parent not in loc_ids:
            issues.append(f"parent 缺页: {lid} → {parent}")
        for n in fm.get("nearby") or []:
            if isinstance(n, str) and n.strip() and n not in loc_ids:
                issues.append(f"nearby 缺页: {lid} → {n}")
    return issues


def lint_places_graph(book: str) -> list[str]:
    """孤儿页 · locations[] 零覆盖 · 弱入链（仅名录）。"""
    loc_ids = _location_ids(book)
    if not loc_ids:
        return []
    loc_dir = CONTENT / "locations" / book
    pages: dict[str, str] = {}
    for p in loc_dir.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        lid = fm.get("id") or p.stem
        pages[lid] = p.read_text(encoding="utf-8")

    inbound: dict[str, set[str]] = defaultdict(set)

    def scan(text: str, source: str) -> None:
        for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", text):
            t = m.group(1).strip()
            if t in loc_ids:
                inbound[t].add(source)
        slug = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}.get(book, "")
        if slug:
            for lid in loc_ids:
                if f"/{slug}/l/{lid}" in text:
                    inbound[lid].add(source)

    for lid, raw in pages.items():
        parts = raw.split("---", 2)
        body = parts[2] if len(parts) > 2 else ""
        fm, _ = parse_frontmatter(loc_dir / f"{lid}.md")
        for other in loc_ids:
            if other != lid and f"[[{other}]]" in body:
                inbound[other].add(f"wiki:{lid}")
        for n in fm.get("nearby") or []:
            if isinstance(n, str) and n in loc_ids and n != lid:
                inbound[n].add(f"nearby:{lid}")

    for sub in ("characters", "topics", "events"):
        d = CONTENT / sub / book
        if d.is_dir():
            for p in d.rglob("*.md"):
                scan(p.read_text(encoding="utf-8"), f"{sub}:{p.stem}")

    idx_name = PLACE_INDEX_TOPIC.get(book)
    if idx_name:
        idx = CONTENT / "topics" / book / idx_name
        if idx.exists():
            txt = idx.read_text(encoding="utf-8")
            for lid in loc_ids:
                if f"/l/{lid}" in txt or f"[[{lid}]]" in txt:
                    inbound[lid].add("index")

    ch_count = _chapter_location_refs(book)

    issues: list[str] = []
    orphans = sorted(l for l in loc_ids if not inbound[l])
    if orphans:
        issues.append(f"location 孤儿页 ({len(orphans)}): {', '.join(orphans[:15])}"
                      + (f" …+{len(orphans)-15}" if len(orphans) > 15 else ""))
    zero_ch = sorted(l for l in loc_ids if ch_count[l] == 0)
    if zero_ch:
        issues.append(f"locations[] 零覆盖 ({len(zero_ch)}): {', '.join(zero_ch[:15])}"
                      + (f" …+{len(zero_ch)-15}" if len(zero_ch) > 15 else ""))
    weak = sorted(l for l in loc_ids if 0 < len(inbound[l]) <= 2 and "index" in inbound[l])
    if weak:
        issues.append(
            f"location 弱入链仅名录 ({len(weak)}): {', '.join(weak[:12])}"
            + (f" …+{len(weak)-12}" if len(weak) > 12 else "")
        )
    return issues


# ── 诗词意象 ──────────────────────────────────────────────


def _load_imagery_pages(book: str) -> list[dict]:
    d = CONTENT / "imagery" / book
    if not d.is_dir():
        return []
    rows: list[dict] = []
    for p in sorted(d.glob("*.md")):
        fm, body = parse_frontmatter(p)
        if fm.get("book") != book:
            continue
        rows.append({**fm, "_body": body, "_path": p.stem})
    return rows


def lint_shi_field_gaps(book: str) -> list[str]:
    issues: list[str] = []
    for fm in _load_imagery_pages(book):
        iid = fm["id"]
        miss = []
        if not fm.get("summary"):
            miss.append("summary")
        if not (fm.get("chapters") or []):
            miss.append("chapters")
        if miss:
            issues.append(f"字段缺漏: {iid} · {', '.join(miss)}")
    return issues


def lint_shi_inference_gaps(book: str) -> list[str]:
    issues: list[str] = []
    pages = _load_imagery_pages(book)

    if book == "红楼梦":
        for fm in pages:
            st = fm.get("subtype")
            if st not in ("judgment", "poem"):
                continue
            if fm["id"] in HLM_POEM_EXEMPT:
                continue
            inf = [
                l
                for l in fm.get("links") or []
                if l.get("inference")
                and l.get("target_kind", "character") == "character"
                and (st != "judgment" or l.get("predicate") in HLM_INF_PRED)
            ]
            if not inf:
                issues.append(f"缺 inference 人物边: {fm['id']} ({fm.get('title', '')})")

    elif book == "金瓶梅":
        for fm in pages:
            if fm.get("subtype") not in JPM_OMEN:
                continue
            inf = [l for l in fm.get("links") or [] if l.get("inference")]
            if not inf:
                issues.append(f"缺 inference 边: {fm['id']}")
                continue
            for l in inf:
                if l.get("phase") not in JPM_PHASES:
                    issues.append(f"inference 缺 phase: {fm['id']}")
                    break
                if l.get("temperature") not in JPM_TEMPS:
                    issues.append(f"inference 缺 temperature: {fm['id']}")
                    break

    elif book == "西游记":
        elem_by_id: dict[str, str | None] = {}
        edge_count = 0
        for fm in pages:
            tags = fm.get("tags") or []
            el = next((str(t)[3:] for t in tags if str(t).startswith("五行-")), None)
            elem_by_id[fm["id"]] = el
            for link in fm.get("links") or []:
                if link.get("predicate") in {"相克", "交并", "调和", "相济"}:
                    edge_count += 1
        for cid, want in XYJ_WUXING_CORE.items():
            if cid not in elem_by_id:
                issues.append(f"缺核心五行符号: {cid}")
            elif elem_by_id[cid] != want:
                issues.append(f"五行标签不符: {cid} 应为 {want}")
        if edge_count < 10:
            issues.append(f"五行生克边过少: {edge_count} < 10")

    return issues


def lint_shi_chain_broken(book: str) -> list[str]:
    chain_file = DATA_DIR / f"{book}.imagery-chains.json"
    if not chain_file.exists():
        return [f"missing {chain_file.name}"]
    nodes = _shi_graph_nodes(book)
    issues: list[str] = []
    data = json.loads(chain_file.read_text(encoding="utf-8-sig"))
    for chain in data.get("chains") or []:
        for nid in chain.get("path") or []:
            if nid not in nodes:
                issues.append(f"互文链缺节点: {chain.get('id')} → {nid}")
    return issues


def _shi_graph_nodes(book: str) -> set[str]:
    nodes: set[str] = set()
    for fm in _load_imagery_pages(book):
        nodes.add(fm["id"])
        for c in fm.get("characters") or []:
            nodes.add(c)
        for link in fm.get("links") or []:
            tgt = link.get("target", "")
            if tgt:
                nodes.add(tgt)
    links_path = DATA_DIR / f"{book}.imagery-links.json"
    if links_path.exists():
        for link in json.loads(links_path.read_text(encoding="utf-8-sig")).get("links", []):
            nodes.add(link["source"])
            nodes.add(link["target"])
    return nodes


def lint_shi_orphans(book: str) -> list[str]:
    img_ids = _imagery_ids(book)
    if not img_ids:
        return []
    inbound: dict[str, set[str]] = defaultdict(set)
    wiki_pat = re.compile(r"\[\[([^\]|]+)")

    def scan(text: str, src: str) -> None:
        for m in wiki_pat.finditer(text):
            t = m.group(1).strip()
            if t in img_ids:
                inbound[t].add(src)

    for sub in ("characters", "topics", "events"):
        d = CONTENT / sub / book
        if d.is_dir():
            for p in d.rglob("*.md"):
                scan(p.read_text(encoding="utf-8"), f"{sub}:{p.stem}")

    for fm in _load_imagery_pages(book):
        iid = fm["id"]
        for link in fm.get("links") or []:
            tgt = link.get("target", "")
            if tgt in img_ids and tgt != iid:
                inbound[tgt].add(f"link:{iid}")
        if (fm.get("characters") or []) and iid in img_ids:
            inbound[iid].add("characters[]")

    links_path = DATA_DIR / f"{book}.imagery-links.json"
    if links_path.exists():
        for link in json.loads(links_path.read_text(encoding="utf-8-sig")).get("links", []):
            src, tgt = link.get("source"), link.get("target")
            if tgt in img_ids:
                inbound[tgt].add(f"json:{src}")

    chain_file = DATA_DIR / f"{book}.imagery-chains.json"
    if chain_file.exists():
        for chain in json.loads(chain_file.read_text(encoding="utf-8-sig")).get("chains") or []:
            path = chain.get("path") or []
            for i, nid in enumerate(path):
                if nid in img_ids and i > 0:
                    inbound[nid].add(f"chain:{chain.get('id')}")

    shi_path = DATA_DIR / "shi_index.json"
    if shi_path.exists():
        book_slug = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}.get(book)
        shi_data = json.loads(shi_path.read_text(encoding="utf-8-sig"))
        entries = ((shi_data.get("books") or {}).get(book_slug or "", {}).get("entries") or [])
        for row in entries:
            iid = row.get("id")
            if iid in img_ids:
                inbound[iid].add("shi_index")

    issues: list[str] = []
    for iid in sorted(img_ids):
        if not inbound.get(iid):
            issues.append(f"意象孤儿: {iid}")
    return issues


def module_sections(book: str) -> list[tuple[str, str, str, object]]:
    """(id, title, group, fn) — group: core | items | places | shi"""
    feats = book_features(book)
    out: list[tuple[str, str, str, object]] = []

    if "items" in feats:
        out.extend(
            [
                ("items_missing_pages", "名物 · 回目缺实体页", "items", lint_items_missing_pages),
                ("items_field_gaps", "名物 · 字段缺漏", "items", lint_items_field_gaps),
                ("items_orphans", "名物 · 孤儿页", "items", lint_items_orphans),
                ("items_crosslinks", "名物 · crosslinks 缺口", "items", lint_items_crosslinks_gap),
                ("items_body_unlisted", "名物 · 正文未入 items[]", "items", lint_items_body_unlisted),
                ("items_character_gaps", "名物 · 人物缺链", "items", lint_items_character_gaps),
                ("items_imagery_unmaterialized", "名物 · 物象谶缺实体", "items", lint_items_imagery_unmaterialized),
                ("hlm_bestiary_semantics", "图鉴 · 人物喜好/信物", "items", lint_hlm_bestiary_semantics),
                ("hlm_item_ids_pollution", "图鉴 · item_ids 人物污染", "items", lint_hlm_item_ids_pollution),
                ("hlm_bestiary_json", "图鉴 · JSON fields 语义", "items", lint_bestiary_json_fields),
                ("jpm_bestiary_semantics", "图鉴 · 人物喜好/关键物品", "items", lint_jpm_bestiary_semantics),
                ("xyj_bestiary_semantics", "图鉴 · 人物喜好/兵器", "items", lint_xyj_bestiary_semantics),
            ]
        )
    if _has_places_module(book):
        out.extend(
            [
                ("places_graph", "建筑 · 图谱（孤儿/零覆盖/弱入链）", "places", lint_places_graph),
                ("places_field_gaps", "建筑 · 字段缺漏", "places", lint_places_field_gaps),
                ("places_nearby_broken", "建筑 · parent/nearby 断链", "places", lint_places_nearby_broken),
            ]
        )
    if "poems" in feats:
        out.extend(
            [
                ("shi_field_gaps", "意象 · 字段缺漏", "shi", lint_shi_field_gaps),
                ("shi_inference", "意象 · inference/五行边", "shi", lint_shi_inference_gaps),
                ("shi_chains", "意象 · 互文链节点", "shi", lint_shi_chain_broken),
                ("shi_orphans", "意象 · 孤儿页", "shi", lint_shi_orphans),
            ]
        )
    return out
