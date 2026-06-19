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

# 红楼梦图鉴「信物」：少量、可触可指的情物/佩饰/物证；非饮食宴饮/诊脉/地点链
HLM_KEEPSAKE_TAGS = frozenset({"信物", "佩饰", "情物"})
HLM_KEEPSAKE_OVERRIDES = frozenset(
    {
        "通灵宝玉",
        "金锁",
        "金麒麟",
        "冷香丸",
        "累丝金凤",
        "成窑杯",
        "折扇",
        "虾须镯",
        "巧哥儿名",
        "求愿金镯",
        "扮青儿",
        "玉匣记",
        "五色纸钱",
        "剪发誓",
        "护官符",
        "玫瑰露",
        "茯苓霜",
        "蔷薇硝",
        "魇魔法",
        "风月宝鉴",
        "贾珠遗砚",
        "金寿星",
        "沉香拐",
        "伽南珠",
        "福寿香",
        "寿宴玉杯",
        "鸽子蛋",
    }
)


def is_hlm_keepsake(meta: dict, iid: str = "") -> bool:
    """红楼梦 frontmatter「关键物品」= 图鉴「信物」，须为名物 id 且符合信物语义。"""
    kind = meta.get("kind", "")
    if kind in ("dishes", "medicines"):
        return False
    if iid in HLM_KEEPSAKE_OVERRIDES:
        return True
    tags = set(meta.get("tags") or [])
    if tags & HLM_KEEPSAKE_TAGS:
        return True
    return False


