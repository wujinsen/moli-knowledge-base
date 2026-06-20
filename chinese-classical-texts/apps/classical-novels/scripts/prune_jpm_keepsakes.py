#!/usr/bin/env python3
"""金瓶梅人物 frontmatter「关键物品」：剔除帮闲凑分/结拜分资等礼仪链误同步项。

用法:
  python scripts/prune_jpm_keepsakes.py [--dry-run]
  python scripts/build_jpm_bestiary_json.py
"""
from __future__ import annotations

import argparse
import re
import sys

import yaml

from _common import CHAR_DIR, parse_frontmatter
from _item_wiki import filter_jpm_keepsake_ids, list_item_catalog

BOOK = "金瓶梅"
FIELDS_PATH = __import__("pathlib").Path(__file__).resolve().parent / "jpm_bestiary_fields.py"


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def patch_extra_source(catalog: dict[str, dict], *, dry_run: bool) -> int:
    text = FIELDS_PATH.read_text(encoding="utf-8")
    changed = 0

    def repl(m: re.Match) -> str:
        nonlocal changed
        prefix, arr_text = m.group(1), m.group(2)
        ids = re.findall(r'"([^"]+)"', arr_text)
        filtered = filter_jpm_keepsake_ids(ids, catalog)
        if filtered == ids:
            return m.group(0)
        changed += 1
        if not filtered:
            return f"{prefix}[]"
        inner = ", ".join(f'"{x}"' for x in filtered)
        return f"{prefix}[{inner}]"

    new_text = re.sub(r'("关键物品":\s*)\[([^\]]*)\]', repl, text)
    if changed and not dry_run:
        FIELDS_PATH.write_text(new_text, encoding="utf-8")
    return changed


def prune_characters(catalog: dict[str, dict], *, dry_run: bool) -> int:
    char_dir = CHAR_DIR / BOOK
    updated = 0
    for path in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        cid = fm.get("id") or path.stem
        old = list(fm.get("关键物品") or [])
        new = filter_jpm_keepsake_ids(old, catalog)
        if old == new:
            continue
        updated += 1
        print(f"  {cid}: {len(old)}→{len(new)}  {old} → {new}")
        if new:
            fm["关键物品"] = new
        else:
            fm.pop("关键物品", None)
        if not dry_run:
            write_frontmatter(path, fm, body)
    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description="Prune 金瓶梅 关键物品 to keepsakes only")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    catalog = list_item_catalog(BOOK)
    n_chars = prune_characters(catalog, dry_run=args.dry_run)
    n_extra = patch_extra_source(catalog, dry_run=args.dry_run)
    print(
        f"[{BOOK}] {'(dry-run) ' if args.dry_run else ''}"
        f"人物 {n_chars} · jpm_bestiary_fields 关键物品行 {n_extra}"
    )
    if n_chars or n_extra:
        print("提示: python scripts/build_jpm_bestiary_json.py", file=sys.stderr)


if __name__ == "__main__":
    main()
