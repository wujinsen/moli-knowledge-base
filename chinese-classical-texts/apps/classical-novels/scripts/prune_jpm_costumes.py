#!/usr/bin/env python3
"""金瓶梅人物 frontmatter「服饰」：剔除六房齐整共用项，保留个人可辨衣饰。

用法:
  python scripts/prune_jpm_costumes.py [--dry-run]
  python scripts/build_jpm_bestiary_json.py && python scripts/build_content_snapshots.py --write
"""
from __future__ import annotations

import argparse
import re
import sys

import yaml

from _common import CHAR_DIR, parse_frontmatter
from _item_wiki import filter_jpm_costume_ids, list_item_catalog

BOOK = "金瓶梅"
FIELDS_PATH = __import__("pathlib").Path(__file__).resolve().parent / "jpm_bestiary_fields.py"


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def patch_extra_source(catalog: dict[str, dict], *, dry_run: bool) -> int:
    text = FIELDS_PATH.read_text(encoding="utf-8")
    changed = 0
    for m in list(re.finditer(r'"([^"]+)":\s*\{[^{}]*?"服饰":\s*\[([^\]]*)\]', text)):
        cid, arr_text = m.group(1), m.group(2)
        ids = re.findall(r'"([^"]+)"', arr_text)
        if not ids:
            continue
        filtered = filter_jpm_costume_ids(ids, catalog, cid)
        if filtered == ids:
            continue
        changed += 1
        inner = ", ".join(f'"{x}"' for x in filtered)
        new_arr = f"[{inner}]" if filtered else "[]"
        old = m.group(0)
        new = re.sub(r'"服饰":\s*\[[^\]]*\]', f'"服饰": {new_arr}', old)
        text = text.replace(old, new, 1)
    if changed and not dry_run:
        FIELDS_PATH.write_text(text, encoding="utf-8")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser(description="Prune 金瓶梅 服饰 to personal items only")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    catalog = list_item_catalog(BOOK)
    char_dir = CHAR_DIR / BOOK
    updated = 0
    for path in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        cid = fm.get("id") or path.stem
        old = list(fm.get("服饰") or [])
        if not old:
            continue
        new = filter_jpm_costume_ids(old, catalog, cid)
        if old == new:
            continue
        updated += 1
        print(f"  {cid}: {len(old)}→{len(new)}  {old} → {new}")
        if new:
            fm["服饰"] = new
        else:
            fm.pop("服饰", None)
        if not args.dry_run:
            write_frontmatter(path, fm, body)

    n_extra = patch_extra_source(catalog, dry_run=args.dry_run)
    print(
        f"[{BOOK}] {'(dry-run) ' if args.dry_run else ''}"
        f"人物 {updated} · jpm_bestiary_fields 服饰行 {n_extra}"
    )
    if (updated or n_extra) and not args.dry_run:
        print(
            "提示: python scripts/build_jpm_bestiary_json.py",
            "&& python scripts/build_content_snapshots.py --write",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
