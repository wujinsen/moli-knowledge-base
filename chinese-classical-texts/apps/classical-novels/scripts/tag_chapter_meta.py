#!/usr/bin/env python3
"""Fill chapter locations[], items[], summary from body text + title.

Only updates frontmatter; never modifies chapter body.
Merges with existing non-empty lists (append newly detected ids).
When items[] is empty, also infers item ids from characters[] via crosslinks occupant_items.

Usage:
  python scripts/tag_chapter_meta.py 红楼梦
  python scripts/tag_chapter_meta.py 红楼梦 --subdir 脂砚斋本
  python scripts/tag_chapter_meta.py 红楼梦 --only summary
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _common import CHAPTER_DIR, CONTENT, DATA_DIR, parse_frontmatter
from tag_chapter_characters import alias_in_text, split_body, strip_html

LOCATION_EXTRA: dict[str, str] = {
    "宁府": "宁国府",
    "荣府": "荣国府",
    "东府": "宁国府",
    "西府": "荣国府",
    "省亲别墅": "大观园",
    "会芳园": "会芳园",
    "十里街": "姑苏阊门",
    "阊门": "姑苏阊门",
    "仁清巷": "葫芦庙",
    "天恩祖德": "荣国府",
    "绛芸轩": "怡红院",
    "梦坡斋": "荣国府",
    "园里": "大观园",
    "园中": "大观园",
    "内书房": "荣国府",
}

BOOK_ITEM_EXTRA: dict[str, dict[str, str]] = {
    "西游记": {
        "如意金箍棒": "金箍棒",
        "铁棒": "金箍棒",
        "九齿渗金钉钯": "九齿钉钯",
        "钉钯": "九齿钉钯",
        "降妖杖": "降妖宝杖",
        "紧箍儿": "紧箍",
        "紧箍咒": "紧箍",
        "铁扇": "芭蕉扇",
        "罗扇": "芭蕉扇",
        "紫金葫芦": "紫金红葫芦",
        "红葫芦": "紫金红葫芦",
        "幌金绳": "幌金绳",
        "金刚圈": "金刚琢",
        "人种袋": "人种袋",
        "定风丹": "定风丹",
    },
}

BOOK_LOCATION_EXTRA: dict[str, dict[str, str]] = {
    "金瓶梅": {
        "西门大官人家": "西门府",
        "大官人": "西门府",
        "月娘房": "吴月娘房",
        "五娘房": "潘金莲房",
        "六娘房": "李瓶儿房",
        "三娘房": "孟玉楼房",
        "药铺": "西门庆生药铺",
        "生药铺": "西门庆生药铺",
        "勾栏": "李娇儿院",
        "院中": "李娇儿院",
        "花二哥家": "花家",
        "武大郎家": "潘家",
        "紫石街": "潘家",
        "吴道官": "玉皇庙",
        "间壁花家": "花家",
    },
}

LOCATION_BLOCK: dict[str, list[str]] = {
    "大观园": ["小大观园"],
}


def load_location_pairs(book: str) -> list[tuple[str, str]]:
    pairs: dict[str, str] = {}
    loc_json = DATA_DIR / f"{book}.locations.json"
    if loc_json.exists():
        data = json.loads(loc_json.read_text(encoding="utf-8"))
        for node in data.get("nodes", []):
            lid = node.get("id")
            if lid:
                pairs[lid] = lid
                for a in node.get("aliases") or []:
                    if len(a) >= 2:
                        pairs[a] = lid
    loc_dir = CONTENT / "locations" / book
    if loc_dir.exists():
        for p in loc_dir.glob("*.md"):
            fm, _ = parse_frontmatter(p)
            lid = fm.get("id") or p.stem
            pairs[lid] = lid
            for a in fm.get("aliases") or []:
                if len(a) >= 2:
                    pairs[a] = lid
    for alias, lid in LOCATION_EXTRA.items():
        pairs.setdefault(alias, lid)
    for alias, lid in BOOK_LOCATION_EXTRA.get(book, {}).items():
        pairs.setdefault(alias, lid)
    return sorted(pairs.items(), key=lambda x: (-len(x[0]), x[0]))


def load_item_pairs(book: str) -> list[tuple[str, str]]:
    pairs: dict[str, str] = {}
    for kind in ("artifacts", "dishes", "medicines", "costumes", "customs"):
        d = CONTENT / kind / book
        if not d.exists():
            continue
        for p in d.glob("*.md"):
            fm, _ = parse_frontmatter(p)
            iid = fm.get("id") or p.stem
            pairs[iid] = iid
            name = fm.get("name")
            if name and len(name) >= 2 and name != iid:
                pairs[name] = iid
    for jname in (f"{book}.food.json", f"{book}.costume.json", f"{book}.customs.json"):
        jp = DATA_DIR / jname
        if not jp.exists():
            continue
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for key, val in data.items():
            if not isinstance(val, list):
                continue
            for row in val:
                if isinstance(row, dict) and row.get("id"):
                    pairs[row["id"]] = row["id"]
                    if row.get("name") and row["name"] != row["id"]:
                        pairs[row["name"]] = row["id"]
    cl_path = DATA_DIR / f"{book}.crosslinks.json"
    if cl_path.exists():
        try:
            cl = json.loads(cl_path.read_text(encoding="utf-8"))
            for bucket in ("location_items", "occupant_items"):
                for ids in (cl.get(bucket) or {}).values():
                    for iid in ids:
                        pairs[iid] = iid
        except json.JSONDecodeError:
            pass
    # Common in-text names
    pairs.setdefault("通灵宝玉", "通灵宝玉")
    pairs.setdefault("通灵玉", "通灵宝玉")
    pairs.setdefault("金锁", "金锁")
    for alias, iid in BOOK_ITEM_EXTRA.get(book, {}).items():
        pairs.setdefault(alias, iid)
    return sorted(pairs.items(), key=lambda x: (-len(x[0]), x[0]))


def load_occupant_items(book: str) -> dict[str, list[str]]:
    cl_path = DATA_DIR / f"{book}.crosslinks.json"
    if not cl_path.exists():
        return {}
    try:
        cl = json.loads(cl_path.read_text(encoding="utf-8"))
        return cl.get("occupant_items") or {}
    except json.JSONDecodeError:
        return {}


def load_location_ids(book: str) -> set[str]:
    ids: set[str] = set()
    loc_json = DATA_DIR / f"{book}.locations.json"
    if loc_json.exists():
        data = json.loads(loc_json.read_text(encoding="utf-8"))
        for node in data.get("nodes", []):
            if node.get("id"):
                ids.add(node["id"])
    loc_dir = CONTENT / "locations" / book
    if loc_dir.exists():
        for p in loc_dir.glob("*.md"):
            fm, _ = parse_frontmatter(p)
            if fm.get("id"):
                ids.add(fm["id"])
    return ids


# Lower rank = preferred when capping character-inferred items.
ITEM_INFER_PRIORITY: dict[str, int] = {
    "宝玉宝钗成婚": 0,
    "迎春出嫁": 1,
    "秦可卿丧仪": 2,
    "贾母八旬宴": 3,
    "元春省亲": 4,
    "省亲宴": 5,
    "宗祠祭祖": 6,
    "元宵夜宴": 7,
    "中秋": 8,
    "端午": 9,
    "累丝金凤": 10,
    "通灵宝玉": 11,
    "金锁": 12,
    "冷香丸": 13,
    "胡庸医诊晴雯": 20,
    "王太医诊晴雯": 21,
    "黛玉郁气吐血": 22,
    "毕知庵诊宝玉": 23,
    "年例": 30,
    "奴婢月例": 31,
}

MAX_INFERRED_ITEMS = 6
BLOATED_ITEMS_THRESHOLD = 10


def items_for_characters(
    char_ids: list[str],
    occupant: dict[str, list[str]],
    *,
    block: set[str],
    limit: int = MAX_INFERRED_ITEMS,
) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for cid in char_ids:
        for iid in occupant.get(cid, []):
            if iid in block or iid in seen:
                continue
            seen.add(iid)
            candidates.append(iid)
    candidates.sort(key=lambda x: (ITEM_INFER_PRIORITY.get(x, 50), x))
    return candidates[:limit]


def find_ids(text: str, alias_pairs: list[tuple[str, str]], blocks: dict[str, list[str]]) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    positions: dict[str, int] = {}
    for alias, iid in alias_pairs:
        if iid in seen:
            continue
        idx = alias_in_text(text, alias)
        if idx < 0:
            continue
        blocked = False
        for compound in blocks.get(alias, []):
            cidx = text.find(compound)
            while cidx >= 0:
                if cidx <= idx < cidx + len(compound):
                    blocked = True
                    break
                cidx = text.find(compound, cidx + 1)
        if blocked:
            continue
        seen.add(iid)
        positions[iid] = idx
        found.append(iid)
    found.sort(key=lambda c: positions[c])
    return found


def parse_list_field(raw: str, field: str) -> list[str] | None:
    m = re.search(rf"^{field}:\s*\[(.*?)\]", raw, re.M)
    if not m:
        return None
    inner = m.group(1).strip()
    if not inner:
        return []
    return re.findall(r"[\u4e00-\u9fff]+", inner)


def parse_scalar_field(raw: str, field: str) -> str | None:
    m = re.search(rf"^{field}:\s*(.+)$", raw, re.M)
    if not m:
        return None
    val = m.group(1).strip()
    if val in ("", '""', "''"):
        return ""
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    return val


def format_list(field: str, items: list[str]) -> str:
    if not items:
        return f"{field}: []"
    return f"{field}: [{', '.join(items)}]"


def title_to_summary(title: str) -> str:
    title = title.strip()
    parts = re.split(r"[\u3000\s]+", title, maxsplit=1)
    if len(parts) == 2 and parts[0] and parts[1]:
        return f"{parts[0]}；{parts[1]}"
    return title


def merge_lists(existing: list[str] | None, detected: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for c in (existing or []) + detected:
        if c not in seen:
            out.append(c)
            seen.add(c)
    return out


def ensure_frontmatter_fields(raw: str) -> str:
    """Ensure locations, items, summary keys exist before closing ---."""
    if parse_scalar_field(raw, "summary") is None:
        title = parse_scalar_field(raw, "title") or ""
        summary = title_to_summary(title) if title else ""
        raw = re.sub(r"\n---\s*\n", f"\nsummary: {summary}\n---\n", raw, count=1)
    if parse_list_field(raw, "items") is None:
        raw = re.sub(r"\n---\s*\n", "\nitems: []\n---\n", raw, count=1)
    if parse_list_field(raw, "locations") is None:
        raw = re.sub(r"\n---\s*\n", "\nlocations: []\n---\n", raw, count=1)
    return raw


def patch_chapter(
    raw: str,
    *,
    loc_pairs: list[tuple[str, str]],
    item_pairs: list[tuple[str, str]],
    occupant_items: dict[str, list[str]],
    location_ids: set[str],
    text: str,
    fields: set[str],
) -> tuple[str, bool]:
    changed = False
    new_raw = raw

    if "locations" in fields:
        existing = parse_list_field(raw, "locations")
        if existing is not None:
            detected = find_ids(text, loc_pairs, LOCATION_BLOCK)
            merged = merge_lists(existing, detected)
            if merged != existing:
                line = format_list("locations", merged)
                new_raw = re.sub(r"^locations:\s*\[.*\]\s*$", line, new_raw, count=1, flags=re.M)
                changed = True

    if "items" in fields:
        existing = parse_list_field(raw, "items")
        if existing is not None:
            detected = find_ids(text, item_pairs, {})
            char_ids = parse_list_field(raw, "characters") or []
            inferred = items_for_characters(
                char_ids, occupant_items, block=location_ids
            )
            if not existing:
                merged = merge_lists(detected, inferred)
            elif len(existing) > BLOATED_ITEMS_THRESHOLD:
                merged = merge_lists(detected, inferred)
            else:
                merged = merge_lists(existing, detected)
            if merged != existing:
                line = format_list("items", merged)
                new_raw = re.sub(r"^items:\s*\[.*\]\s*$", line, new_raw, count=1, flags=re.M)
                changed = True

    if "summary" in fields:
        current = parse_scalar_field(raw, "summary")
        if current is not None and not current.strip():
            title = parse_scalar_field(raw, "title") or ""
            if title:
                summary = title_to_summary(title)
                if re.search(r"^summary:\s*", raw, re.M):
                    new_raw = re.sub(
                        r"^summary:\s*.*$",
                        f"summary: {summary}",
                        new_raw,
                        count=1,
                        flags=re.M,
                    )
                else:
                    new_raw = re.sub(
                        r"\n---\s*\n",
                        f"\nsummary: {summary}\n---\n",
                        new_raw,
                        count=1,
                    )
                changed = True

    return new_raw, changed


def iter_chapter_files(book: str, subdir: str | None) -> list[Path]:
    base = CHAPTER_DIR / book
    if subdir:
        base = base / subdir
    return sorted(base.glob("[0-9]*.md"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Tag chapter locations/items/summary")
    ap.add_argument("book", nargs="?", default="红楼梦")
    ap.add_argument("--subdir", default="")
    ap.add_argument(
        "--only",
        choices=("locations", "items", "summary", "all"),
        default="all",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fields = {"locations", "items", "summary"} if args.only == "all" else {args.only}
    loc_pairs = load_location_pairs(args.book)
    item_pairs = load_item_pairs(args.book)
    occupant_items = load_occupant_items(args.book)
    location_ids = load_location_ids(args.book)

    updated = 0
    for path in iter_chapter_files(args.book, args.subdir or None):
        raw = path.read_text(encoding="utf-8")
        raw = ensure_frontmatter_fields(raw)
        text = strip_html(split_body(raw))
        new_raw, changed = patch_chapter(
            raw,
            loc_pairs=loc_pairs,
            item_pairs=item_pairs,
            occupant_items=occupant_items,
            location_ids=location_ids,
            text=text,
            fields=fields,
        )
        if changed:
            updated += 1
            rel = path.relative_to(CHAPTER_DIR / args.book)
            print(f"  {rel}")
            if not args.dry_run:
                path.write_text(new_raw, encoding="utf-8")

    scope = args.subdir or "程高本"
    print(f"[{args.book}/{scope}] updated {updated} chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
