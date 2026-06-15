#!/usr/bin/env python3
"""从 xiyouji.bestiary.json 同步 frontmatter 的 性格/喜好。

编辑 scripts/xyj_bestiary_fields.py 后先运行 build_xyj_bestiary_json.py
"""
from __future__ import annotations

import json

import yaml

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter

BOOK = "西游记"
DATA_PATH = DATA_DIR / "xiyouji.bestiary.json"
FIELDS = ("性格", "喜好", "结局")


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    field_map: dict[str, dict] = data.get("fields", {})
    char_dir = CHAR_DIR / BOOK
    updated = 0

    for path in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        cid = fm.get("id", path.stem)
        expected = field_map.get(cid, {})
        changed = False
        for key in FIELDS:
            val = expected.get(key)
            if key == "喜好":
                val = val if val else []
            if val:
                if fm.get(key) != val:
                    fm[key] = val
                    changed = True
            elif key in fm:
                del fm[key]
                changed = True
        if not changed:
            continue
        write_frontmatter(path, fm, body)
        print(f"  {cid}: 性格={'有' if fm.get('性格') else '—'} · 喜好 {len(fm.get('喜好') or [])} 项")
        updated += 1

    print(f"[{BOOK}] 更新 {updated} 个图鉴字段（共 {len(field_map)} 条定义）")


if __name__ == "__main__":
    main()
