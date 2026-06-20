#!/usr/bin/env python3
"""图鉴 card 字段语义审计（喜好/信物/关键物品/金瓶梅·服饰）。"""
from __future__ import annotations

import argparse
import json
import sys

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter
from _item_wiki import (
    audit_bestiary_json_fields,
    audit_item_ids_pollution,
    filter_hlm_keepsake_ids,
    filter_hlm_like_ids,
    filter_jpm_costume_ids,
    filter_jpm_keepsake_ids,
    filter_jpm_like_ids,
    filter_xyj_keepsake_ids,
    filter_xyj_like_ids,
    list_item_catalog,
    validate_card_field_semantics,
)

SLUG = {"红楼梦": "hongloumeng", "西游记": "xiyouji", "金瓶梅": "jinpingmei"}
SNAP_SLUG = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}


def _snapshot_field_issues(
    book: str,
    field: str,
    catalog: dict[str, dict],
    filter_fn,
    label: str,
) -> list[str]:
    snap_path = DATA_DIR / "characters_index.json"
    if not snap_path.is_file():
        return []
    slug = SNAP_SLUG.get(book, "")
    if not slug:
        return []
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    for row in snap.get("books", {}).get(slug, {}).get("entries", []):
        cid = row.get("id", "")
        for x in row.get(field) or []:
            ok = filter_fn([x], catalog, cid)
            if x not in ok:
                issues.append(f"快照{label}非法 {cid}: {x}")
    return issues


def _snapshot_keepsake_issues(
    book: str,
    catalog: dict[str, dict],
    char_ids: set[str],
    filter_fn,
) -> list[str]:
    snap_path = DATA_DIR / "characters_index.json"
    if not snap_path.is_file():
        return []
    slug = SNAP_SLUG.get(book, "")
    if not slug:
        return []
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    for row in snap.get("books", {}).get(slug, {}).get("entries", []):
        cid = row.get("id", "")
        ctype = row.get("type") or "character"
        for x in row.get("关键物品") or []:
            ok = filter_fn([x], catalog, char_ids, cid, ctype)
            if x not in ok:
                issues.append(f"快照关键物品非法 {cid}: {x}")
    return issues


def _jpm_costume_filter(ids: list[str], catalog: dict[str, dict], cid: str) -> list[str]:
    return filter_jpm_costume_ids(ids, catalog, cid)


def _jpm_keepsake_filter(
    ids: list[str],
    catalog: dict[str, dict],
    char_ids: set[str],
    _cid: str,
    _ctype: str,
) -> list[str]:
    return filter_jpm_keepsake_ids(ids, catalog, char_ids, book="金瓶梅")


def _xyj_keepsake_filter(
    ids: list[str],
    catalog: dict[str, dict],
    char_ids: set[str],
    cid: str,
    ctype: str,
) -> list[str]:
    return filter_xyj_keepsake_ids(
        ids, catalog, cid, char_type=ctype, char_ids=char_ids, book="西游记"
    )


def audit_hlm() -> dict:
    book = "红楼梦"
    catalog = list_item_catalog(book)
    cids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
    data = json.loads((DATA_DIR / "hongloumeng.bestiary.json").read_text(encoding="utf-8"))
    fields = data.get("fields", {})
    bad_fm: list[str] = []
    drift: list[str] = []
    no_likes: list[str] = []
    has_keys: list[tuple[str, list[str]]] = []
    for cid in sorted(cids):
        fm, _ = parse_frontmatter(CHAR_DIR / book / f"{cid}.md")
        exp = fields.get(cid, {})
        for key in ("喜好", "关键物品"):
            if (fm.get(key) or []) != (exp.get(key) or []):
                drift.append(f"{cid}.{key}: fm={fm.get(key)} json={exp.get(key)}")
        likes = fm.get("喜好") or []
        if not likes:
            no_likes.append(cid)
        keys = fm.get("关键物品") or []
        if keys:
            has_keys.append((cid, keys))
        for x in likes:
            if x not in filter_hlm_like_ids(
                [x], catalog, cids, relations=fm.get("relations") or []
            ):
                bad_fm.append(f"喜好非法 {cid}: {x}")
        for x in keys:
            if x not in filter_hlm_keepsake_ids([x], catalog, cids, book=book):
                bad_fm.append(f"信物非法 {cid}: {x}")
    snap_bad: list[str] = []
    snap_path = DATA_DIR / "characters_index.json"
    if snap_path.is_file():
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
        for row in snap.get("books", {}).get("honglou", {}).get("entries", []):
            cid = row.get("id", "")
            for x in row.get("关键物品") or []:
                if x not in filter_hlm_keepsake_ids([x], catalog, cids, book=book):
                    snap_bad.append(f"快照信物非法 {cid}: {x}")
    return {
        "book": book,
        "chars": len(cids),
        "defined": len(fields),
        "bad_semantics": bad_fm,
        "snapshot_keepsake_bad": snap_bad,
        "json_fm_drift": drift,
        "item_ids_pollution": audit_item_ids_pollution(
            book,
            set(json.loads((DATA_DIR / "hongloumeng.item_ids.json").read_text(encoding="utf-8"))),
            cids,
        )
        if (DATA_DIR / "hongloumeng.item_ids.json").is_file()
        else [],
        "no_likes": no_likes,
        "with_keepsakes": has_keys,
        "json_fields_bad": audit_bestiary_json_fields(book),
    }