def filter_hlm_keepsake_ids(ids: list[str], catalog: dict[str, dict]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        if is_hlm_keepsake(catalog.get(iid, {}), iid):
            seen.add(iid)
            out.append(iid)
    return out


# 红楼梦图鉴「喜好」：性情/技艺/人名/具体饮食；非地点/宴事/诊脉/制度名物 id
HLM_LIKE_PLOT_MARKERS = ("省亲", "出嫁", "丧仪", "诊", "抄检", "成婚", "郁气", "夜宴", "宴")


def is_hlm_valid_like(meta: dict, iid: str, char_ids: set[str], *, book: str = "红楼梦") -> bool:
    """红楼梦 frontmatter「喜好」须为性情/技艺/人名/具体饮食，勿填地点/情节链 id。"""
    if not iid:
        return False
    if iid in char_ids:
        return True
    loc_dir = CONTENT / "locations" / book
    if loc_dir.is_dir() and (loc_dir / f"{iid}.md").is_file():
        return False
    kind = meta.get("kind")
    if not kind:
        if any(m in iid for m in HLM_LIKE_PLOT_MARKERS):
            return False
        return True
    if kind in ("locations", "customs"):
        return False
    typ = meta.get("type") or ""
    tags = set(meta.get("tags") or [])
    if kind == "medicines":
        return typ not in ("diagnosis", "prescription", "pulse_case") and "诊脉" not in tags
    if kind == "dishes":
        return typ not in ("banquet", "feast") and "宴席" not in tags
    if kind in ("costumes", "artifacts"):
        return False
    return True


def filter_hlm_like_ids(
    ids: list[str], catalog: dict[str, dict], char_ids: set[str], *, book: str = "红楼梦"
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        meta = catalog.get(iid, {})
        if is_hlm_valid_like(meta if meta else {}, iid, char_ids, book=book):
            seen.add(iid)
            out.append(iid)
    return out


# 西游记图鉴「关键物品」
XYJ_TANGSANBAO = frozenset({"九环锡杖", "锦襴袈裟", "紧箍"})


def is_xyj_keepsake(meta: dict, iid: str = "", char_id: str = "") -> bool:
    """西游记 frontmatter「关键物品」= 主兵器或唐僧三宝；非符咒微器/地点/饮食链。"""
    if meta.get("kind") != "artifacts":
        return False
    if char_id == "唐僧" and iid in XYJ_TANGSANBAO:
        return True
    if not char_id and iid in XYJ_TANGSANBAO:
        return True
    tags = set(meta.get("tags") or [])
    typ = meta.get("type", "")
    owner = meta.get("owner") or ""
    if char_id and owner and owner != char_id:
        return False
    if "五众兵器" in tags:
        return True
    if typ == "weapon":
        return True
    return False


def filter_xyj_keepsake_ids(
    ids: list[str],
    catalog: dict[str, dict],
    char_id: str = "",
    *,
    char_type: str = "",
) -> list[str]:
    if char_type == "monster":
        return []
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        if is_xyj_keepsake(catalog.get(iid, {}), iid, char_id):
            seen.add(iid)
            out.append(iid)
    return out


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


def item_target_field(meta: dict, book: str | None = None) -> str | None:
    """costume/fabric → 服饰；红楼梦信物 / 西游记主兵器 → 关键物品；金瓶梅等非服饰 → 关键物品。"""
    book = book or meta.get("book") or ""
    kind = meta.get("kind", "")
    typ = meta.get("type", "")
    iid = meta.get("id", "")
    if kind == "costumes" and typ in ("costume", "fabric"):
        return "服饰"
    if book == "红楼梦":
        return "关键物品" if is_hlm_keepsake(meta, iid) else None
    if book == "西游记":
        return "关键物品" if is_xyj_keepsake(meta, iid) else None
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
    strict_keys = book in ("红楼梦", "西游记")
    list_fields = ("wearers",) if strict_keys else PERSON_LIST_FIELDS
    single_fields = ("wearer", "holder", "owner") if strict_keys else PERSON_SINGLE_FIELDS

    for iid, meta in catalog.items():
        field = item_target_field(meta, book)
        if not field:
            continue
        persons: set[str] = set()
        for key in list_fields:
            for raw in meta.get(key) or []:
                if isinstance(raw, str):
                    persons.update(parse_person_refs(raw, char_ids))
        for key in single_fields:
            raw = meta.get(key)
            if isinstance(raw, str):
                persons.update(parse_person_refs(raw, char_ids))
        if not strict_keys:
            for key in PERSON_LIST_FIELDS:
                if key in list_fields:
                    continue
                for raw in meta.get(key) or []:
                    if isinstance(raw, str):
                        persons.update(parse_person_refs(raw, char_ids))
            for key in PERSON_SINGLE_FIELDS:
                if key in single_fields:
                    continue
                raw = meta.get(key)
                if isinstance(raw, str):
                    persons.update(parse_person_refs(raw, char_ids))
        for pid in persons:
            buckets[pid][field].add(iid)

    if not strict_keys:
        char_dir = CHAR_DIR / book
        if char_dir.is_dir():
            for p in char_dir.glob("*.md"):
                cid = p.stem
                text = p.read_text(encoding="utf-8-sig")
                for m in WIKI_LINK.finditer(text):
                    iid = m.group(1).strip()
                    if iid not in item_ids:
                        continue
                    field = item_target_field(catalog[iid], book)
                    if not field:
                        continue
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
    *,
    book: str | None = None,
    catalog: dict[str, dict] | None = None,
) -> dict:
    out = dict(entry)
    wiki = wiki or {}
    book = book or out.get("book") or ""
    strict_key_items = book in ("红楼梦", "西游记")
    for field in ("服饰", "关键物品"):
        wiki_part = [] if (strict_key_items and field == "关键物品") else (wiki.get(field) or [])
        out[field] = merge_item_lists(out.get(field), wiki_part)
    if book not in ("红楼梦", "西游记"):
        likes = out.get("喜好") or []
        promo = [x for x in likes if isinstance(x, str) and x in item_ids]
        if promo:
            out["关键物品"] = merge_item_lists(out.get("关键物品"), promo)
    if book == "红楼梦" and catalog is not None:
        keys = filter_hlm_keepsake_ids(out.get("关键物品") or [], catalog)
        if keys:
            out["关键物品"] = keys
        else:
            out.pop("关键物品", None)
    elif book == "西游记" and catalog is not None:
        char_id = out.get("id") or ""
        char_type = out.get("type") or ""
        keys = filter_xyj_keepsake_ids(
            out.get("关键物品") or [], catalog, char_id, char_type=char_type
        )
        if keys:
            out["关键物品"] = keys
        else:
            out.pop("关键物品", None)
    for field in ("服饰", "关键物品"):
        if not out.get(field):
            out.pop(field, None)
    return out
