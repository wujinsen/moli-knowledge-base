#!/usr/bin/env python3
"""合并 xyj_bestiary_fields.py 写入 xiyouji.bestiary.json。

用法: python scripts/build_xyj_bestiary_json.py
"""
from __future__ import annotations

import json
import sys

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter
from _item_wiki import build_chip_item_ids, filter_xyj_like_ids, list_item_catalog
from outcome_extract import extract_outcome, personality_from_summary
from xyj_bestiary_fields import EXTRA, FIELDS

BOOK = "西游记"
OUT = DATA_DIR / "xiyouji.bestiary.json"
CELESTIAL_FACTIONS = frozenset({"天庭", "佛界", "护行神祇", "仙家", "西天"})


def _group_ids(data: dict) -> set[str]:
    out: set[str] = set()
    for ids in data.get("groups", {}).values():
        out.update(ids)
    return out


def _backfill_entry(cid: str, entry: dict, fm: dict, body: str) -> None:
    if not entry.get("性格") and not fm.get("性格"):
        p = personality_from_summary(fm.get("summary") or "")
        if p:
            entry["性格"] = p
    if entry.get("结局") or fm.get("结局"):
        return
    o = extract_outcome(fm, body)
    if not o:
        weight = int(fm.get("weight") or 0)
        faction = fm.get("faction") or ""
        if weight >= 30 and (
            faction in CELESTIAL_FACTIONS or "神" in faction or faction.endswith("界")
        ):
            o = "仍司神职"
    if o:
        entry["结局"] = o


def main() -> int:
    data = json.loads(OUT.read_text(encoding="utf-8"))
    char_dir = CHAR_DIR / BOOK
    catalog = list_item_catalog(BOOK)
    char_ids = {p.stem for p in char_dir.glob("*.md")}
    group_ids = _group_ids(data)

    missing_pages = [cid for cid in FIELDS if not (char_dir / f"{cid}.md").is_file()]
    if missing_pages:
        print(f"warn: FIELDS 无人物页: {', '.join(missing_pages)}")

    fields: dict[str, dict] = dict(data.get("fields", {}))
    for cid, base in FIELDS.items():
        entry = dict(fields.get(cid, {}))
        entry.update(base)
        if not entry.get("结局"):
            path = char_dir / f"{cid}.md"
            if path.is_file():
                fm, body = parse_frontmatter(path)
                if fm.get("结局"):
                    entry["结局"] = fm["结局"]
                else:
                    o = extract_outcome(fm, body)
                    if o:
                        entry["结局"] = o
        fields[cid] = entry

    for cid, patch in EXTRA.items():
        base = dict(fields.get(cid, {}))
        base.update(patch)
        if patch.get("喜好") == []:
            base.pop("喜好", None)
        fields[cid] = base

    for cid in sorted(group_ids):
        path = char_dir / f"{cid}.md"
        if not path.is_file():
            continue
        fm, body = parse_frontmatter(path)
        entry = dict(fields.get(cid, {}))
        _backfill_entry(cid, entry, fm, body)
        fields[cid] = entry

    for cid, entry in list(fields.items()):
        likes = entry.get("喜好")
        if likes:
            path = char_dir / f"{cid}.md"
            rel: list = []
            faction = entry.get("faction") or ""
            if path.is_file():
                fm_rel, _ = parse_frontmatter(path)
                rel = fm_rel.get("relations") or []
                faction = fm_rel.get("faction") or faction
            filtered = filter_xyj_like_ids(
                likes, catalog, char_ids, char_id=cid, faction=faction, relations=rel
            )
            if filtered:
                entry["喜好"] = filtered
            else:
                entry.pop("喜好", None)

    data["fields"] = fields

    chip_extra: set[str] = set()
    for vals in fields.values():
        for key in vals.get("关键物品") or []:
            chip_extra.add(key)
    item_ids = build_chip_item_ids(BOOK, catalog, char_ids, extra_ids=chip_extra)
    ids_out = DATA_DIR / "xiyouji.item_ids.json"
    ids_out.write_text(
        json.dumps(sorted(item_ids), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with_personality = sum(1 for v in fields.values() if v.get("性格"))
    with_outcome = sum(1 for v in fields.values() if v.get("结局"))
    print(
        f"[{BOOK}] 写入 {OUT.name}: {len(fields)} 人 · "
        f"{len(data.get('groups', {}))} 组 · {len(item_ids)} 名物 id · "
        f"性格 {with_personality} · 结局 {with_outcome}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