def audit_xyj() -> dict:
    book = "西游记"
    catalog = list_item_catalog(book)
    cids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
    data = json.loads((DATA_DIR / "xiyouji.bestiary.json").read_text(encoding="utf-8"))
    fields = data.get("fields", {})
    bad: list[str] = []
    bad_likes: list[str] = []
    drift: list[str] = []
    no_keys_ok: list[str] = []
    with_keys: list[tuple[str, list[str]]] = []
    monster_with_keys: list[str] = []
    for path in sorted((CHAR_DIR / book).glob("*.md")):
        fm, _ = parse_frontmatter(path)
        cid = fm.get("id") or path.stem
        ctype = fm.get("type") or "character"
        exp = fields.get(cid, {})
        for key in ("喜好", "性格", "结局"):
            if (fm.get(key) or ([] if key == "喜好" else None)) != (exp.get(key) or ([] if key == "喜好" else None)):
                if key == "喜好" and not fm.get(key) and not exp.get(key):
                    continue
                drift.append(f"{cid}.{key}: fm={fm.get(key)} json={exp.get(key)}")
        for x in fm.get("喜好") or []:
            if x not in filter_xyj_like_ids(
                [x], catalog, cids, char_id=cid, faction=fm.get("faction") or "", relations=fm.get("relations") or []
            ):
                bad_likes.append(f"喜好非法 {cid}: {x}")
        keys = fm.get("关键物品") or []
        if keys:
            filtered = filter_xyj_keepsake_ids(
                keys, catalog, cid, char_type=ctype, char_ids=cids, book=book
            )
            if filtered != keys:
                bad.append(f"关键物品非法 {cid}: {keys} -> 应 {filtered}")
            if ctype == "monster":
                monster_with_keys.append(cid)
            else:
                with_keys.append((cid, filtered or keys))
        elif ctype == "character" and cid in ("孙悟空", "猪八戒", "沙僧", "唐僧", "二郎神"):
            no_keys_ok.append(cid)
    snap_bad = _snapshot_keepsake_issues(book, catalog, cids, _xyj_keepsake_filter)
    return {
        "book": book,
        "chars": len(list((CHAR_DIR / book).glob("*.md"))),
        "defined": len(fields),
        "bad_semantics": bad,
        "bad_likes": bad_likes,
        "snapshot_keepsake_bad": snap_bad,
        "json_fm_drift": drift,
        "item_ids_pollution": audit_item_ids_pollution(
            book,
            set(json.loads((DATA_DIR / "xiyouji.item_ids.json").read_text(encoding="utf-8"))),
            cids,
        )
        if (DATA_DIR / "xiyouji.item_ids.json").is_file()
        else [],
        "monster_with_keys": monster_with_keys,
        "with_weapons": with_keys,
        "missing_expected_weapon": no_keys_ok,
        "json_fields_bad": audit_bestiary_json_fields(book),
    }


