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
    "梦坡斋": "梦坡斋",
    "园里": "大观园",
    "园中": "大观园",
    "内书房": "小书房",
}

BOOK_ITEM_EXTRA: dict[str, dict[str, str]] = {
    "金瓶梅": {
        "金华酒": "金华酒",
        "烧羊": "烧羊",
        "酥酥": "酥酥",
        "犀角带": "犀角带",
        "貂鼠皮袄": "貂鼠里皮袄",
        "五灵脂": "五灵脂",
        "春药": "胡僧药",
        "胡僧": "胡僧药",
        "刻丝段子": "大红段子袄",
        "销金": "销金裙带",
    },
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
        "净瓶": "羊脂玉净瓶",
        "七星剑": "七星剑",
        "金铙": "金铙",
        "捣药杵": "捣药杵",
        "紫金铃": "紫金铃",
        "五彩仙衣": "五彩仙衣",
        "仙衣": "五彩仙衣",
        "阴阳二气瓶": "阴阳二气瓶",
        "搭包": "白布搭包",
        "白布搭包": "白布搭包",
        "蟠龙拐": "蟠龙拐",
        "蟠龙拐杖": "蟠龙拐",
        "锦襴袈裟": "锦襴袈裟",
        "锦襕袈裟": "锦襴袈裟",
        "锦绒褊衫": "锦襴袈裟",
        "火尖枪": "火尖枪",
        "九瓣铜锤": "九瓣铜锤",
        "铜锤": "九瓣铜锤",
    },
}

BOOK_LOCATION_EXTRA: dict[str, dict[str, str]] = {
    "红楼梦": {
        "金陵": "金陵城",
        "都中": "金陵城",
        "馒头庵": "水月庵",
        "绛芸轩": "怡红院",
        "薛姨妈家": "薛家",
        "太太房": "王夫人上房",
        "老爷房": "贾政上房",
        "锦阁": "缀锦阁",
        "花枝巷": "小花枝巷",
        "凤姐房": "凤姐院",
        "琏二奶奶房": "凤姐院",
        "环哥儿房": "赵姨娘房",
        "大太太房": "邢夫人上房",
        "珍大奶奶房": "尤氏上房",
        "蓉大奶奶房": "可卿上房",
        "宁国府上房": "可卿上房",
        "宗祠": "贾氏宗祠",
        "祠堂": "贾氏宗祠",
        "内书房": "小书房",
        "辅仁谕德": "议事厅",
        "小花厅": "议事厅",
        "柳堤": "柳叶渚",
        "北静亲王府": "北静王府",
        "忠顺亲王府": "忠顺王府",
        "忠顺府": "忠顺王府",
        "先陵": "孝慈县",
        "南安郡王": "南安王府",
        "南安亲王府": "南安王府",
        "锦乡侯": "锦乡侯府",
        "柳家厨房": "大观园厨房",
        "园里厨房": "大观园厨房",
        "小角门": "角门",
        "西边小角门": "角门",
        "甄府": "甄家",
        "甄家府": "甄家",
        "乐善郡王": "乐善郡王府",
        "临昌伯": "临昌伯府",
        "永昌驸马": "永昌驸马府",
        "临安伯": "临安伯府",
        "东角门": "东角门",
        "内茶房": "内茶房",
        "洒泪亭": "洒泪亭",
        "地藏庵": "地藏庵",
        "二门": "二门",
        "园中后门": "后门",
        "孙绍祖家": "孙家",
        "外书房": "外书房",
        "郝家庄": "郝家庄",
        "下房": "下房",
        "腰门": "腰门",
        "腰门子": "腰门",
        "破寺": "破寺",
        "城外破寺": "破寺",
        "后廊": "后廊",
        "回廊": "回廊",
        "夹道": "夹道",
        "贡院": "贡院",
        "考场": "贡院",
        "会试场": "贡院",
        "临敬殿": "临敬殿",
        "临敬门外": "临敬殿",
        "孝幕": "孝幕",
        "门房": "门上",
        "舡坞": "船坞",
        "龙门口": "贡院",
        "蓉大奶奶": "可卿上房",
        "秦氏房中": "可卿上房",
        "来至秦氏房中": "可卿上房",
        "周姨娘并": "周姨娘房",
        "周姨奶奶房": "周姨娘房",
        "贾政房": "贾政上房",
        "王夫人房": "王夫人上房",
        "贾母房": "贾母上房",
        "东院角门": "东角门",
        "蓉大奶奶房": "可卿上房",
        "神京": "金陵城",
        "京城": "金陵城",
        "江南甄家": "甄家",
        "珍大奶奶": "尤氏上房",
        "十里街": "姑苏阊门",
        "急流津觉迷渡口": "急流津",
        "本家庵": "地藏庵",
        "赵姨娘院": "赵姨娘房",
        "义学": "家塾",
        "贾家之义学": "家塾",
    },
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

# Vite SSR 对中文文件名 import 不稳，crosslinks 用 slug 文件名
CROSSLINKS_SLUG: dict[str, str] = {
    "红楼梦": "hongloumeng",
    "西游记": "xiyouji",
    "金瓶梅": "jinpingmei",
}


def crosslinks_path(book: str) -> Path:
    slug = CROSSLINKS_SLUG.get(book)
    if slug:
        p = DATA_DIR / f"{slug}.crosslinks.json"
        if p.exists():
            return p
    return DATA_DIR / f"{book}.crosslinks.json"


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
    cl_path = crosslinks_path(book)
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
    cl_path = crosslinks_path(book)
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
    "犀角带": 5,
    "金华酒": 8,
    "胡僧药": 6,
    "五灵脂": 7,
    "大红段子袄": 9,
    "烧羊": 12,
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
    """Parse a YAML frontmatter list field (block `- item` or inline `[a, b]`)."""
    parts = raw.split("---", 2)
    fm_raw = parts[1] if len(parts) >= 3 else raw

    if len(parts) >= 3:
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(fm_raw)
            if isinstance(data, dict) and field in data:
                val = data[field]
                if val is None:
                    return []
                if isinstance(val, list):
                    return [str(x) for x in val]
                if isinstance(val, str):
                    return [val]
                return []
        except Exception:
            pass

    return _parse_list_field_legacy(fm_raw, field)


def _parse_list_field_legacy(fm_raw: str, field: str) -> list[str] | None:
    m = re.search(rf"^{re.escape(field)}:\s*\[(.*?)\]", fm_raw, re.M | re.S)
    if m:
        inner = m.group(1).strip()
        if not inner:
            return []
        return re.findall(r"[\u4e00-\u9fff]+", inner)

    block = re.search(
        rf"^{re.escape(field)}:\s*\n((?:[ \t]*-[ \t].+\n?)+)",
        fm_raw,
        re.M,
    )
    if block:
        items: list[str] = []
        for line in block.group(1).splitlines():
            line = line.strip()
            if line.startswith("- "):
                item = line[2:].strip().strip('"').strip("'")
                if item:
                    items.append(item)
        return items

    if re.search(rf"^{re.escape(field)}:\s*$", fm_raw, re.M):
        return []

    return None


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


def canonicalize_ids(items: list[str], alias_pairs: list[tuple[str, str]]) -> list[str]:
    alias_to_id = {alias: lid for alias, lid in alias_pairs}
    out: list[str] = []
    seen: set[str] = set()
    for x in items:
        cid = alias_to_id.get(x, x)
        if cid not in seen:
            out.append(cid)
            seen.add(cid)
    return out


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
            merged = canonicalize_ids(merged, loc_pairs)
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
