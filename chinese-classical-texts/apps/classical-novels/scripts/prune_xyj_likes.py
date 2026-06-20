#!/usr/bin/env python3
"""西游记人物 frontmatter「喜好」：剔除地点/洞府/职责/部属链等误填项。

用法:
  python scripts/prune_xyj_likes.py [--dry-run]
  python scripts/build_xyj_bestiary_json.py && python scripts/seed_xyj_bestiary.py
"""
from __future__ import annotations

import argparse
import re
import sys

import yaml

from _common import CHAR_DIR, parse_frontmatter
from _item_wiki import filter_xyj_like_ids, list_item_catalog

BOOK = "西游记"
FIELDS_PATH = __import__("pathlib").Path(__file__).resolve().parent / "xyj_bestiary_fields.py"


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def char_ids(book: str) -> set[str]:
    return {p.stem for p in (CHAR_DIR / book).glob("*.md")}


def patch_fields_source(catalog: dict[str, dict], cids: set[str], *, dry_run: bool) -> int:
    """按各 FIELDS 人物页的 relations 逐条过滤源文件中的喜好。"""
    text = FIELDS_PATH.read_text(encoding="utf-8")
    changed = 0
    for m in list(re.finditer(r'"([^"]+)":\s*\{[^{}]*?"喜好":\s*\[([^\]]*)\]', text)):
        cid, arr_text = m.group(1), m.group(2)
        ids = re.findall(r'"([^"]+)"', arr_text)
        if not ids:
            continue
        rel: list = []
        path = CHAR_DIR / BOOK / f"{cid}.md"
        if path.is_file():
            fm, _ = parse_frontmatter(path)
            rel = fm.get("relations") or []
        filtered = filter_xyj_like_ids(ids, catalog, cids, char_id=cid, faction=fm.get("faction") or "", relations=rel)
        if filtered == ids:
            continue
        changed += 1
        inner = ", ".join(f'"{x}"' for x in filtered)
        new_arr = f"[{inner}]" if filtered else "[]"
        old = m.group(0)
        new = re.sub(r'"喜好":\s*\[[^\]]*\]', f'"喜好": {new_arr}', old)
        text = text.replace(old, new, 1)
    if changed and not dry_run:
        FIELDS_PATH.write_text(text, encoding="utf-8")
    return changed


def prune_characters(catalog: dict[str, dict], cids: set[str], *, dry_run: bool) -> int:
    char_dir = CHAR_DIR / BOOK
    updated = 0
    for path in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        cid = fm.get("id") or path.stem
        old = list(fm.get("喜好") or [])
        rel = fm.get("relations") or []
        new = filter_xyj_like_ids(old, catalog, cids, char_id=cid, faction=fm.get("faction") or "", relations=rel)
        if old == new:
            continue
        updated += 1
        print(f"  {cid}: {len(old)}→{len(new)}  {old} → {new}")
        if new:
            fm["喜好"] = new
        else:
            fm.pop("喜好", None)
        if not dry_run:
            write_frontmatter(path, fm, body)
    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description="Prune 西游记 喜好 to valid semantics")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    catalog = list_item_catalog(BOOK)
    cids = char_ids(BOOK)
    n_chars = prune_characters(catalog, cids, dry_run=args.dry_run)
    n_fields = patch_fields_source(catalog, cids, dry_run=args.dry_run)
    print(
        f"[{BOOK}] {'(dry-run) ' if args.dry_run else ''}"
        f"人物 {n_chars} · xyj_bestiary_fields {n_fields}"
    )
    if n_chars or n_fields:
        print(
            "提示: python scripts/build_xyj_bestiary_json.py && python scripts/seed_xyj_bestiary.py",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