def audit_jpm() -> dict:
    book = "金瓶梅"
    catalog = list_item_catalog(book)
    cids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
    data = json.loads((DATA_DIR / "jinpingmei.bestiary.json").read_text(encoding="utf-8"))
    fields = data.get("fields", {})
    bad_likes: list[str] = []
    bad_keys: list[str] = []
    bad_costumes: list[str] = []
    drift: list[str] = []
    no_likes: list[str] = []
    with_costumes: list[tuple[str, list[str]]] = []
    for cid in sorted(cids):
        fm, _ = parse_frontmatter(CHAR_DIR / book / f"{cid}.md")
        exp = fields.get(cid, {})
        for key in ("喜好", "关键物品", "服饰"):
            if (fm.get(key) or []) != (exp.get(key) or []):
                drift.append(f"{cid}.{key}: fm={fm.get(key)} json={exp.get(key)}")
        likes = fm.get("喜好") or []
        if not likes:
            no_likes.append(cid)
        rel = fm.get("relations") or []
        for x in likes:
            if x not in filter_jpm_like_ids([x], catalog, cids, relations=rel):
                bad_likes.append(f"喜好非法 {cid}: {x}")
        for x in fm.get("关键物品") or []:
            if x not in filter_jpm_keepsake_ids([x], catalog, cids, book=book):
                bad_keys.append(f"关键物品非法 {cid}: {x}")
        costumes = fm.get("服饰") or []
        if costumes:
            with_costumes.append((cid, costumes))
        for x in costumes:
            if x not in filter_jpm_costume_ids([x], catalog, cid):
                bad_costumes.append(f"服饰非个人 {cid}: {x}")
    snap_bad = _snapshot_keepsake_issues(book, catalog, cids, _jpm_keepsake_filter)
    snap_costume_bad = _snapshot_field_issues(
        book, "服饰", catalog, _jpm_costume_filter, "服饰"
    )
    item_path = DATA_DIR / "jinpingmei.item_ids.json"
    return {
        "book": book,
        "chars": len(cids),
        "defined": len(fields),
        "bad_likes": bad_likes,
        "bad_keys": bad_keys,
        "bad_costumes": bad_costumes,
        "snapshot_keepsake_bad": snap_bad,
        "snapshot_costume_bad": snap_costume_bad,
        "json_fm_drift": drift,
        "item_ids_pollution": audit_item_ids_pollution(
            book,
            set(json.loads(item_path.read_text(encoding="utf-8"))),
            cids,
        )
        if item_path.is_file()
        else [],
        "no_likes": no_likes,
        "with_costumes": with_costumes,
        "json_fields_bad": audit_bestiary_json_fields(book),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = {"hlm": audit_hlm(), "xyj": audit_xyj(), "jpm": audit_jpm()}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    h = report["hlm"]
    x = report["xyj"]
    j = report["jpm"]
    print("=== 红楼梦图鉴 ===")
    print(f"人物 {h['chars']} · 定义 {h['defined']}")
    print(f"语义非法: {len(h['bad_semantics'])} · JSON fields: {len(h.get('json_fields_bad', []))} · JSON/人物漂移: {len(h['json_fm_drift'])} · item_ids污染: {len(h.get('item_ids_pollution', []))} · 快照信物: {len(h.get('snapshot_keepsake_bad', []))}")
    print(f"无喜好: {len(h['no_likes'])} · 有信物: {len(h['with_keepsakes'])}")
    for line in h["bad_semantics"][:20]:
        print(" ", line)
    for line in h.get("json_fields_bad", [])[:10]:
        print(" ", line)
    for line in h["json_fm_drift"][:10]:
        print(" ", line)
    print("--- 有信物 ---")
    for cid, keys in h["with_keepsakes"]:
        print(f"  {cid}: {keys}")
    print()
    print("=== 西游记图鉴 ===")
    print(f"人物+妖 {x['chars']} · 定义 {x['defined']}")
    print(
        f"语义非法: {len(x['bad_semantics'])} · 喜好非法: {len(x['bad_likes'])} · "
        f"JSON/人物漂移: {len(x['json_fm_drift'])} · JSON fields: {len(x.get('json_fields_bad', []))} · "
        f"item_ids污染: {len(x.get('item_ids_pollution', []))} · "
        f"快照关键物品: {len(x.get('snapshot_keepsake_bad', []))} · "
        f"妖怪误填关键物品: {len(x['monster_with_keys'])}"
    )
    for line in x["bad_likes"][:15]:
        print(" ", line)
    for line in x["bad_semantics"][:10]:
        print(" ", line)
    for line in x["json_fm_drift"][:5]:
        print(" ", line)
    if x["monster_with_keys"]:
        print("  妖怪:", ", ".join(x["monster_with_keys"][:15]))
    print("--- 主兵器 ---")
    for cid, keys in x["with_weapons"][:20]:
        print(f"  {cid}: {keys}")
    print()
    print("=== 金瓶梅图鉴 ===")
    print(f"人物 {j['chars']} · 定义 {j['defined']}")
    print(
        f"喜好非法: {len(j['bad_likes'])} · 关键物品非法: {len(j.get('bad_keys', []))} · "
        f"服饰非法: {len(j.get('bad_costumes', []))} · "
        f"JSON/人物漂移: {len(j['json_fm_drift'])} · JSON fields: {len(j.get('json_fields_bad', []))} · "
        f"item_ids污染: {len(j.get('item_ids_pollution', []))} · "
        f"快照关键物品: {len(j.get('snapshot_keepsake_bad', []))} · "
        f"快照服饰: {len(j.get('snapshot_costume_bad', []))}"
    )
    for line in j["bad_likes"][:20]:
        print(" ", line)
    for line in j.get("bad_keys", [])[:20]:
        print(" ", line)
    for line in j.get("bad_costumes", [])[:20]:
        print(" ", line)
    for line in j["json_fm_drift"][:10]:
        print(" ", line)
    if j.get("with_costumes"):
        print("--- 有服饰 ---")
        for cid, costumes in j["with_costumes"][:12]:
            print(f"  {cid}: {costumes}")
    ok = (
        not h["bad_semantics"]
        and not h.get("snapshot_keepsake_bad")
        and not h.get("json_fields_bad")
        and not h["json_fm_drift"]
        and not h.get("item_ids_pollution")
        and not x["bad_semantics"]
        and not x["bad_likes"]
        and not x.get("snapshot_keepsake_bad")
        and not x.get("json_fields_bad")
        and not x["json_fm_drift"]
        and not x.get("item_ids_pollution")
        and not x["monster_with_keys"]
        and not j["bad_likes"]
        and not j.get("bad_keys")
        and not j.get("bad_costumes")
        and not j.get("snapshot_keepsake_bad")
        and not j.get("snapshot_costume_bad")
        and not j.get("json_fields_bad")
        and not j["json_fm_drift"]
        and not j.get("item_ids_pollution")
    )
    print()
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
